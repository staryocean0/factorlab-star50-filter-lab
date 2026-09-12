"""Non-invasive DataHub reception instrumentation adapters.

Wraps the existing DataHub HqApiPort / QuotesListParserPort seam. The capture
boundary is the Python SDK return from get_security_quotes(), before the
DataHub quote parser. This is *not* raw TCP-frame timing and does not infer
historical received_at values.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from threading import Lock
from typing import Any, Mapping, Protocol, Sequence
import base64
import json

from recorder import ReceptionRecorder, ReceiptStamp, ParsedReceipt, validate_pair


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


class RecordSink(Protocol):
    def append(self, record: Any) -> None: ...


@dataclass(frozen=True)
class CapturedQuote:
    stamp: ReceiptStamp
    canonical_payload: bytes
    request_symbols: tuple[str, ...]


@dataclass(frozen=True)
class CapturedBatch:
    items: tuple[CapturedQuote, ...]
    endpoint: tuple[str, int] | None
    market: str


class CaptureBuffer:
    """FIFO handoff between the wrapped HQ API and wrapped quote parser."""

    def __init__(self) -> None:
        self._batches: deque[CapturedBatch] = deque()
        self._lock = Lock()

    def push(self, batch: CapturedBatch) -> None:
        with self._lock:
            self._batches.append(batch)

    def pop_for(self, payload: Sequence[Mapping[str, Any]]) -> CapturedBatch:
        with self._lock:
            if not self._batches:
                raise RuntimeError("no captured reception batch available for parser payload")
            batch = self._batches.popleft()
        if len(batch.items) != len(payload):
            raise RuntimeError(
                f"capture/parser cardinality mismatch: captured={len(batch.items)} payload={len(payload)}"
            )
        for index, (captured, raw) in enumerate(zip(batch.items, payload)):
            current = canonicalize_sdk_quote(raw)
            if current != captured.canonical_payload:
                raise RuntimeError(f"capture/parser payload mismatch at index {index}")
        return batch

    def pending_batches(self) -> int:
        with self._lock:
            return len(self._batches)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            return {"__float__": repr(value)}
        return value
    if isinstance(value, bytes):
        return {"__bytes_b64__": base64.b64encode(value).decode("ascii")}
    if isinstance(value, bytearray):
        return {"__bytes_b64__": base64.b64encode(bytes(value)).decode("ascii")}
    if isinstance(value, memoryview):
        return {"__bytes_b64__": base64.b64encode(bytes(value)).decode("ascii")}
    if isinstance(value, datetime):
        return {"__datetime__": value.isoformat()}
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    raise TypeError(f"unsupported SDK quote value type: {type(value).__name__}")


def canonicalize_sdk_quote(item: Mapping[str, Any]) -> bytes:
    """Stable identity for the Python SDK object, not original network-frame bytes."""
    if not isinstance(item, Mapping):
        raise TypeError("TDX SDK quote item must be a mapping")
    safe = _json_safe(item)
    return json.dumps(safe, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _base_code(value: str) -> str:
    text = str(value).strip().upper()
    if "." in text:
        text = text.split(".", 1)[0]
    return text


def canonical_symbol(raw: Mapping[str, Any], requested: Sequence[str]) -> str | None:
    candidate = raw.get("code") or raw.get("symbol")
    if candidate is None:
        return None
    candidate_text = str(candidate).strip().upper()
    if candidate_text in requested:
        return candidate_text
    base = _base_code(candidate_text)
    matches = [symbol for symbol in requested if _base_code(symbol) == base]
    return matches[0] if len(matches) == 1 else None


def _positive_price(value: Any) -> float | None:
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    return price if isfinite(price) and price > 0 else None


def _source_sequence(raw: Mapping[str, Any]) -> str | int | None:
    for key in ("sequence_no", "sequence", "seq", "source_sequence"):
        if key in raw and raw[key] is not None:
            return raw[key]
    return None


def _raw_event_candidate(raw: Mapping[str, Any]) -> tuple[str | None, str | None, str | None, str]:
    """Return raw event-time candidate conservatively.

    Supplied DataHub TDX source does not establish any vendor event-time key.
    If a future adapter explicitly presents one of these self-describing keys,
    preserve the raw value but do not normalize it here without a source contract.
    """
    for key in ("market_event_time", "event_time", "exchange_timestamp", "quote_time"):
        value = raw.get(key)
        if value is not None:
            return str(value), None, None, "UNPARSED"
    return None, None, None, "UNPARSED"


class TdxReceptionHqTap:
    """Stamp every TDX SDK quote immediately after the delegated SDK call returns."""

    def __init__(
        self,
        delegate: HqApiPort,
        *,
        recorder: ReceptionRecorder,
        capture_buffer: CaptureBuffer,
        receipt_sink: RecordSink,
    ) -> None:
        self._delegate = delegate
        self._recorder = recorder
        self._buffer = capture_buffer
        self._receipt_sink = receipt_sink

    def get_security_quotes(
        self,
        symbols: list[str],
        market: str,
        *,
        endpoint: tuple[str, int] | None = None,
        connection: object | None = None,
    ) -> list[dict]:
        payload = self._delegate.get_security_quotes(
            symbols=symbols,
            market=market,
            endpoint=endpoint,
            connection=connection,
        )
        if payload is None:
            payload = []
        if not isinstance(payload, list) or any(not isinstance(x, Mapping) for x in payload):
            raise TypeError("delegate get_security_quotes must return list[dict]")
        captured: list[CapturedQuote] = []
        for item in payload:
            canonical = canonicalize_sdk_quote(item)
            stamp = self._recorder.stamp(canonical)
            self._receipt_sink.append(stamp)
            captured.append(
                CapturedQuote(
                    stamp=stamp,
                    canonical_payload=canonical,
                    request_symbols=tuple(symbols),
                )
            )
        self._buffer.push(CapturedBatch(items=tuple(captured), endpoint=endpoint, market=market))
        return payload


class ReceptionAwareQuotesParser:
    """Delegate to DataHub's parser, then attach parsed fields to immutable stamps."""

    def __init__(
        self,
        delegate: QuotesListParserPort,
        *,
        recorder: ReceptionRecorder,
        capture_buffer: CaptureBuffer,
        parsed_sink: RecordSink,
    ) -> None:
        self._delegate = delegate
        self._recorder = recorder
        self._buffer = capture_buffer
        self._parsed_sink = parsed_sink

    def _write_failure(self, batch: CapturedBatch, payload: Sequence[Mapping[str, Any]], message: str) -> None:
        for captured, raw in zip(batch.items, payload):
            parsed = self._recorder.parsed(
                captured.stamp,
                symbol=canonical_symbol(raw, captured.request_symbols),
                trading_day=None,
                market_event_time_raw=None,
                market_event_time_normalized=None,
                market_event_timezone=None,
                event_time_parse_status="UNPARSED",
                price=_positive_price(raw.get("price")),
                source_sequence=_source_sequence(raw),
                parse_error=message,
            )
            validate_pair(captured.stamp, parsed)
            self._parsed_sink.append(parsed)

    def parse_quotes(self, payload: list[dict]) -> list[dict]:
        batch = self._buffer.pop_for(payload)
        try:
            parsed_rows = self._delegate.parse_quotes(payload)
        except Exception as exc:
            self._write_failure(batch, payload, f"delegate_parser_error:{type(exc).__name__}:{exc}")
            raise
        if not isinstance(parsed_rows, list):
            self._write_failure(batch, payload, "delegate_parser_returned_non_list")
            raise TypeError("delegate parse_quotes must return list[dict]")
        if len(parsed_rows) != len(payload):
            self._write_failure(
                batch,
                payload,
                f"delegate_parser_cardinality_mismatch:{len(payload)}->{len(parsed_rows)}",
            )
            raise RuntimeError("delegate parser changed quote cardinality")

        for index, (captured, raw, parsed_row) in enumerate(zip(batch.items, payload, parsed_rows)):
            if not isinstance(parsed_row, Mapping):
                self._write_failure(batch, payload, f"delegate_parser_non_mapping_at:{index}")
                raise TypeError("delegate parser rows must be mappings")
            symbol = canonical_symbol(raw, captured.request_symbols)
            raw_event, normalized_event, event_tz, event_status = _raw_event_candidate(raw)
            # The supplied DataHub TDX parser sets `timestamp=datetime.now(UTC)`.
            # It is parse-time metadata and is intentionally NOT promoted to vendor event time.
            price = _positive_price(raw.get("price"))
            if price is None:
                price = _positive_price(parsed_row.get("last_price", parsed_row.get("price")))
            local_parse_day = parsed_row.get("trading_day")
            parsed = self._recorder.parsed(
                captured.stamp,
                symbol=symbol,
                trading_day=None if local_parse_day is None else str(local_parse_day),
                market_event_time_raw=raw_event,
                market_event_time_normalized=normalized_event,
                market_event_timezone=event_tz,
                event_time_parse_status=event_status,
                price=price,
                source_sequence=_source_sequence(raw),
                parse_error=None,
            )
            validate_pair(captured.stamp, parsed)
            self._parsed_sink.append(parsed)
        return parsed_rows
