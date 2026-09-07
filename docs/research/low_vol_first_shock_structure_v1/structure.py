"""Frozen low-volatility first-shock conditional-structure measurements.

This module contains no market-data loader and no event-label implementation.
The runner must reuse the sealed first_shock_gate/seconds_v2 definitions.  The
functions here only measure M1--M4 and evaluate already-labelled decision rows.
No returns/P&L/trading labels are accepted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

SEED = 20260907
PRIMARY_RANGE_BP = 30.0
EPS_RV = 1e-16
CALIBRATION_YEAR = 2023
EVALUATION_YEARS = (2024, 2025)
MEASURES = ("M1", "M2", "M3", "M4")
FORBIDDEN_COLUMNS = (
    "pnl", "profit", "loss", "drawdown", "mdd", "sharpe", "position",
    "trade_result", "future_return", "forward_return", "ret_fwd",
)


class StudyError(ValueError):
    pass


def assert_results_blind(columns: Iterable[str]) -> None:
    for col in columns:
        low = str(col).lower()
        if any(token in low for token in FORBIDDEN_COLUMNS):
            raise StudyError(f"results-blind violation: {col}")


def _rolling_window(a: np.ndarray, n: int) -> np.ndarray:
    a = np.asarray(a, float)
    if a.ndim != 1 or n < 1:
        raise StudyError("rolling input must be a vector")
    if len(a) < n:
        return np.empty((0, n))
    return np.lib.stride_tricks.sliding_window_view(a, n)


def fine_measurements(sample: dict, minute_returns_bp: np.ndarray) -> pd.DataFrame:
    """Compute M1/M2 raw inputs at minute ends from a strict 15-second path.

    ``sample`` must be the result of the frozen ``seconds_v2.sample_session``
    called with ``step=15, gap_limit=3``. A complete 5-minute window therefore
    contains 20 known 15-second returns and 21 known endpoint prices. No missing
    fine return is filled or treated as zero.
    """
    sec = np.asarray(sample["second"], float)
    price = np.asarray(sample["price"], float)
    r15 = np.asarray(sample["return_bp"], float)
    if len(sec) != 481 or len(price) != 481 or len(r15) != 481:
        raise StudyError("expected full 0..7200 15-second grid")
    if not np.array_equal(sec, np.arange(0, 7201, 15)):
        raise StudyError("unexpected 15-second grid")
    r1 = np.asarray(minute_returns_bp, float)
    if len(r1) != 120:
        raise StudyError("minute return grid must have 120 rows")

    rows = []
    for minute in range(1, 121):
        j = minute * 4
        item = {"minute": minute, "fine_complete5": False,
                "pre5m_range_bp": np.nan, "M1": np.nan, "M2": np.nan,
                "A5": np.nan, "rms1m5": np.nan}
        if minute >= 5:
            fine = r15[j-19:j+1]
            prices = price[j-20:j+1]
            coarse = r1[minute-5:minute]
            complete = (len(fine) == 20 and len(prices) == 21 and
                        np.isfinite(fine).all() and np.isfinite(prices).all() and
                        (prices > 0).all())
            item["fine_complete5"] = bool(complete)
            if complete:
                logrel = np.log(prices / prices[0]) * 1e4
                item["pre5m_range_bp"] = float(logrel.max() - logrel.min())
                rv_fine = float(np.sum(fine * fine))
                if np.isfinite(coarse).all():
                    rv_coarse = float(np.sum(coarse * coarse))
                    item["M1"] = float(np.log((rv_fine + EPS_RV) / (rv_coarse + EPS_RV)))
                    item["rms1m5"] = float(np.sqrt(np.mean(coarse * coarse)))
                motion = np.abs(fine)
                total = float(motion.sum())
                if total > 0:
                    share = motion / total
                    item["M2"] = float(len(motion) * np.sum(share * share))
                item["A5"] = float(np.sqrt(np.mean(fine * fine)))
        rows.append(item)
    return pd.DataFrame(rows)


def attach_activity_surprise(frame: pd.DataFrame, min_history: int = 60) -> pd.DataFrame:
    """Attach causal same-index/same-half-session-clock M3 and fixed M4.

    Each row's reference uses *strictly earlier* rows in the same
    ``(symbol, afternoon, minute)`` bucket. No current or future observation is
    included. Median/MAD are robust but intentionally not optimized.
    """
    need = {"symbol", "day", "year", "afternoon", "minute", "A5", "M1"}
    if not need <= set(frame):
        raise StudyError(f"missing columns: {sorted(need-set(frame))}")
    out = frame.copy()
    out["M3"] = np.nan
    order = pd.to_datetime(out["day"], errors="raise")
    out["_date_order"] = order
    for _, ix in out.groupby(["symbol", "afternoon", "minute"], sort=False).groups.items():
        idx = list(ix)
        idx.sort(key=lambda i: (out.at[i, "_date_order"], i))
        prior: list[float] = []
        for i in idx:
            a5 = float(out.at[i, "A5"]) if pd.notna(out.at[i, "A5"]) else np.nan
            if np.isfinite(a5) and a5 > 0 and len(prior) >= min_history:
                values = np.asarray(prior, float)
                med = float(np.median(values))
                mad = float(np.median(np.abs(values-med)))
                scale = max(1.4826 * mad, 1e-8)
                out.at[i, "M3"] = (np.log(a5)-med) / scale
            if np.isfinite(a5) and a5 > 0:
                prior.append(float(np.log(a5)))
    out["M4"] = out["M3"] + out["M1"]
    return out.drop(columns="_date_order")


def freeze_thresholds(frame: pd.DataFrame, range_bp: float = PRIMARY_RANGE_BP) -> pd.DataFrame:
    """Freeze 2023 80th-percentile thresholds using admissible low-range rows."""
    need = {"symbol", "year", "decision_ok", "fine_complete5", "pre5m_range_bp", *MEASURES}
    if not need <= set(frame):
        raise StudyError(f"threshold frame missing: {sorted(need-set(frame))}")
    rows = []
    for symbol, q in frame.groupby("symbol", sort=True):
        cal = q[(q.year == CALIBRATION_YEAR) & q.decision_ok & q.fine_complete5 &
                (q.pre5m_range_bp < range_bp)]
        for measure in MEASURES:
            values = pd.to_numeric(cal[measure], errors="coerce")
            values = values[np.isfinite(values)]
            if len(values) < 100:
                raise StudyError(f"insufficient 2023 calibration for {symbol}/{measure}: {len(values)}")
            rows.append({"symbol": symbol, "measure": measure, "year": CALIBRATION_YEAR,
                         "quantile": 0.8, "threshold": float(np.quantile(values, .8)),
                         "calibration_n": int(len(values)), "range_bp": float(range_bp)})
    return pd.DataFrame(rows)


def apply_threshold(frame: pd.DataFrame, thresholds: pd.DataFrame, measure: str,
                    range_bp: float = PRIMARY_RANGE_BP) -> pd.DataFrame:
    if measure not in MEASURES and measure != "C1":
        raise StudyError(f"unregistered measure {measure}")
    out = frame.copy()
    out["low_amplitude"] = out.fine_complete5 & (out.pre5m_range_bp < range_bp)
    out["analysis_ok"] = out.decision_ok & out.low_amplitude & np.isfinite(out[measure])
    out["alarm"] = False
    for symbol, q in out.groupby("symbol", sort=False):
        row = thresholds[(thresholds.symbol == symbol) & (thresholds.measure == measure)]
        if len(row) != 1:
            raise StudyError(f"need one frozen threshold for {symbol}/{measure}")
        t = float(row.iloc[0].threshold)
        ix = q.index[q.analysis_ok]
        out.loc[ix, "alarm"] = out.loc[ix, measure] >= t
    return out


def decision_metrics(q: pd.DataFrame) -> dict:
    """Risk among strictly labelled actionable rows, not event recall."""
    known = q.analysis_ok & np.isfinite(q.target)
    high = known & q.alarm
    low = known & ~q.alarm
    yh = pd.to_numeric(q.loc[high, "target"], errors="coerce").to_numpy(float)
    yl = pd.to_numeric(q.loc[low, "target"], errors="coerce").to_numpy(float)
    rh = float(yh.mean()) if len(yh) else np.nan
    rl = float(yl.mean()) if len(yl) else np.nan
    return {"known_decisions": int(known.sum()), "high_n": int(high.sum()), "low_n": int(low.sum()),
            "events_in_high_windows": int(np.nansum(yh)), "events_in_low_windows": int(np.nansum(yl)),
            "risk_high": rh, "risk_low": rl,
            "risk_difference": rh-rl if np.isfinite(rh) and np.isfinite(rl) else np.nan,
            "risk_ratio": rh/rl if np.isfinite(rh) and np.isfinite(rl) and rl > 0 else None,
            "alarm_coverage": float(q.loc[q.analysis_ok, "alarm"].mean()) if q.analysis_ok.any() else np.nan}


def event_metrics(q: pd.DataFrame) -> dict:
    """Unique first-event recall with the frozen t=e-15..e-2 strict-lead window."""
    hits = []
    opportunities = []
    leads = []
    for _, ix in q.groupby("session", sort=False).groups.items():
        part = q.loc[ix].sort_values("minute", kind="stable")
        events = part[part["first"] == 1]
        for _, ev in events.iterrows():
            e = int(ev.minute)
            if e < 33:
                continue
            w = part[part.minute.between(max(31, e-15), e-2)]
            eligible = w.analysis_ok
            alarm = eligible & w.alarm
            opportunities.append(bool(eligible.any()))
            hit = bool(alarm.any())
            hits.append(hit)
            if hit:
                alarm_minutes = w.loc[alarm, "minute"].to_numpy(int)
                leads.append(int(e - alarm_minutes.min()))
    # Merge consecutive alarm minutes into segments, session by session.
    segments = 0
    for _, part in q.groupby("session", sort=False):
        a = (part.analysis_ok & part.alarm).to_numpy(bool)
        segments += int(np.sum(a & ~np.r_[False, a[:-1]]))
    return {"unique_first_events": int(len(hits)), "unique_first_events_hit": int(sum(hits)),
            "unique_event_recall": float(np.mean(hits)) if hits else np.nan,
            "events_with_low_amp_opportunity": int(sum(opportunities)),
            "alarm_segments": int(segments), "earliest_lead_minutes": leads,
            "median_earliest_lead_minutes": float(np.median(leads)) if leads else None}


def _daily_counts(q: pd.DataFrame) -> pd.DataFrame:
    known = q.analysis_ok & np.isfinite(q.target)
    rows = []
    for day, z in q.loc[known].groupby("day", sort=True):
        high = z.alarm.to_numpy(bool)
        y = z.target.to_numpy(float)
        rows.append({"day": day, "yh": float(y[high].sum()), "nh": int(high.sum()),
                     "yl": float(y[~high].sum()), "nl": int((~high).sum())})
    return pd.DataFrame(rows)


def moving_block_bootstrap(q: pd.DataFrame, repeats: int = 2000, block_days: int = 5,
                           seed: int = SEED) -> dict:
    daily = _daily_counts(q)
    if len(daily) < block_days:
        return {"status": "insufficient_days", "repeats": 0, "ci": [None, None], "p_two_sided": None}
    arr = daily[["yh", "nh", "yl", "nl"]].to_numpy(float)
    starts = np.arange(0, len(arr)-block_days+1)
    rng = np.random.default_rng(seed)
    values = []
    target_blocks = int(np.ceil(len(arr)/block_days))
    for _ in range(repeats):
        chosen = rng.choice(starts, size=target_blocks, replace=True)
        sample = np.concatenate([arr[s:s+block_days] for s in chosen], axis=0)[:len(arr)]
        yh, nh, yl, nl = sample.sum(axis=0)
        if nh > 0 and nl > 0:
            values.append(yh/nh - yl/nl)
    if not values:
        return {"status": "degenerate", "repeats": 0, "ci": [None, None], "p_two_sided": None}
    v = np.asarray(values, float)
    p = min(1.0, 2*min(float(np.mean(v <= 0)), float(np.mean(v >= 0))))
    return {"status": "ok", "repeats": int(len(v)),
            "ci": [float(np.quantile(v,.025)), float(np.quantile(v,.975))],
            "p_two_sided": p}


def holm_adjust(p_values: list[float | None]) -> list[float | None]:
    valid = [(i, float(p)) for i,p in enumerate(p_values) if p is not None and np.isfinite(p)]
    out: list[float | None] = [None] * len(p_values)
    if not valid:
        return out
    ordered = sorted(valid, key=lambda x: x[1])
    m = len(ordered); running = 0.0
    for rank, (i,p) in enumerate(ordered):
        adj = min(1.0, (m-rank)*p)
        running = max(running, adj)
        out[i] = running
    return out
