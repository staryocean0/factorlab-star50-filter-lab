"""Bounded V2 family and fixed-entry-unit index-direction simulation."""

from dataclasses import asdict, dataclass
from itertools import product

import numpy as np
import pandas as pd
from scipy.signal import lfilter

from star50_filter.slope_union import SlopeUnionConfig, coefficients, threshold_table


@dataclass(frozen=True)
class Policy:
    entry_alpha: float = 0.01
    exit_alpha: float = 0.05
    weight_power: float = 1.0
    volatility_window: int = 240
    entry_confirm: int = 1
    cooldown: int = 0

    def __post_init__(self):
        self.base()
        if type(self.entry_confirm) is not int or self.entry_confirm < 1:
            raise ValueError("positive integer confirmation required")
        if type(self.cooldown) is not int or self.cooldown < 0:
            raise ValueError("nonnegative integer cooldown required")

    def base(self):
        return SlopeUnionConfig(**{k: v for k, v in asdict(self).items() if k not in {"entry_confirm", "cooldown"}})

    @property
    def id(self):
        return (
            f"e{self.entry_alpha:g}_x{self.exit_alpha:g}_p{self.weight_power:g}"
            f"_w{self.volatility_window}_c{self.entry_confirm}_d{self.cooldown}"
        )


def family():
    return [
        Policy(*values) for values in product([0.001, 0.01, 0.05], [0.05, 0.15, 0.30], [0.0, 1.0, 2.0], [120, 240, 480], [1, 3], [0, 5])
    ]


def features(close):
    x = np.log(np.asarray(close, dtype=float))
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("finite positive prices required")
    a, b = coefficients(SlopeUnionConfig())
    y = lfilter([b, b], [1.0, -a], x - x[0])
    y[:120] = np.nan
    slopes = np.column_stack([pd.Series(y).diff(h).to_numpy() / h for h in range(1, 6)])
    sigma = {w: pd.Series(x).diff().rolling(w).std(ddof=1).shift(1).to_numpy() for w in [120, 240, 480]}
    return y, slopes, sigma


def targets(slopes, sigma, policy):
    table = threshold_table(policy.base())
    valid = np.isfinite(slopes).all(axis=1) & np.isfinite(sigma) & (sigma > 1e-12)
    entry = sigma[:, None] * table.entry_per_sigma.to_numpy()
    exit_ = sigma[:, None] * table.exit_per_sigma.to_numpy()
    el = (slopes > entry).any(axis=1) & valid
    es = (slopes < -entry).any(axis=1) & valid
    xl = (slopes < -exit_).any(axis=1) & valid
    xs = (slopes > exit_).any(axis=1) & valid
    ix = np.arange(len(valid))

    def confirmed(flag):
        return (ix - np.maximum.accumulate(np.where(~flag, ix, -1))) >= policy.entry_confirm

    el, es = confirmed(el), confirmed(es)
    events = np.flatnonzero(el | es | xl | xs)
    out = np.zeros(len(valid), dtype=np.int8)
    current, last_change, last_exit = 0, 0, -(10**9)
    for i in events:
        conflict = el[i] and es[i]
        can_enter = i > last_exit + policy.cooldown
        # After a cooldown all confirmation bars must be newly eligible.
        if policy.cooldown and i - policy.entry_confirm + 1 <= last_exit + policy.cooldown:
            can_enter = False
        long = el[i] and not conflict and can_enter
        short = es[i] and not conflict and can_enter
        new = current
        if current == 1 and xl[i]:
            new = -1 if short and policy.cooldown == 0 else 0
        elif current == -1 and xs[i]:
            new = 1 if long and policy.cooldown == 0 else 0
        elif current == 0:
            new = 1 if long else (-1 if short else 0)
        if new != current:
            out[last_change:i] = current
            if current:
                last_exit = i
            current, last_change = new, i
    out[last_change:] = current
    return out


