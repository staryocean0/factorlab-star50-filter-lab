"""State-only E-15 delivery prototype; no market loader, fit, or trading action.

Input states must come from the frozen V9 calculation. Provenance fields are
assertions by the caller, not proof that its upstream calculation was correct.
This slice does not implement close events, recovery probabilities, or serving.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SYMBOLS = ("000688.SH", "000852.SH")
STATES = ("NORMAL", "UNSAFE", "RECOVERING")
RISK_STATES = ("UNSAFE", "RECOVERING")
V9_BLOB = "ae2a7e095df58692ef9df0dfee5856cac727ca44"
V19_BLOB = "ee2fce299d5ee21abf1ab2c2c5183bac101ae822"
TIMING_BASES = ("owner_realtime_assumption", "observed_reception_log")


def _aware(value: datetime, name: str) -> None:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")


@dataclass(frozen=True)
class Annotation:
    symbol: str
    bar_end: datetime
    decision_time: datetime
    published_at: datetime
    timing_basis: str
    state: str | None
    previous_confirmed_state: str | None
    partial_state: str | None
    transition: str | None
    availability_reason: str
    state_basis: str
    exit_pending: bool
    observation_time: datetime | None
    observation_known_at: datetime | None
    previous_bar_end: datetime | None
    previous_state_known_at: datetime | None
    schema: str = "causal_kline_state_delivery_v1_e15_prototype"
    frozen_partial_runner_blob: str = V9_BLOB
    frozen_machine_blob: str = V19_BLOB
    recovery_probabilities: None = None
    recovery_availability: str = "NOT_ATTACHED_IN_CONTRACT_SLICE"
    production_authority: bool = False

    @property
    def bucket_key(self) -> str:
        """An attribute key only, never a trade/position/router instruction."""
        return "UNAVAILABLE" if self.state is None else f"{self.state}|{self.state_basis}"

    def as_dict(self) -> dict:
        out = asdict(self)
        for key, value in out.items():
            if isinstance(value, datetime):
                out[key] = value.isoformat()
        out["bucket_key"] = self.bucket_key
        return out


def emit_e15(
    *, symbol: str, bar_end: datetime, published_at: datetime,
    previous_bar_end: datetime | None, previous_state_known_at: datetime | None,
    previous_state: str | None, partial_state: str | None,
    observation_time: datetime | None, observation_known_at: datetime | None,
    reference_chain_valid: bool, checkpoint_available: bool,
    source_runner_blob: str, timing_basis: str,
) -> Annotation:
    """Wrap frozen states without accepting current-final labels or future paths.

    `available_at` is intentionally not an input: the repository's historical
    retrieval timestamp must not be treated as an intraday availability clock.
    Inputs unavailable at the E-15 decision produce an explicit missing state.
    Malformed inputs raise; they are never silently converted to NORMAL.
    """
    if symbol not in SYMBOLS or source_runner_blob != V9_BLOB:
        raise ValueError("unsupported symbol or non-frozen partial-state authority")
    if timing_basis not in TIMING_BASES:
        raise ValueError("declare the realtime timing basis")
    if type(reference_chain_valid) is not bool or type(checkpoint_available) is not bool:
        raise ValueError("availability flags must be booleans")
    for value in (previous_state, partial_state):
        if value is not None and value not in STATES:
            raise ValueError("unknown state vocabulary")
    _aware(bar_end, "bar_end")
    _aware(published_at, "published_at")
    # This prototype carries no 2026 realtime data/serving authority.
    if not 2021 <= bar_end.astimezone(ZoneInfo("Asia/Shanghai")).year <= 2025:
        raise ValueError("outside the bounded 2021-2025 realtime prototype scope")
    decision = bar_end - timedelta(seconds=15)
    start = bar_end - timedelta(minutes=5)
    if published_at < decision:
        raise ValueError("publication cannot precede the decision")
    for name, value in (("previous_bar_end", previous_bar_end),
                        ("previous_state_known_at", previous_state_known_at),
                        ("observation_time", observation_time),
                        ("observation_known_at", observation_known_at)):
        if value is not None:
            _aware(value, name)
    if previous_bar_end is not None and previous_bar_end > start:
        raise ValueError("previous confirmed bar overlaps the current bar")
    if previous_state_known_at is not None and previous_bar_end is not None:
        if previous_state_known_at < previous_bar_end:
            raise ValueError("previous final state cannot be known before its close")
    if observation_known_at is not None and observation_time is not None:
        if observation_known_at < observation_time:
            raise ValueError("observation cannot be known before it occurs")
    reason = "AVAILABLE"
    if not reference_chain_valid or any(x is None for x in (
        previous_bar_end, previous_state_known_at, previous_state
    )):
        reason = "REFERENCE_UNAVAILABLE"
    elif not checkpoint_available or any(x is None for x in (
        partial_state, observation_time, observation_known_at
    )):
        reason = "CHECKPOINT_UNAVAILABLE"
    elif (previous_state_known_at > decision or observation_known_at > decision
          or observation_time > decision):
        reason = "INPUT_NOT_KNOWN_BY_DECISION"
    elif observation_time <= start:
        reason = "OBSERVATION_OUTSIDE_CURRENT_BAR"
    state = None
    basis = "UNAVAILABLE"
    pending = False
    if reason == "AVAILABLE":
        if partial_state in RISK_STATES:
            state, basis = partial_state, "E15_PROVISIONAL"
        elif previous_state in RISK_STATES:
            state, basis, pending = previous_state, "PRIOR_CONFIRMED_EXIT_PENDING", True
        else:
            state, basis = "NORMAL", "E15_PROVISIONAL"
    # Suppress even input state fields when guards fail: no downstream bypass.
    return Annotation(
        symbol=symbol, bar_end=bar_end, decision_time=decision,
        published_at=published_at, timing_basis=timing_basis, state=state,
        previous_confirmed_state=previous_state if state is not None else None,
        partial_state=partial_state if state is not None else None,
        transition=f"{previous_state}->{state}" if state is not None else None,
        availability_reason=reason, state_basis=basis, exit_pending=pending,
        observation_time=observation_time, observation_known_at=observation_known_at,
        previous_bar_end=previous_bar_end, previous_state_known_at=previous_state_known_at,
    )


def visible_at(annotation: Annotation, consumer_time: datetime) -> Annotation | None:
    """Do not backdate publication or carry an E-15 snapshot past bar close.

    Close confirmation needs a separate close-event adapter (not in this slice).
    A visible UNAVAILABLE annotation is still missing information, not safety.
    """
    _aware(consumer_time, "consumer_time")
    if annotation.published_at <= consumer_time < annotation.bar_end:
        return annotation
    return None
