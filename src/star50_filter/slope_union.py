"""Research-only half-day lowpass with correlated 1..5-minute slope unions.

Targets are decided at bar close; this module neither fills nor places orders.
See docs/research/half_day_slope_union_v1/whitepaper.md for model limitations.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy.signal import lfilter
from scipy.stats import norm

LOOKBACKS = (1, 2, 3, 4, 5)


@dataclass(frozen=True)
class SlopeUnionConfig:
    cutoff_minutes: float = 120.0
    volatility_window: int = 240
    entry_alpha: float = 0.01
    exit_alpha: float = 0.05
    weight_power: float = 1.0
    sigma_floor: float = 1e-12
    direction: str = "long_short"

    def __post_init__(self) -> None:
        numeric = (
            self.cutoff_minutes,
            self.entry_alpha,
            self.exit_alpha,
            self.weight_power,
            self.sigma_floor,
        )
        if not all(math.isfinite(v) for v in numeric):
            raise ValueError("configuration must be finite")
        if not 4 <= self.cutoff_minutes <= 100_000:
            raise ValueError("cutoff_minutes must be in [4, 100000]")
        if type(self.volatility_window) is not int or self.volatility_window < 20:
            raise ValueError("volatility_window must be an integer >= 20")
        if not 0 < self.entry_alpha <= self.exit_alpha < 0.5:
            raise ValueError("require 0 < entry_alpha <= exit_alpha < 0.5")
        if not 0 <= self.weight_power <= 8 or self.sigma_floor <= 0:
            raise ValueError("require weight_power in [0, 8] and positive sigma_floor")
        if self.direction not in {"long_short", "long_only", "short_only"}:
            raise ValueError("unknown direction")

    @property
    def fingerprint(self) -> str:
        identity = {"schema": "star50.half_day_slope_union@1.0", **asdict(self)}
        return hashlib.sha256(json.dumps(identity, sort_keys=True, allow_nan=False).encode()).hexdigest()


def coefficients(config: SlopeUnionConfig) -> tuple[float, float]:
    k = math.tan(math.pi / config.cutoff_minutes)
    return (1 - k) / (1 + k), k / (1 + k)


def slope_covariance(config: SlopeUnionConfig) -> np.ndarray:
    """Steady-state Cov(s_h, s_g) with independent unit-variance returns."""
    a, b = coefficients(config)

    def gamma(lag: int) -> float:
        return b if lag == 0 else b * (1 + a) * a ** (lag - 1) / 2

    return np.array([[sum(gamma(abs(i - j)) for i in range(h) for j in range(g)) / (h * g) for g in LOOKBACKS] for h in LOOKBACKS])


def threshold_table(config: SlopeUnionConfig = SlopeUnionConfig()) -> pd.DataFrame:
    h = np.asarray(LOOKBACKS, dtype=float)
    weights = h**config.weight_power
    weights /= weights.sum()
    scale = np.sqrt(np.diag(slope_covariance(config)))
    return pd.DataFrame(
        {
            "lookback": LOOKBACKS,
            "weight": weights,
            "slope_sd_per_sigma": scale,
            "entry_per_sigma": norm.isf(config.entry_alpha * weights / 2) * scale,
            "exit_per_sigma": norm.isf(config.exit_alpha * weights / 2) * scale,
        }
    )


def transition(
    current: int,
    *,
    entry_long: bool,
    entry_short: bool,
    exit_long: bool,
    exit_short: bool,
    direction: str = "long_short",
) -> tuple[int, str]:
    """Pure target-state transition; raw entry conflicts are resolved before mode."""
    if direction not in {"long_short", "long_only", "short_only"}:
        raise ValueError("unknown direction")
    if current not in {-1, 0, 1}:
        raise ValueError("target must be -1, 0 or +1")
    if (direction == "long_only" and current == -1) or (direction == "short_only" and current == 1):
        raise ValueError("current target conflicts with direction mode")
    conflict = entry_long and entry_short
    can_long = entry_long and not conflict and direction != "short_only"
    can_short = entry_short and not conflict and direction != "long_only"
    if current == 1:
        if exit_long:
            return (-1, "reverse_short") if can_short else (0, "exit_long")
        return 1, "hold_long"
    if current == -1:
        if exit_short:
            return (1, "reverse_long") if can_long else (0, "exit_short")
        return -1, "hold_short"
    if can_long:
        return 1, "enter_long"
    if can_short:
        return -1, "enter_short"
    return 0, "entry_conflict" if conflict else "flat"


def _validated_bars(bars: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp", "trading_minute", "close"}
    if not required.issubset(bars.columns) or bars.empty:
        raise ValueError("nonempty timestamp/trading_minute/close input required")
    out = bars.loc[:, ["timestamp", "trading_minute", "close"]].copy()
    stamps = pd.to_datetime(out.timestamp, errors="raise")
    if stamps.isna().any() or stamps.dt.tz is None:
        raise ValueError("timestamps must be nonmissing and timezone aware")
    stamps = stamps.dt.tz_convert("Asia/Shanghai")
    if stamps.duplicated().any() or not stamps.is_monotonic_increasing:
        raise ValueError("timestamps must be strictly increasing")
    minute = stamps.dt.hour * 60 + stamps.dt.minute
    in_session = minute.between(571, 690) | minute.between(781, 900)
    if not in_session.all() or (stamps != stamps.dt.floor("min")).any():
        raise ValueError("expected complete native 1m session close labels")
    ordinal = out.trading_minute.to_numpy()
    if not pd.api.types.is_integer_dtype(out.trading_minute.dtype):
        raise ValueError("trading_minute must be integer")
    if out.trading_minute.isna().any() or not np.all(np.diff(ordinal) == 1):
        raise ValueError("missing or duplicate trading minute")
    for i in range(1, len(stamps)):
        previous, now = stamps.iloc[i - 1], stamps.iloc[i]
        same_day = previous.date() == now.date()
        consecutive = same_day and now - previous == pd.Timedelta(minutes=1)
        lunch = same_day and minute.iloc[i - 1] == 690 and minute.iloc[i] == 781
        overnight = not same_day and minute.iloc[i - 1] == 900 and minute.iloc[i] == 571
        if not (consecutive or lunch or overnight):
            raise ValueError("non-1m gap inside trading session")
    prices = out.close.to_numpy(dtype=float)
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise ValueError("close prices must be positive and finite")
    out["timestamp"] = stamps
    out["close"] = prices
    return out.reset_index(drop=True)


def build_signals(
    bars: pd.DataFrame,
    config: SlopeUnionConfig = SlopeUnionConfig(),
) -> pd.DataFrame:
    """Return causal diagnostics and close targets on validated native 1m bars.

    Prefix recomputation starts flat from the same first bar. Streaming callers
    must retain that prefix; chunk resets are not a continuation mechanism.
    """
    out = _validated_bars(bars)
    x = np.log(out.close.to_numpy())
    a, b = coefficients(config)
    y = lfilter([b, b], [1.0, -a], x - x[0])
    warmup = math.ceil(config.cutoff_minutes)
    y[:warmup] = np.nan
    slopes = np.column_stack([pd.Series(y).diff(h).to_numpy() / h for h in LOOKBACKS])
    sigma = pd.Series(x).diff().rolling(config.volatility_window).std(ddof=1).shift(1).to_numpy()
    table = threshold_table(config)
    entry = sigma[:, None] * table.entry_per_sigma.to_numpy()
    exits = sigma[:, None] * table.exit_per_sigma.to_numpy()
    ready = np.isfinite(slopes).all(axis=1) & np.isfinite(sigma) & (sigma > config.sigma_floor)
    comparisons = {
        "entry_long": slopes > entry,
        "entry_short": slopes < -entry,
        "exit_long": slopes < -exits,
        "exit_short": slopes > exits,
    }
    flags = {}
    for name, hits in comparisons.items():
        hits &= ready[:, None]
        out[name + "_mask"] = (hits * (1 << np.arange(5))).sum(axis=1)
        flags[name] = hits.any(axis=1)
    current = 0
    targets, priors, reasons = [], [], []
    for i in range(len(out)):
        priors.append(current)
        if ready[i]:
            current, reason = transition(
                current,
                **{key: bool(value[i]) for key, value in flags.items()},
                direction=config.direction,
            )
        else:
            reason = "not_ready_hold_target"
        targets.append(current)
        reasons.append(reason)
    out["lowpass_log_relative"] = y
    out["sigma_prior"] = sigma
    out["ready"] = ready
    out["entry_conflict"] = flags["entry_long"] & flags["entry_short"]
    out["prior_target"] = priors
    out["target_at_close"] = targets
    out["reason"] = reasons
    for index, h in enumerate(LOOKBACKS):
        out[f"slope_{h}"] = slopes[:, index]
        out[f"entry_threshold_{h}"] = entry[:, index]
        out[f"exit_threshold_{h}"] = exits[:, index]
    out.attrs.update(
        {
            "strategy_id": "star50_half_day_lowpass",
            "version": "slope_union_v1",
            "config_sha256": config.fingerprint,
            "earliest_execution": "next_tradable_open",
            "production_authority": False,
            "fills_computed": False,
        }
    )
    return out
