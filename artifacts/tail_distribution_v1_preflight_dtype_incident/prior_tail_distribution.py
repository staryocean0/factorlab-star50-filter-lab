"""Matched-clock tail diagnostics. No trading decisions or parameter search."""

import numpy as np
import pandas as pd


def prepare_instrument(frame, minutes):
    f = frame.sort_values("timestamp").reset_index(drop=True).copy()
    ts = pd.to_datetime(f.timestamp.astype(str).str[:19]).dt.tz_localize("Asia/Shanghai")
    if ts.duplicated().any():
        raise ValueError("duplicate timestamps")
    prices = f[["open", "high", "low", "close"]].to_numpy(float)
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise ValueError("invalid prices")
    if ((f.high < f[["open", "close"]].max(axis=1)) | (f.low > f[["open", "close"]].min(axis=1))).any():
        raise ValueError("OHLC contradiction")
    f["timestamp"] = ts
    f["day"] = ts.dt.strftime("%Y-%m-%d")
    f["year"] = ts.dt.year
    f["session"] = (ts.dt.hour >= 13).astype(int)
    f["clock"] = ts.dt.strftime("%H:%M")
    first = (f.day != f.day.shift()) | (f.session != f.session.shift())
    adjacent = ts.diff() == pd.Timedelta(minutes=minutes)
    if ((~first) & (~adjacent)).any():
        raise ValueError("non-boundary clock gap")
    x = np.log(f.close.to_numpy(float))
    r = pd.Series(x).diff()
    f["return_all"] = r
    f["r"] = r.where(~first)
    f["boundary"] = first
    f["body"] = np.log(f.close / f.open)
    f["gap"] = np.log(f.open / f.close.shift())
    n = 480 // minutes
    minimum = int(np.ceil(0.9 * n))
    f["sigma_prior"] = f.r.rolling(n, min_periods=minimum).std(ddof=1).shift(1)
    f["robust_sigma_prior"] = f.r.abs().rolling(n, min_periods=minimum).median().shift(1) / 0.6744897501960817
    f["z"] = f.r / f.sigma_prior.where(f.sigma_prior > 1e-12)
    f["robust_z"] = f.r / f.robust_sigma_prior.where(f.robust_sigma_prior > 1e-12)
    f["prediction_time"] = ts.shift()
    f["frequency_minutes"] = minutes
    return f


def calibrate(frames):
    train = pd.concat([f[(f.year >= 2021) & (f.year <= 2023) & ~f.boundary] for f in frames])
    cuts = {
        basis: float(train[column].abs().quantile(0.995)) for basis, column in [("raw", "r"), ("standardized", "z"), ("robust", "robust_z")]
    }
    bins = {symbol: g.sigma_prior.quantile([1 / 3, 2 / 3]).to_list() for symbol, g in train.groupby("symbol")}
    return {
        "tail_cutoffs": cuts,
        "volatility_terciles": bins,
        "calibration_rows": len(train),
        "calibration_min_day": train.day.min(),
        "calibration_max_day": train.day.max(),
    }


def previous_any(events, bars):
    y = np.asarray(events, dtype=bool)
    if y.ndim != 3 or bars < 1:
        raise ValueError("day/session/bar matrix and positive lag required")
    result = np.zeros_like(y)
    for lag in range(1, min(bars, y.shape[-1]) + 1):
        result[:, :, lag:] |= y[:, :, :-lag]
    return result


def tail_statistics(y, vol, lookback):
    previous = previous_any(y, lookback)
    total = int(y.sum())
    prior_count = int(previous.sum())
    after = float(y[previous].mean()) if prior_count else 0.0
    ordinary = float(y[~previous].mean()) if (~previous).any() else 0.0
    hi = float(y[vol == 2].mean()) if (vol == 2).any() else 0.0
    lo = float(y[vol == 0].mean()) if (vol == 0).any() else 0.0
    day_counts = y.sum(axis=(1, 2))
    fano = float(day_counts.var(ddof=1) / day_counts.mean()) if total else 0.0
    first = y & ~previous
    return {
        "events": total,
        "rate": float(y.mean()),
        "daily_fano": fano,
        "after5_rate": after,
        "no_recent_rate": ordinary,
        "serial_risk_difference": after - ordinary,
        "high_vol_rate": hi,
        "low_vol_rate": lo,
        "vol_risk_difference": hi - lo,
        "high_vol_time_share": float((vol == 2).mean()),
        "high_vol_capture": float(y[vol == 2].sum() / total) if total else 0.0,
        "high_vol_first_capture": float((first & (vol == 2)).sum() / first.sum()) if first.any() else 0.0,
        "first_events": int(first.sum()),
        "subsequent_events": int((y & previous).sum()),
        "top_1pct_days_share": float(np.sort(day_counts)[-max(1, int(np.ceil(len(day_counts) * 0.01))) :].sum() / total) if total else 0.0,
    }


