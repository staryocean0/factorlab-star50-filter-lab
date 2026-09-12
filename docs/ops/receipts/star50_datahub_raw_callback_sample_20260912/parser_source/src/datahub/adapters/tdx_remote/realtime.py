# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import threading
import time
from datetime import datetime, timezone
from itertools import count
from typing import Any, Protocol

from tdx_data_sdk.realtime import (
    DEFAULT_QUOTE_ENDPOINTS,
    RoundRobinEndpointPool,
    TdxQuoteClient,
    TdxQuoteConnectionPool,
)
from tdx_data_sdk.realtime.constants import Endpoint


class ConnectionPoolPort(Protocol):
    def acquire(self, endpoint: tuple[str, int] | None = None) -> object: ...
    def release(self, conn: object) -> None: ...


class IpPoolPort(Protocol):
    def pick_endpoint(self) -> tuple[str, int]: ...


class HqApiPort(Protocol):
    def get_security_quotes(
        self,
        symbols: list[str],
        market: str,
        *,
        endpoint: tuple[str, int] | None = None,
        connection: object | None = None,
    ) -> list[dict]: ...


class QuotesListParserPort(Protocol):
    def parse_quotes(self, payload: list[dict]) -> list[dict]: ...


class TdxRemoteRealtimeAdapter:
    def __init__(
        self,
        *,
        mode: str = "stub",
        request_timeout_seconds: float = 5.0,
        endpoints: list[str] | list[Endpoint] | None = None,
        connection_pool: ConnectionPoolPort | None = None,
        ip_pool: IpPoolPort | None = None,
        hq_api: HqApiPort | None = None,
        quotes_parser: QuotesListParserPort | None = None,
    ) -> None:
        resolved_endpoints = _coerce_endpoints(endpoints)
        self._configured_endpoints = list(resolved_endpoints)
        live_mode = mode == "live" or any(
            dependency is not None
            for dependency in (connection_pool, ip_pool, hq_api, quotes_parser)
        )
        self._mode = "live" if live_mode else "stub"
        self._seq = count(1)
        self._connection_pool = connection_pool or (
            TdxConnectionPoolAdapter(
                endpoints=resolved_endpoints,
                timeout_seconds=request_timeout_seconds,
            )
            if live_mode
            else None
        )
        self._ip_pool = ip_pool or (
            TdxIpPoolAdapter(endpoints=resolved_endpoints) if live_mode else None
        )
        self._hq_api = hq_api or (
            TdxHqApiAdapter(
                endpoints=resolved_endpoints,
                timeout_seconds=request_timeout_seconds,
            )
            if live_mode
            else None
        )
        self._quotes_parser = quotes_parser or TdxQuotesListParserAdapter()
        self._fallback_count = 0
        self._last_fallback_reason: str | None = None
        self._last_fallback_endpoint: str | None = None

    def poll_quotes(
        self, *, symbols: list[str], market: str = "cn_a"
    ) -> list[dict[str, object]]:
        if self._hq_api is None:
            self._record_fallback(reason="hq_api_unavailable", endpoint=None)
            return self._poll_stub_quotes(symbols=symbols, market=market)
        last_failure_reason: str | None = None
        last_failure_endpoint: tuple[str, int] | None = None
        for round_index in range(2):
            for endpoint in self._candidate_endpoints():
                conn: object | None = None
                try:
                    if self._connection_pool is not None:
                        try:
                            conn = self._connection_pool.acquire(endpoint=endpoint)
                        except TypeError:
                            conn = self._connection_pool.acquire()
                    payload = self._hq_api.get_security_quotes(
                        symbols=symbols,
                        market=market,
                        endpoint=endpoint,
                        connection=conn,
                    )
                    parsed = (
                        self._quotes_parser.parse_quotes(payload)
                        if self._quotes_parser
                        else payload
                    )
                    if not parsed:
                        last_failure_reason = "empty_quote_payload"
                        last_failure_endpoint = endpoint
                        self._report_failure(endpoint=endpoint)
                        continue
                    self._last_fallback_reason = None
                    self._last_fallback_endpoint = None
                    self._report_success(endpoint=endpoint)
                    return [self._normalize_raw(item, market=market) for item in parsed]
                except Exception as exc:
                    last_failure_reason = f"{type(exc).__name__}: {exc}"
                    last_failure_endpoint = endpoint
                    self._report_failure(endpoint=endpoint)
                finally:
                    if self._connection_pool is not None and conn is not None:
                        self._connection_pool.release(conn)
            if round_index == 0:
                time.sleep(0.2)
        self._record_fallback(
            reason=last_failure_reason or "all_candidate_endpoints_failed",
            endpoint=last_failure_endpoint,
        )
        return self._poll_stub_quotes(symbols=symbols, market=market)

    def _poll_stub_quotes(
        self, *, symbols: list[str], market: str = "cn_a"
    ) -> list[dict[str, object]]:
        now = datetime.now(timezone.utc)
        ts = now.isoformat()
        trading_day = ts[:10]
        items: list[dict[str, object]] = []
        for idx, symbol in enumerate(symbols, start=1):
            base = 10.0 + idx
            items.append(
                {
                    "symbol": symbol,
                    "market": market,
                    "timestamp": ts,
                    "trading_day": trading_day,
                    "last_price": round(base + 0.01, 2),
                    "volume": float(1000 * idx),
                    "amount": float(10000 * idx),
                    "bid_price_1": round(base, 2),
                    "ask_price_1": round(base + 0.01, 2),
                    "bid_volume_1": float(100 * idx),
                    "ask_volume_1": float(90 * idx),
                    "available_at": ts,
                    "source_kind": "tdx_hq_stub",
                    "sequence_no": next(self._seq),
                    "stream_id": f"stream_{market}",
                }
            )
        return items

    def _select_endpoint(self) -> tuple[str, int] | None:
        if self._ip_pool is None:
            return None
        for _ in range(3):
            endpoint = self._ip_pool.pick_endpoint()
            is_healthy = getattr(self._connection_pool, "is_endpoint_healthy", None)
            if not callable(is_healthy) or is_healthy(endpoint):
                return endpoint
        return self._ip_pool.pick_endpoint()

    def _candidate_endpoints(self) -> list[tuple[str, int] | None]:
        if self._ip_pool is None:
            return [None]
        first = self._select_endpoint()
        if first is None:
            return [None]
        ordered = [first]
        for endpoint in self._configured_endpoints:
            if endpoint not in ordered:
                ordered.append(endpoint)
        return ordered

    def _report_failure(self, *, endpoint: tuple[str, int] | None) -> None:
        if endpoint is None:
            return
        report_failure = getattr(self._connection_pool, "report_failure", None)
        if callable(report_failure):
            report_failure(endpoint)

    def _report_success(self, *, endpoint: tuple[str, int] | None) -> None:
        if endpoint is None:
            return
        report_success = getattr(self._connection_pool, "report_success", None)
        if callable(report_success):
            report_success(endpoint)

    def _record_fallback(
        self,
        *,
        reason: str,
        endpoint: tuple[str, int] | None,
    ) -> None:
        self._fallback_count += 1
        self._last_fallback_reason = reason
        self._last_fallback_endpoint = (
            None if endpoint is None else f"{endpoint[0]}:{endpoint[1]}"
        )

    def _normalize_raw(self, raw: dict, *, market: str) -> dict[str, object]:
        now = datetime.now(timezone.utc).isoformat()
        last_price = raw.get("last_price", raw.get("price", 0.0))
        volume = raw.get("volume", raw.get("vol", raw.get("cur_vol", 0.0)))
        bid_price_1 = raw.get("bid_price_1", raw.get("bid1", 0.0))
        ask_price_1 = raw.get("ask_price_1", raw.get("ask1", 0.0))
        bid_volume_1 = raw.get("bid_volume_1", raw.get("bid_vol1", 0.0))
        ask_volume_1 = raw.get("ask_volume_1", raw.get("ask_vol1", 0.0))
        return {
            "symbol": str(raw["symbol"]),
            "market": str(raw.get("market", market)),
            "timestamp": str(raw.get("timestamp", now)),
            "trading_day": str(raw.get("trading_day", now[:10])),
            "last_price": float(last_price),
            "volume": float(volume),
            "amount": float(raw.get("amount", 0.0)),
            "bid_price_1": float(bid_price_1),
            "ask_price_1": float(ask_price_1),
            "bid_volume_1": float(bid_volume_1),
            "ask_volume_1": float(ask_volume_1),
            "available_at": str(raw.get("available_at", now)),
            "source_kind": str(raw.get("source_kind", "tdx_hq_live")),
            "sequence_no": int(raw.get("sequence_no", next(self._seq))),
            "stream_id": str(raw.get("stream_id", f"stream_{market}")),
        }

    def get_health_snapshot(self) -> dict[str, Any]:
        pool_snapshot: dict[str, Any] = {}
        if self._connection_pool is not None:
            getter = getattr(self._connection_pool, "get_health_snapshot", None)
            if callable(getter):
                pool_snapshot = getter()
        ip_snapshot = {
            "enabled": self._ip_pool is not None,
            "adapter": type(self._ip_pool).__name__
            if self._ip_pool is not None
            else None,
        }
        hq_snapshot = {
            "enabled": self._hq_api is not None,
            "adapter": type(self._hq_api).__name__
            if self._hq_api is not None
            else None,
        }
        return {
            "mode": self._mode,
            "connection_pool": pool_snapshot,
            "ip_pool": ip_snapshot,
            "hq_api": hq_snapshot,
            "fallback_count": self._fallback_count,
            "last_fallback_reason": self._last_fallback_reason,
            "last_fallback_endpoint": self._last_fallback_endpoint,
        }

    def close(self) -> None:
        close = getattr(self._connection_pool, "close", None)
        if callable(close):
            close()