def account(open_prices, times, decisions, prior_decision=0, fee_bps=2.0):
    """Positions at open i use decision i-1; terminal open closes all trades."""
    op = np.asarray(open_prices, float)
    signal = np.asarray(decisions)
    if len(op) != len(signal) or len(op) < 2 or not np.isfinite(op).all() or (op <= 0).any():
        raise ValueError("invalid execution prices or length")
    if not np.isin(signal, [-1, 0, 1]).all() or prior_decision not in [-1, 0, 1]:
        raise ValueError("invalid target")
    if not 0 <= fee_bps < 100:
        raise ValueError("invalid cost")
    fee = fee_bps / 10000
    p = np.r_[prior_decision, signal[:-1]].astype(np.int8)
    terminal_held = int(p[-2])
    p[-1] = 0
    changes = np.flatnonzero(p != np.r_[0, p[:-1]])
    nav = np.ones(len(op))
    capital, last = 1.0, 0
    trades = []
    for start, end in zip(changes[:-1], changes[1:], strict=True):
        side = int(p[start])
        if side == 0:
            continue
        nav[last:start] = capital
        ratio = op[start : end + 1] / op[start]
        mark = 1 + (side * (ratio - 1) - fee) / (1 + fee)
        final = 1 + (side * (ratio[-1] - 1) - fee * (1 + ratio[-1])) / (1 + fee)
        if min(mark.min(), final) <= 0:
            raise ValueError("simulated account insolvent")
        nav[start : end + 1] = capital * mark
        capital *= final
        nav[end] = capital
        last = end
        trades.append(
            {
                "entry_i": int(start),
                "exit_i": int(end),
                "side": side,
                "entry_time": str(times.iloc[start]),
                "exit_time": str(times.iloc[end]),
                "entry": op[start],
                "exit": op[end],
                "bars": int(end - start),
                "gross_bp": side * (ratio[-1] - 1) * 10000,
                "net_bp": (final - 1) * 10000,
                "forced_year_end": bool(end == len(op) - 1 and terminal_held != 0),
            }
        )
    nav[last:] = capital
    ledger = pd.DataFrame(
        trades,
        columns=["entry_i", "exit_i", "side", "entry_time", "exit_time", "entry", "exit", "bars", "gross_bp", "net_bp", "forced_year_end"],
    )
    index = pd.DatetimeIndex(times)
    daily = pd.Series(nav, index=index).groupby(index.strftime("%Y-%m-%d")).last()
    daily_return = daily.pct_change().fillna(daily.iloc[0] - 1)
    day_frame = pd.DataFrame({"nav": daily, "return": daily_return})
    values = ledger.net_bp.to_numpy(dtype=float)
    metrics = summary(ledger, day_frame, nav)
    assert np.isclose(np.prod(1 + values / 10000), nav[-1], rtol=1e-10)
    return ledger, day_frame, nav, metrics


def summary(trades, daily, nav=None):
    values = trades.net_bp.to_numpy(dtype=float)
    r = daily["return"].to_numpy()
    curve = np.cumprod(1 + r) if nav is None else nav
    count = len(values)
    std = r.std(ddof=1) if len(r) > 1 else 0.0
    losses = -values[values < 0].sum()
    return {
        "trades": count,
        "mean_net_bp": float(values.mean()) if count else 0.0,
        "median_net_bp": float(np.median(values)) if count else 0.0,
        "win_rate": float((values > 0).mean()) if count else 0.0,
        "profit_factor": float(values[values > 0].sum() / losses) if losses else 0.0,
        "mean_bars": float(trades.bars.mean()) if count else 0.0,
        "short_hold_fraction": float((trades.bars <= 5).mean()) if count else 0.0,
        "sharpe": float(r.mean() / std * np.sqrt(252)) if std else 0.0,
        "return": float(curve[-1] - 1),
        "cagr": float(curve[-1] ** (252 / len(r)) - 1),
        "mdd": float((1 - curve / np.maximum.accumulate(np.r_[1.0, curve])[1:]).max()),
        "sum_trade_net_bp": float(values.sum()),
    }
