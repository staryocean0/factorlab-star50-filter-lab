"""Frozen research-only post-shock state machine.

Implements the supported abstraction:
    observed first shock -> Unsafe -> Recovering

There is intentionally no online Clean transition.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt, isfinite
from typing import Optional


@dataclass
class PostShockState:
    state: str = "IDLE"
    sigma_pre: Optional[float] = None
    episode_session: Optional[str] = None
    event_minute: Optional[int] = None
    post_returns_bp: list[Optional[float]] = field(default_factory=list)
    recovery_ratio: Optional[float] = None

    def start(self, *, session: str, event_minute: int, sigma_pre: float) -> None:
        if self.state not in {"IDLE", "ENDED"}:
            raise ValueError("episode already active")
        if not session:
            raise ValueError("session required")
        if not (isfinite(sigma_pre) and sigma_pre > 0):
            raise ValueError("sigma_pre must be positive and finite")
        self.state = "UNSAFE"
        self.sigma_pre = float(sigma_pre)
        self.episode_session = str(session)
        self.event_minute = int(event_minute)
        self.post_returns_bp = []
        self.recovery_ratio = None

    def observe_completed_minute(
        self,
        *,
        session: str,
        minute: int,
        return_bp: Optional[float],
        quality_valid: bool,
    ) -> str:
        """Consume one completed post-shock minute causally.

        State is based only on the latest five completed post-shock minute returns.
        Invalid/missing inputs make the current state UNKNOWN rather than zero-volatility.
        A session change ends the episode; no lunch/overnight bridge is allowed.
        """
        if self.state in {"IDLE", "ENDED"}:
            raise ValueError("no active episode")
        if session != self.episode_session:
            self.state = "ENDED"
            self.recovery_ratio = None
            return self.state
        if minute <= int(self.event_minute):
            raise ValueError("observation must be after event minute")

        if quality_valid and return_bp is not None and isfinite(float(return_bp)):
            x: Optional[float] = float(return_bp)
        else:
            x = None
        self.post_returns_bp.append(x)

        # The first five post-shock minutes remain explicitly Unsafe until a
        # complete causal five-minute window can be evaluated.
        if len(self.post_returns_bp) < 5:
            self.state = "UNSAFE" if x is not None else "UNKNOWN"
            self.recovery_ratio = None
            return self.state

        last5 = self.post_returns_bp[-5:]
        if any(v is None for v in last5):
            self.state = "UNKNOWN"
            self.recovery_ratio = None
            return self.state

        ratio = sqrt(sum(v * v for v in last5) / 5.0) / float(self.sigma_pre)
        self.recovery_ratio = ratio
        self.state = "UNSAFE" if ratio >= 1.5 else "RECOVERING"
        return self.state

    def end_session(self) -> None:
        if self.state == "IDLE":
            return
        self.state = "ENDED"
        self.recovery_ratio = None

    @property
    def online_clean(self) -> bool:
        """Always false until a future independent protocol validates Clean."""
        return False