def permute_same_year_clock(events, years, rng):
    out = np.empty_like(events)
    for year in np.unique(years):
        ix = np.flatnonzero(years == year)
        out[ix] = rng.permuted(events[ix], axis=0)
    return out


def clustering_tests(events, vol, years, lookback, seed=20260907, repeats=999):
    observed = tail_statistics(events, vol, lookback)
    names = ["daily_fano", "serial_risk_difference", "vol_risk_difference"]
    null = np.empty((repeats, 3))
    rng = np.random.default_rng(seed)
    for i in range(repeats):
        p = permute_same_year_clock(events, years, rng)
        s = tail_statistics(p, vol, lookback)
        null[i] = [s[name] for name in names]
    rows = []
    for j, name in enumerate(names):
        upper = (1 + (null[:, j] >= observed[name]).sum()) / (repeats + 1)
        lower = (1 + (null[:, j] <= observed[name]).sum()) / (repeats + 1)
        pv = min(1.0, 2 * min(upper, lower)) if name == "vol_risk_difference" else upper
        rows.append(
            {
                "test": name,
                "observed": observed[name],
                "null_median": float(np.median(null[:, j])),
                "p_raw": float(pv),
                "permutations": repeats,
            }
        )
    return rows, null


def holm(pvalues):
    p = np.asarray(pvalues, float)
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("invalid p values")
    order = np.argsort(p, kind="stable")
    ranked = p[order] * (len(p) - np.arange(len(p)))
    adjusted = np.minimum(1.0, np.maximum.accumulate(ranked))
    out = np.empty_like(p)
    out[order] = adjusted
    return out


def cluster_episodes(y, minutes):
    rows = []
    max_gap = 5 // minutes
    for d in range(y.shape[0]):
        for session in range(2):
            events = np.flatnonzero(y[d, session])
            if len(events) == 0:
                continue
            splits = np.split(events, np.flatnonzero(np.diff(events) > max_gap) + 1)
            for group in splits:
                rows.append(
                    {
                        "day_index": d,
                        "session": session,
                        "start_bar": int(group[0]),
                        "end_bar": int(group[-1]),
                        "events": len(group),
                        "span_minutes": int((group[-1] - group[0]) * minutes),
                    }
                )
    return pd.DataFrame(rows)


def probability_scores(train, test):
    """Frozen six-cell and clock-only risk forecasts; predictions precede target bars."""
    global_p = (train.event.sum() + 0.5) / (len(train) + 1)
    cells = train.groupby(["vol_bin", "prior5"]).event.agg(["sum", "size"])
    lookup = {(int(v), bool(p)): (row["sum"] + 0.5) / (row["size"] + 1) for (v, p), row in cells.iterrows()}
    clocks = train.groupby("clock").event.agg(["sum", "size"])
    clock_map = ((clocks["sum"] + 0.5) / (clocks["size"] + 1)).to_dict()
    pred = np.array([lookup.get((int(v), bool(p)), global_p) for v, p in zip(test.vol_bin, test.prior5, strict=True)])
    clock = test.clock.map(clock_map).fillna(global_p).to_numpy()
    outcomes = test.event.to_numpy(float)
    rows = []
    for name, prob in [("constant", np.full(len(test), global_p)), ("clock_only", clock), ("volatility_and_recent_tail", pred)]:
        q = np.clip(prob, 1e-12, 1 - 1e-12)
        rows.append(
            {
                "forecast": name,
                "event_rate": outcomes.mean(),
                "mean_prediction": prob.mean(),
                "brier": float(np.mean((prob - outcomes) ** 2)),
                "log_loss": float(-np.mean(outcomes * np.log(q) + (1 - outcomes) * np.log1p(-q))),
            }
        )
    return rows, pred
