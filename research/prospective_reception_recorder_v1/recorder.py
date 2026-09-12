"""Prospective true-reception clock recorder.

This module captures a local receipt stamp before parsing/normalization.
It does not infer historical reception times and does not connect to a feed by itself.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Callable, Mapping, Any
import base64
import hashlib
import json
import os
import time
import uuid

SCHEMA = "factorlab_true_reception_capture_v1"
RECORDER_VERSION = "prospective_reception_recorder_v1"
SUPPORTED_SYMBOLS = frozenset({"000688.SH", "000852.SH"})


def _iso_utc_from_ns(ns: int) -> str:
    if not isinstance(ns, int) or ns < 0:
        raise ValueError("wall clock nanoseconds must be a non-negative integer")
    dt = datetime.fromtimestamp(ns / 1_000_000_000, tz=timezone.utc)
    return dt.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _clean_text(value: str | None, name: str, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise ValueError(f"{name} is required")
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string or null")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{name} is required")
    return value or None


@dataclass(frozen=True)
class ReceiptStamp:
    schema: str
    recorder_version: str
    recorder_instance_id: str
    receipt_id: str
    source: str
    channel: str | None
    local_sequence: int
    receive_wallclock_utc_ns: int
    receive_wallclock_utc: str
    receive_monotonic_ns: int
    process_start_wallclock_utc_ns: int
    process_start_monotonic_ns: int
    raw_payload_sha256: str
    raw_payload_size: int
    raw_payload_b64: str | None
    production_authority: bool = False


@dataclass(frozen=True)
class ParsedReceipt:
    schema: str
    recorder_version: str
    recorder_instance_id: str
    receipt_id: str
    local_sequence: int
    symbol: str | None
    trading_day: str | None
    market_event_time_raw: str | None
    market_event_time_normalized: str | None
    market_event_timezone: str | None
    event_time_parse_status: str
    price: float | None
    source_sequence: str | None
    parse_error: str | None
    production_authority: bool = False


class ReceptionRecorder:
    """Capture receipt clocks before parsing.

    `stamp()` must be called at the feed callback boundary, before parsing,
    normalization, queueing, resampling, deduplication, or model logic.
    """

    def __init__(
        self,
        *,
        source: str,
        channel: str | None = None,
        recorder_instance_id: str | None = None,
        wall_clock_ns: Callable[[], int] = time.time_ns,
        monotonic_ns: Callable[[], int] = time.monotonic_ns,
        retain_raw_payload: bool = True,
    ) -> None:
        self.source = _clean_text(source, "source", required=True)
        self.channel = _clean_text(channel, "channel")
        self.recorder_instance_id = recorder_instance_id or str(uuid.uuid4())
        self._wall_clock_ns = wall_clock_ns
        self._monotonic_ns = monotonic_ns
        self._retain_raw_payload = bool(retain_raw_payload)
        self.process_start_wallclock_utc_ns = int(self._wall_clock_ns())
        self.process_start_monotonic_ns = int(self._monotonic_ns())
        self._sequence = 0
        self._lock = Lock()

    def stamp(self, raw_payload: bytes) -> ReceiptStamp:
        """Stamp first, before parsing. No event-time semantics are assumed here."""
        if not isinstance(raw_payload, (bytes, bytearray, memoryview)):
            raise TypeError("raw_payload must be bytes-like")
        payload = bytes(raw_payload)
        with self._lock:
            self._sequence += 1
            seq = self._sequence
            wall = int(self._wall_clock_ns())
            mono = int(self._monotonic_ns())
        if wall < 0 or mono < 0:
            raise ValueError("clock values must be non-negative")
        digest = hashlib.sha256(payload).hexdigest()
        return ReceiptStamp(
            schema=SCHEMA,
            recorder_version=RECORDER_VERSION,
            recorder_instance_id=self.recorder_instance_id,
            receipt_id=f"{self.recorder_instance_id}:{seq}",
            source=self.source,
            channel=self.channel,
            local_sequence=seq,
            receive_wallclock_utc_ns=wall,
            receive_wallclock_utc=_iso_utc_from_ns(wall),
            receive_monotonic_ns=mono,
            process_start_wallclock_utc_ns=self.process_start_wallclock_utc_ns,
            process_start_monotonic_ns=self.process_start_monotonic_ns,
            raw_payload_sha256=digest,
            raw_payload_size=len(payload),
            raw_payload_b64=base64.b64encode(payload).decode("ascii") if self._retain_raw_payload else None,
        )

    def parsed(
        self,
        stamp: ReceiptStamp,
        *,
        symbol: str | None,
        trading_day: str | None,
        market_event_time_raw: str | None,
        market_event_time_normalized: str | None,
        market_event_timezone: str | None,
        event_time_parse_status: str,
        price: float | None,
        source_sequence: str | int | None = None,
        parse_error: str | None = None,
    ) -> ParsedReceipt:
        """Attach parsed fields without changing the original receive stamp."""
        if stamp.recorder_instance_id != self.recorder_instance_id:
            raise ValueError("stamp belongs to another recorder instance")
        status = _clean_text(event_time_parse_status, "event_time_parse_status", required=True)
        if status not in {"PARSED", "UNPARSED", "INVALID"}:
            raise ValueError("event_time_parse_status must be PARSED/UNPARSED/INVALID")
        symbol = _clean_text(symbol, "symbol")
        if symbol is not None and symbol not in SUPPORTED_SYMBOLS:
            raise ValueError("unsupported symbol")
        if price is not None:
            price = float(price)
            if not (price > 0):
                raise ValueError("price must be positive when present")
        if status == "PARSED":
            if not market_event_time_normalized or not market_event_timezone:
                raise ValueError("PARSED event time requires normalized time and timezone")
        if status != "PARSED" and market_event_time_normalized is not None:
            raise ValueError("non-PARSED event time cannot have normalized time")
        return ParsedReceipt(
            schema=SCHEMA,
            recorder_version=RECORDER_VERSION,
            recorder_instance_id=self.recorder_instance_id,
            receipt_id=stamp.receipt_id,
            local_sequence=stamp.local_sequence,
            symbol=symbol,
            trading_day=_clean_text(trading_day, "trading_day"),
            market_event_time_raw=_clean_text(market_event_time_raw, "market_event_time_raw"),
            market_event_time_normalized=_clean_text(market_event_time_normalized, "market_event_time_normalized"),
            market_event_timezone=_clean_text(market_event_timezone, "market_event_timezone"),
            event_time_parse_status=status,
            price=price,
            source_sequence=None if source_sequence is None else str(source_sequence),
            parse_error=_clean_text(parse_error, "parse_error"),
        )


class AppendOnlyJsonl:
    """Minimal append-only JSONL sink.

    Each line is flushed. `fsync=True` is available for durability testing, but
    recorder overhead must be measured before any live deployment.
    """

    def __init__(self, path: str | Path, *, fsync: bool = False) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fsync = bool(fsync)
        self._lock = Lock()

    def append(self, record: ReceiptStamp | ParsedReceipt | Mapping[str, Any]) -> None:
        if hasattr(record, "__dataclass_fields__"):
            payload = asdict(record)  # type: ignore[arg-type]
        else:
            payload = dict(record)
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with self._lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(line)
                fh.flush()
                if self.fsync:
                    os.fsync(fh.fileno())


def validate_pair(stamp: ReceiptStamp, parsed: ParsedReceipt) -> None:
    """Reject joins that could silently mix recorder instances or sequence rows."""
    if stamp.schema != SCHEMA or parsed.schema != SCHEMA:
        raise ValueError("schema mismatch")
    if stamp.recorder_version != RECORDER_VERSION or parsed.recorder_version != RECORDER_VERSION:
        raise ValueError("recorder version mismatch")
    if stamp.recorder_instance_id != parsed.recorder_instance_id:
        raise ValueError("recorder instance mismatch")
    if stamp.receipt_id != parsed.receipt_id or stamp.local_sequence != parsed.local_sequence:
        raise ValueError("receipt identity mismatch")