class TdxConnectionPoolAdapter:
    def __init__(
        self,
        connection_pool_module: Any | None = None,
        *,
        endpoints: list[Endpoint] | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._delegate = None
        self._endpoints = endpoints or list(DEFAULT_QUOTE_ENDPOINTS)
        self._timeout_seconds = timeout_seconds
        self._pool_module = connection_pool_module
        if connection_pool_module is None:
            self._delegate = TdxQuoteConnectionPool(
                endpoints=self._endpoints,
                timeout_seconds=self._timeout_seconds,
            )
            return

        self._pool = None
        self._pool_lock = threading.Lock()
        self._cached_conn: object | None = None
        self._cached_endpoint: tuple[str, int] | None = None
        self._lease_count = 0
        self._reuse_hits = 0
        self._new_conn_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._endpoint_failures: dict[tuple[str, int], int] = {}
        self._endpoint_unhealthy_until: dict[tuple[str, int], float] = {}
        self._cooldown_seconds = 30.0

    def _ensure_pool(self) -> None:
        if self._delegate is not None:
            return
        with self._pool_lock:
            if self._pool is not None:
                return
            self._pool = self._pool_module.AsyncConnectionPool(
                servers=self._endpoints or None
            )
            enter = getattr(self._pool, "__aenter__", None)
            if callable(enter):
                _run_async(enter())

    def acquire(self, endpoint: tuple[str, int] | None = None) -> object:
        if self._delegate is not None:
            return self._delegate.acquire(endpoint=endpoint)
        self._ensure_pool()
        with self._pool_lock:
            if self._cached_conn is not None:
                if endpoint is None or self.is_endpoint_healthy(endpoint):
                    self._lease_count += 1
                    self._reuse_hits += 1
                    return self._cached_conn
            conn = _run_async(self._pool.acquire())
            self._cached_conn = conn
            self._cached_endpoint = endpoint
            self._lease_count += 1
            self._new_conn_count += 1
            return conn

    def release(self, conn: object) -> None:
        if self._delegate is not None:
            self._delegate.release(conn)
            return
        with self._pool_lock:
            if self._lease_count > 0:
                self._lease_count -= 1
        _ = conn

    def report_failure(self, endpoint: tuple[str, int]) -> None:
        if self._delegate is not None:
            self._delegate.report_failure(endpoint)
            return
        self._failure_count += 1
        current = self._endpoint_failures.get(endpoint, 0) + 1
        self._endpoint_failures[endpoint] = current
        if current >= 3:
            self._endpoint_unhealthy_until[endpoint] = (
                time.time() + self._cooldown_seconds
            )
            with self._pool_lock:
                if self._cached_endpoint == endpoint and self._cached_conn is not None:
                    try:
                        self._pool.release(self._cached_conn)
                    except Exception:
                        pass
                    self._cached_conn = None
                    self._cached_endpoint = None

    def report_success(self, endpoint: tuple[str, int]) -> None:
        if self._delegate is not None:
            self._delegate.report_success(endpoint)
            return
        self._success_count += 1
        self._endpoint_failures.pop(endpoint, None)
        self._endpoint_unhealthy_until.pop(endpoint, None)

    def is_endpoint_healthy(self, endpoint: tuple[str, int]) -> bool:
        if self._delegate is not None:
            return self._delegate.is_endpoint_healthy(endpoint)
        until = self._endpoint_unhealthy_until.get(endpoint)
        if until is None:
            return True
        if time.time() >= until:
            self._endpoint_unhealthy_until.pop(endpoint, None)
            self._endpoint_failures.pop(endpoint, None)
            return True
        return False

    def get_health_snapshot(self) -> dict[str, Any]:
        if self._delegate is not None:
            return self._delegate.get_health_snapshot()
        stats = {}
        if self._pool is not None:
            try:
                stats = self._pool.get_stats()
            except Exception:
                stats = {}
        return {
            "pool_stats": stats,
            "reuse_hits": self._reuse_hits,
            "new_conn_count": self._new_conn_count,
            "lease_count": self._lease_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "endpoint_failures": {
                f"{ip}:{port}": count
                for (ip, port), count in self._endpoint_failures.items()
            },
        }

    def close(self) -> None:
        if self._delegate is not None:
            self._delegate.close()
            return
        with self._pool_lock:
            cached_conn = self._cached_conn
            self._cached_conn = None
            self._cached_endpoint = None
        close = getattr(cached_conn, "close", None)
        if callable(close):
            _run_async(close())


class TdxIpPoolAdapter:
    def __init__(self, *, endpoints: list[Endpoint] | None = None) -> None:
        self._pool = RoundRobinEndpointPool(endpoints=endpoints)

    def pick_endpoint(self) -> tuple[str, int]:
        return self._pool.pick_endpoint()


class TdxHqApiAdapter:
    def __init__(
        self,
        hq_module: Any | None = None,
        *,
        endpoints: list[Endpoint] | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._hq_module = hq_module
        self._endpoints = endpoints or list(DEFAULT_QUOTE_ENDPOINTS)
        self._timeout_seconds = timeout_seconds

    def get_security_quotes(
        self,
        symbols: list[str],
        market: str,
        *,
        endpoint: tuple[str, int] | None = None,
        connection: object | None = None,
    ) -> list[dict]:
        query = [(_resolve_market_code(symbol, market), symbol) for symbol in symbols]
        if connection is not None and hasattr(connection, "get_security_quotes"):
            rows = connection.get_security_quotes(query)
            if asyncio.iscoroutine(rows):
                return _run_async(rows) or []
            return rows or []
        if self._hq_module is not None:
            server = endpoint or (
                self._endpoints[0] if self._endpoints else ("39.108.28.83", 7709)
            )
            return _run_async(self._fetch_quotes_via_module(server=server, query=query))
        server = endpoint or (
            self._endpoints[0] if self._endpoints else ("39.108.28.83", 7709)
        )
        client = TdxQuoteClient(endpoint=server, timeout_seconds=self._timeout_seconds)
        try:
            return client.get_security_quotes(query)
        finally:
            client.close()

    async def _fetch_quotes_via_module(
        self, *, server: tuple[str, int], query: list[tuple[int, str]]
    ) -> list[dict]:
        api = await self._hq_module.AsyncTdxHq_API.factory(
            server=server, raise_exception=False
        )
        if api is None:
            return []
        try:
            rows = await api.get_security_quotes(query)
            return rows or []
        finally:
            close = getattr(api, "close", None)
            if callable(close):
                await close()
            else:
                disconnect = getattr(api, "disconnect", None)
                if callable(disconnect):
                    await disconnect()


class TdxQuotesListParserAdapter:
    def parse_quotes(self, payload: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        trading_day = now.date().isoformat()
        parsed: list[dict] = []
        for item in payload:
            parsed.append(
                {
                    "symbol": item.get("code") or item.get("symbol"),
                    "market": "cn_a",
                    "timestamp": timestamp,
                    "trading_day": trading_day,
                    "last_price": item.get("price", 0.0),
                    "volume": item.get("vol", item.get("cur_vol", 0.0)),
                    "amount": item.get("amount", 0.0),
                    "bid_price_1": item.get("bid1", 0.0),
                    "ask_price_1": item.get("ask1", 0.0),
                    "bid_volume_1": item.get("bid_vol1", 0.0),
                    "ask_volume_1": item.get("ask_vol1", 0.0),
                    "available_at": timestamp,
                    "source_kind": "tdx_hq_live",
                }
            )
        return parsed


OldSdkConnectionPoolAdapter = TdxConnectionPoolAdapter
OldSdkIpPoolAdapter = TdxIpPoolAdapter
OldSdkHqApiAdapter = TdxHqApiAdapter
OldSdkQuotesListParserAdapter = TdxQuotesListParserAdapter


def _coerce_endpoints(endpoints: list[str] | list[Endpoint] | None) -> list[Endpoint]:
    if not endpoints:
        return list(DEFAULT_QUOTE_ENDPOINTS)
    resolved: list[Endpoint] = []
    for item in endpoints:
        if isinstance(item, tuple):
            host, port = item
            resolved.append((str(host), int(port)))
            continue
        host, _, port = str(item).partition(":")
        if host and port:
            resolved.append((host, int(port)))
    return resolved or list(DEFAULT_QUOTE_ENDPOINTS)


def _resolve_market_code(symbol: str, market: str) -> int:
    normalized = str(symbol)
    if normalized.startswith(("4", "8", "9")) or market in {"bj", "cn_bj"}:
        return 2
    if normalized.startswith(("5", "6", "11")) or market in {"sh", "cn_sh"}:
        return 1
    return 0


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    result_holder: dict[str, Any] = {}
    error_holder: dict[str, BaseException] = {}

    def _runner() -> None:
        try:
            result_holder["value"] = asyncio.run(coro)
        except BaseException as exc:  # pragma: no cover - defensive
            error_holder["error"] = exc

    worker = threading.Thread(target=_runner, daemon=True)
    worker.start()
    worker.join()
    if "error" in error_holder:
        raise error_holder["error"]
    return result_holder.get("value", [])
