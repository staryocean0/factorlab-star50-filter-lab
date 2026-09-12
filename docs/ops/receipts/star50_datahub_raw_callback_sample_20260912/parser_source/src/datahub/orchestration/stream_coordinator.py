# -*- coding: utf-8 -*-
# ---
# module_primary: market-stream
# module_related: [orchestration]
# governed_surface: stream coordination and fanout logic
# ---
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable
from uuid import uuid4

from fastapi import WebSocket

from datahub.adapters.tdx_remote.realtime import TdxRemoteRealtimeAdapter
from datahub.core.services.realtime_service import RealtimeService
from datahub.orchestration.subscription_state_machine import SubscriptionStateMachine
from datahub.orchestration.states import SubscriptionStatus


TickCallback = Callable[[dict], Awaitable[None]]


@dataclass(slots=True)
class SubscriptionRuntime:
    websocket: WebSocket
    symbols: list[str]
    market: str
    state: str = SubscriptionStatus.REQUESTED.value


class StreamCoordinator:
    def __init__(
        self,
        *,
        adapter: TdxRemoteRealtimeAdapter | None = None,
        on_tick: TickCallback | None = None,
        poll_interval_seconds: float = 0.2,
    ) -> None:
        self._adapter = adapter or TdxRemoteRealtimeAdapter()
        self._normalizer = RealtimeService()
        self._on_tick = on_tick
        self._poll_interval_seconds = poll_interval_seconds
        self._state_machine = SubscriptionStateMachine()
        self._subscriptions: dict[str, SubscriptionRuntime] = {}
        self._poll_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._metrics: dict[str, float | int | list[float]] = {
            "tick_total": 0,
            "send_failures": 0,
            "poll_iterations": 0,
            "poll_failures": 0,
            "suppressed_stub_batches": 0,
            "recoveries": 0,
            "last_recovery_ms": 0.0,
            "poll_latency_ms_samples": [],
        }

    async def add_subscription(
        self, websocket: WebSocket, *, symbols: list[str], market: str
    ) -> str:
        sub_id = f"sub_{uuid4().hex[:10]}"
        async with self._lock:
            runtime = SubscriptionRuntime(
                websocket=websocket, 
                symbols=symbols, 
                market=market,
                state=SubscriptionStatus.REQUESTED.value
            )
            self._subscriptions[sub_id] = runtime
            
            # Transition to ACTIVE
            if self._state_machine.can_transition(runtime.state, SubscriptionStatus.ACTIVE.value):
                runtime.state = SubscriptionStatus.ACTIVE.value
                
            self.ensure_poll_task(symbols=symbols, market=market)
        return sub_id

    async def remove_subscription(self, subscription_id: str) -> None:
        async with self._lock:
            runtime = self._subscriptions.get(subscription_id)
            if runtime:
                if self._state_machine.can_transition(runtime.state, SubscriptionStatus.CANCELLING.value):
                    runtime.state = SubscriptionStatus.CANCELLING.value
                if self._state_machine.can_transition(runtime.state, SubscriptionStatus.CLOSED.value):
                    runtime.state = SubscriptionStatus.CLOSED.value
            self._subscriptions.pop(subscription_id, None)
            self._cleanup_idle_tasks()

    def ensure_poll_task(self, *, symbols: list[str], market: str) -> str:
        poll_key = self._build_poll_key(symbols=symbols, market=market)
        task = self._poll_tasks.get(poll_key)
        if task is None or task.done():
            self._poll_tasks[poll_key] = asyncio.create_task(
                self._poll_loop(symbols=symbols, market=market),
                name=f"stream-poll-{poll_key}",
            )
        return poll_key

    async def close_websocket(self, websocket: WebSocket) -> None:
        async with self._lock:
            to_remove = [
                sub_id
                for sub_id, runtime in self._subscriptions.items()
                if runtime.websocket is websocket
            ]
            for sub_id in to_remove:
                self._subscriptions.pop(sub_id, None)
            self._cleanup_idle_tasks()

    async def _poll_loop(self, *, symbols: list[str], market: str) -> None:
        poll_key = self._build_poll_key(symbols=symbols, market=market)
        last_failure_at: float | None = None
        while True:
            async with self._lock:
                active = any(
                    self._build_poll_key(symbols=sub.symbols, market=sub.market)
                    == poll_key
                    for sub in self._subscriptions.values()
                )
            if not active:
                return
            poll_started = time.perf_counter()
            try:
                raw_ticks = self._adapter.poll_quotes(symbols=symbols, market=market)
                self._metrics["poll_iterations"] = (
                    int(self._metrics["poll_iterations"]) + 1
                )
                if self._should_suppress_stub_batch(raw_ticks):
                    self._metrics["poll_failures"] = (
                        int(self._metrics["poll_failures"]) + 1
                    )
                    self._metrics["suppressed_stub_batches"] = (
                        int(self._metrics["suppressed_stub_batches"]) + 1
                    )
                    if last_failure_at is None:
                        last_failure_at = time.perf_counter()
                    await asyncio.sleep(self._poll_interval_seconds)
                    continue
                if last_failure_at is not None:
                    recovered_ms = (time.perf_counter() - last_failure_at) * 1000.0
                    self._metrics["recoveries"] = int(self._metrics["recoveries"]) + 1
                    self._metrics["last_recovery_ms"] = recovered_ms
                    last_failure_at = None
            except Exception:
                self._metrics["poll_failures"] = int(self._metrics["poll_failures"]) + 1
                if last_failure_at is None:
                    last_failure_at = time.perf_counter()
                await asyncio.sleep(self._poll_interval_seconds)
                continue
            latency_ms = (time.perf_counter() - poll_started) * 1000.0
            self._record_poll_latency(latency_ms)
            for raw in raw_ticks:
                envelope = self._normalizer.normalize_tick(raw).model_dump()
                await self._fanout_tick(envelope=envelope, poll_key=poll_key)
                if self._on_tick is not None:
                    await self._on_tick(envelope)
            await asyncio.sleep(self._poll_interval_seconds)

    async def _fanout_tick(self, *, envelope: dict, poll_key: str) -> None:
        async with self._lock:
            targets = [
                (sub_id, runtime.websocket)
                for sub_id, runtime in self._subscriptions.items()
                if self._build_poll_key(symbols=runtime.symbols, market=runtime.market)
                == poll_key
            ]
        for sub_id, ws in targets:
            try:
                await ws.send_json(
                    {
                        "type": "tick",
                        "channel": "stream",
                        "request_id": f"req_ws_tick_{envelope.get('sequence_no', 0)}",
                        "subscription_id": sub_id,
                        "data": envelope,
                        "meta": {
                            "source_kind": envelope.get("source_kind", "tdx_hq_stub"),
                            "sequence_no": envelope.get("sequence_no", 0),
                        },
                    }
                )
                self._metrics["tick_total"] = int(self._metrics["tick_total"]) + 1
            except Exception:
                self._metrics["send_failures"] = int(self._metrics["send_failures"]) + 1
                await self.remove_subscription(sub_id)

    def _cleanup_idle_tasks(self) -> None:
        active_poll_keys = {
            self._build_poll_key(symbols=sub.symbols, market=sub.market)
            for sub in self._subscriptions.values()
        }
        for poll_key, task in list(self._poll_tasks.items()):
            if poll_key not in active_poll_keys:
                task.cancel()
                self._poll_tasks.pop(poll_key, None)

    async def close(self) -> None:
        async with self._lock:
            tasks = list(self._poll_tasks.values())
            self._poll_tasks.clear()
            self._subscriptions.clear()
        for task in tasks:
            task.cancel()
        close = getattr(self._adapter, "close", None)
        if callable(close):
            close()

    def debug_snapshot(self) -> dict:
        get_health_snapshot = getattr(self._adapter, "get_health_snapshot", None)
        adapter_health = get_health_snapshot() if callable(get_health_snapshot) else {}
        return {
            "active_subscriptions": len(self._subscriptions),
            "active_poll_tasks": len(
                [task for task in self._poll_tasks.values() if not task.done()]
            ),
            "stream_metrics": self._metrics_snapshot(),
            "connection_pool": adapter_health.get("connection_pool", {}),
            "ip_pool": adapter_health.get("ip_pool", {}),
            "hq_api": adapter_health.get("hq_api", {}),
        }

    def _record_poll_latency(self, latency_ms: float) -> None:
        samples = self._metrics["poll_latency_ms_samples"]
        if not isinstance(samples, list):
            return
        samples.append(latency_ms)
        if len(samples) > 200:
            samples.pop(0)

    def _metrics_snapshot(self) -> dict:
        samples = self._metrics["poll_latency_ms_samples"]
        p95 = 0.0
        if isinstance(samples, list) and samples:
            ordered = sorted(float(item) for item in samples)
            idx = int(0.95 * (len(ordered) - 1))
            p95 = ordered[idx]
        return {
            "tick_total": int(self._metrics["tick_total"]),
            "send_failures": int(self._metrics["send_failures"]),
            "poll_iterations": int(self._metrics["poll_iterations"]),
            "poll_failures": int(self._metrics["poll_failures"]),
            "suppressed_stub_batches": int(self._metrics["suppressed_stub_batches"]),
            "recoveries": int(self._metrics["recoveries"]),
            "last_recovery_ms": float(self._metrics["last_recovery_ms"]),
            "poll_latency_p95_ms": p95,
        }

    def _should_suppress_stub_batch(self, raw_ticks: list[dict]) -> bool:
        if not raw_ticks:
            return False
        get_health_snapshot = getattr(self._adapter, "get_health_snapshot", None)
        if not callable(get_health_snapshot):
            return False
        health = get_health_snapshot() or {}
        if str(health.get("mode") or "") != "live":
            return False
        if not bool((health.get("hq_api") or {}).get("enabled")):
            return False
        return all(str(item.get("source_kind") or "") == "tdx_hq_stub" for item in raw_ticks)

    @staticmethod
    def _build_poll_key(*, symbols: list[str], market: str) -> str:
        normalized = ",".join(sorted({str(item) for item in symbols}))
        return f"{market}:{normalized}"
