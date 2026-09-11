"""Bounded research consumer: immutable D2 events + D4 E15 numeric enrichment.

No prices, training, future labels, quantile gates, orders or network access.
Artifact identity is verified by run_acceptance.py, not by caller claims alone.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, time, timedelta
import hashlib
import json
import math
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")
SYMBOLS = ("000688.SH", "000852.SH")
STATES = ("NORMAL", "UNSAFE", "RECOVERING")
RISK = ("UNSAFE", "RECOVERING")
BLOBS = {
    "frozen_v9_blob": "ae2a7e095df58692ef9df0dfee5856cac727ca44",
    "frozen_v19_blob": "ee2fce299d5ee21abf1ab2c2c5183bac101ae822",
    "frozen_v16_blob": "1f88966cf5dd3fb102f0d75746d5d00434555647",
}
EVENT_FIELDS = frozenset("age_clock availability_reason bar_end bucket_key decision_time event_id event_type exit_pending frozen_v16_blob frozen_v19_blob frozen_v9_blob observation_known_at observation_time partial_state previous_confirmed_state probability_target_clock production_authority published_at recent_shock_age_bars recovery_probabilities recovery_reason schema shock shock_intensity state state_basis symbol timing_basis transition valid_until vol_ratio".split())
ATTRIBUTE_FIELDS = frozenset("symbol bar_end decision_time published_at valid_until observation_time state state_basis availability_reason available shock_intensity vol_ratio lag_intensity lag_ratio delta_intensity delta_ratio numeric_bucket".split())
SCHEMA = "state_degree_research_consumer_d5_v1"
EXTRA_FIELDS = frozenset("source_schema source_event_sha256 numeric_basis numeric_availability lag_intensity lag_ratio delta_intensity delta_ratio delta_status observation_age_seconds quantile_encoding information_scope".split())
OUTPUT_FIELDS = EVENT_FIELDS | EXTRA_FIELDS


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def aware(value: datetime | str) -> datetime:
    d = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(d, datetime) or d.utcoffset() is None:
        raise ValueError("timezone-aware time required")
    return d.astimezone(TZ)


def csv_time(value: str, timezone: str) -> datetime:
    if timezone != "Asia/Shanghai":
        raise ValueError("D4 CSV timezone contract mismatch")
    d = datetime.fromisoformat(value)
    if d.utcoffset() is not None:
        raise ValueError("expected D4 declared-naive wallclock CSV")
    return d.replace(tzinfo=TZ)


def number(value: object, *, nullable: bool = False) -> float | None:
    if value is None or value == "":
        if nullable:
            return None
        raise ValueError("missing numeric value")
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric measurement")
    n = float(value)
    if not math.isfinite(n):
        raise ValueError("non-finite numeric value")
    return n


def exact_fields(row: dict, fields: frozenset) -> None:
    if set(row) != fields:
        raise ValueError(f"column contract: extra={sorted(set(row)-fields)}, missing={sorted(fields-set(row))}")


def in_session(d: datetime) -> bool:
    t = aware(d).time()
    return time(9, 30) <= t <= time(11, 30) or time(13) <= t <= time(15)


def expected_expiry(end: datetime, kind: str) -> datetime:
    if kind == "E15":
        return end
    if end.time() == time(11, 30):
        return end.replace(hour=13, minute=4, second=45)
    if end.time() == time(15):
        return end + timedelta(microseconds=1)
    return end + timedelta(minutes=4, seconds=45)


@dataclass(frozen=True, slots=True)
class Snapshot:
    event_id: str
    symbol: str
    decision: datetime
    published: datetime
    expires: datetime
    payload: str

    def as_dict(self) -> dict:
        # A fresh deep copy: callers cannot rewrite history through nested lists.
        return json.loads(self.payload)


def build_snapshot(event: dict, attributes: dict | None = None, *, csv_timezone: str = "Asia/Shanghai") -> Snapshot:
    exact_fields(event, EVENT_FIELDS)
    e = json.loads(canonical(event))
    if e["schema"] != "causal_kline_delivery_d2_v1" or e["symbol"] not in SYMBOLS:
        raise ValueError("source schema/symbol mismatch")
    if any(e[k] != v for k, v in BLOBS.items()):
        raise ValueError("frozen source version mismatch")
    if e["production_authority"] is not False or e["timing_basis"] != "owner_realtime_assumption":
        raise ValueError("no production or measured-feed authority")
    if e["age_clock"] != "5m_bar_steps_within_trading_day" or e["probability_target_clock"] != "frozen_V16_horizon_labels_at_reference_bar_end":
        raise ValueError("frozen probability/age clock mismatch")
    kind = e["event_type"]
    if kind not in ("E15", "CLOSE"):
        raise ValueError("unsupported event type")
    end, decision, pub, expiry = [aware(e[k]) for k in ("bar_end", "decision_time", "published_at", "valid_until")]
    t = end.time()
    if not (2021 <= end.year <= 2025 and end.second == end.microsecond == 0 and end.minute % 5 == 0
            and (time(9, 35) <= t <= time(11, 30) or time(13, 5) <= t <= time(15))):
        raise ValueError("outside bounded bar grid")
    if e["event_id"] != f"{e['symbol']}|{end.isoformat()}|{kind}":
        raise ValueError("event key mismatch")
    if decision != end - (timedelta(seconds=15) if kind == "E15" else timedelta()):
        raise ValueError("wrong decision clock")
    if pub < decision or expiry != expected_expiry(end, kind):
        raise ValueError("publication backdating or changed expiry")
    obs = aware(e["observation_time"]) if e["observation_time"] else None
    known = aware(e["observation_known_at"]) if e["observation_known_at"] else None
    if obs is not None and (known is None or not obs <= known <= decision):
        raise ValueError("observation unknown at decision")
    if obs is not None and (obs < end-timedelta(minutes=5) or (kind == "CLOSE" and obs != end)):
        raise ValueError("observation belongs to a different bar/clock")
    if type(e["exit_pending"]) is not bool:
        raise ValueError("exit_pending must be boolean")
    for key in ("state", "partial_state", "previous_confirmed_state"):
        if e[key] is not None and e[key] not in STATES:
            raise ValueError("unknown risk state")
    available = e["availability_reason"] == "AVAILABLE"
    if available:
        if e["state"] is None or obs is None or e["previous_confirmed_state"] is None or type(e["shock"]) is not bool:
            raise ValueError("incomplete available state")
        if any(number(e[k]) < 0 for k in ("shock_intensity", "vol_ratio")):
            raise ValueError("negative risk magnitude")
        if kind == "E15":
            p, previous = e["partial_state"], e["previous_confirmed_state"]
            if p is None:
                raise ValueError("missing partial state")
            state = p if p in RISK else previous if previous in RISK else "NORMAL"
            pending = p == "NORMAL" and previous in RISK
            basis = "PRIOR_CONFIRMED_EXIT_PENDING" if pending else "E15_PROVISIONAL"
            if (e["state"], e["exit_pending"], e["state_basis"]) != (state, pending, basis):
                raise ValueError("V19 semantics drift")
        elif e["partial_state"] is not None or e["exit_pending"] or e["state_basis"] != "CLOSE_CONFIRMED":
            raise ValueError("close/provisional semantics mixed")
    elif any(e[k] is not None for k in ("state", "partial_state", "previous_confirmed_state", "shock_intensity", "vol_ratio", "shock", "recovery_probabilities")):
        raise ValueError("unavailable fields must be suppressed")
    if e["bucket_key"] != (f"{e['state']}|{e['state_basis']}" if available else "UNAVAILABLE"):
        raise ValueError("state bucket mismatch")
    probs = e["recovery_probabilities"]
    if probs is not None:
        if not available or e["recovery_reason"] != "scored" or not isinstance(probs, list) or len(probs) != 3:
            raise ValueError("recovery availability mismatch")
        pp = [number(p) for p in probs]
        if not 0 <= pp[0] <= pp[1] <= pp[2] <= 1:
            raise ValueError("invalid recovery curve")
    elif e["recovery_reason"] == "scored":
        raise ValueError("missing scored curve")
    extras = dict(lag_intensity=None, lag_ratio=None, delta_intensity=None, delta_ratio=None)
    numeric_basis = "D2_CLOSE_CONFIRMED" if kind == "CLOSE" else "D4_E15_ENRICHED"
    numeric_status = "AVAILABLE" if available else e["availability_reason"]
    delta_status = "NOT_DEFINED_FOR_CLOSE" if kind == "CLOSE" else "DESCRIPTIVE_ONLY"
    if kind == "CLOSE" and attributes is not None:
        raise ValueError("E15 enrichment cannot be attached to CLOSE")
    if kind == "E15":
        if attributes is None:
            numeric_status, delta_status = "D4_ROW_MISSING", "D4_ROW_MISSING"
            e["shock_intensity"] = e["vol_ratio"] = None
        else:
            a = attributes
            exact_fields(a, ATTRIBUTE_FIELDS)
            if a["symbol"] != e["symbol"] or a["available"] not in ("True", "False") or (a["available"] == "True") != available:
                raise ValueError("D4 identity/availability mismatch")
            for k in ("bar_end", "decision_time", "published_at", "valid_until", "observation_time"):
                av = csv_time(a[k], csv_timezone) if a[k] else None
                ev = aware(e[k]) if e[k] else None
                if av != ev:
                    raise ValueError(f"D4 clock mismatch: {k}")
            for k in ("state", "state_basis", "availability_reason"):
                if (a[k] or None) != e[k]:
                    raise ValueError(f"D4 state mismatch: {k}")
            for k in ("shock_intensity", "vol_ratio"):
                v = number(a[k], nullable=True)
                if (v is None) != (e[k] is None) or (v is not None and abs(v-e[k]) > 1e-12):
                    raise ValueError(f"D4 magnitude mismatch: {k}")
            extras = {k: number(a[k], nullable=not available) for k in extras}
            if not available and any(v is not None for v in extras.values()):
                raise ValueError("unavailable enhancement leak")
            if available:
                for current, lag, delta in (("shock_intensity", "lag_intensity", "delta_intensity"), ("vol_ratio", "lag_ratio", "delta_ratio")):
                    if extras[lag] < 0 or abs((e[current]-extras[lag])-extras[delta]) > 1e-12:
                        raise ValueError("delta/lag mismatch")
            # numeric_bucket deliberately NOT delivered: fitted descriptive encoding.
    out = dict(e, **extras, schema=SCHEMA, source_schema=event["schema"],
               source_event_sha256=hashlib.sha256(canonical(event).encode()).hexdigest(),
               numeric_basis=numeric_basis, numeric_availability=numeric_status,
               delta_status=delta_status if available else "UNAVAILABLE",
               observation_age_seconds=(decision-obs).total_seconds() if obs else None,
               quantile_encoding="OMITTED_NOT_ADMITTED_AS_GATE",
               information_scope="D4_E15_SPECIFIED_ENDPOINTS_ONLY" if kind == "E15" else "D2_CONTEXT_NOT_D4_E15_UTILITY")
    return Snapshot(e["event_id"], e["symbol"], decision, pub, expiry, canonical(out))


class ResearchConsumer:
    """Append-only, per-symbol as-of index. Missing/latest-expired never falls back."""
    def __init__(self) -> None:
        self._times = {s: [] for s in SYMBOLS}
        self._records = {s: [] for s in SYMBOLS}
        self._ids: dict[str, str] = {}
        self._last_received: datetime | None = None

    def ingest(self, snapshot: Snapshot, *, received_at: datetime | str) -> bool:
        received = aware(received_at)
        if received < snapshot.published:
            raise ValueError("cannot receive before publication")
        old = self._ids.get(snapshot.event_id)
        if old is not None:
            if old != snapshot.payload:
                raise ValueError("conflicting duplicate; never revise a published event")
            return False
        if self._last_received is not None and received < self._last_received:
            raise ValueError("out-of-order receipt")
        history = self._records[snapshot.symbol]
        if history and snapshot.decision <= history[-1][1].decision:
            raise ValueError("out-of-order source event")
        self._ids[snapshot.event_id] = snapshot.payload
        self._times[snapshot.symbol].append(received)
        history.append((received, snapshot))
        self._last_received = received
        return True

    def as_of(self, symbol: str, when: datetime | str) -> dict:
        t = aware(when)
        if symbol not in SYMBOLS:
            raise ValueError("unsupported consumer symbol")
        result = dict(symbol=symbol, as_of=t.isoformat(), status="NO_CURRENT_SNAPSHOT", reason="NO_PUBLISHED_EVENT", snapshot=None,
                      production_authority=False, receipt_basis="HISTORICAL_REPLAY_OR_SYNTHETIC_DELAY_NOT_MEASURED_FEED")
        if not in_session(t):
            result["reason"] = "SESSION_CLOSED"
            return result
        i = bisect_right(self._times[symbol], t) - 1
        if i < 0:
            return result
        received, record = self._records[symbol][i]
        if t >= record.expires:
            result["reason"] = "LATEST_EVENT_EXPIRED"
            return result
        view = record.as_dict()
        status = "UNAVAILABLE" if view["state"] is None else "STATE_ONLY" if view["numeric_availability"] != "AVAILABLE" else "AVAILABLE"
        result.update(status=status, reason=view["availability_reason"] if status != "STATE_ONLY" else view["numeric_availability"],
                      snapshot=view, consumer_received_at=received.isoformat(), consumer_visible_at=received.isoformat())
        return result
