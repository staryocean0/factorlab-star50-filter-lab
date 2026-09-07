"""Causal price-grid diagnostics; does not construct OHLC or trading signals."""

import numpy as np
import pandas as pd


def observed_grid(times, prices, valid_until, grid, max_age_seconds=3):
    """As-of observed state, only within its true validity and age limit."""
    t = np.asarray(times, dtype=np.int64)
    p = np.asarray(prices, dtype=float)
    until = np.asarray(valid_until, dtype=np.int64)
    g = np.asarray(grid, dtype=np.int64)
    if len(t) != len(p) or len(t) != len(until) or np.any(np.diff(t) <= 0):
        raise ValueError("state times must be unique and increasing")
    out = np.full(len(g), np.nan)
    age = np.full(len(g), np.nan)
    if len(t) == 0:
        return out, age
    j = np.searchsorted(t, g, side="right") - 1
    safe = np.maximum(j, 0)
    elapsed = (g - t[safe]) / 1e9
    ok = (j >= 0) & (elapsed >= 0) & (elapsed <= max_age_seconds) & (g < until[safe]) & np.isfinite(p[safe]) & (p[safe] > 0)
    out[ok] = p[safe[ok]]
    age[ok] = elapsed[ok]
    return out, age


def efficiency(prices, steps):
    """Trailing efficiency requires every underlying observed increment."""
    if type(steps) is not int or steps < 1:
        raise ValueError("positive integer steps")
    p = pd.Series(np.asarray(prices, float))
    if ((p <= 0) & p.notna()).any():
        raise ValueError("positive prices required")
    x = np.log(p)
    r = x.diff()
    road = r.abs().rolling(steps, min_periods=steps).sum()
    net = x.diff(steps)
    er = net.abs() / road.where(road > 0)
    top = r.abs().rolling(steps, min_periods=steps).max() / road.where(road > 0)
    zero = (r == 0).astype(float).where(r.notna()).rolling(steps, min_periods=steps).mean()
    return pd.DataFrame({"er": er, "road": road, "net": net, "top1": top, "zero_share": zero})


def session_measurements(times, price_sets, until, start_ns, day, symbol, phase):
    records = []
    quality = []
    for field, prices in price_sets.items():
        for delta in [3, 15, 30, 60, 300]:
            grid = start_ns + np.arange(0, 7200 + 1, delta, dtype=np.int64) * 10**9
            p, age = observed_grid(times, prices, until, grid)
            quality.append(
                {
                    "day": day,
                    "symbol": symbol,
                    "session": phase,
                    "field": field,
                    "delta": delta,
                    "grid_points": len(p),
                    "valid_points": int(np.isfinite(p).sum()),
                    "mean_age_seconds": float(np.nanmean(age)) if np.isfinite(age).any() else None,
                }
            )
            for horizon in [15, 30, 60]:
                n = horizon * 60 // delta
                f = efficiency(p, n)
                # All resolutions report the SAME five-minute clock, not different sample counts.
                ix = np.arange(0, len(p), 300 // delta)
                shared = f.iloc[ix].reset_index(drop=True)
                shared["var60"] = shared.er.rolling(12, min_periods=12).var(ddof=1)
                shared["step5"] = shared.er.diff().abs()
                for j, row in shared.iterrows():
                    if not np.isfinite(row.er):
                        continue
                    records.append(
                        {
                            "day": day,
                            "year": int(day[:4]),
                            "symbol": symbol,
                            "session": phase,
                            "minute": int(j * 5),
                            "field": field,
                            "delta": delta,
                            "horizon": horizon,
                            "steps": n,
                            **row.to_dict(),
                            "nonoverlap": bool((j * 5) % horizon == 0),
                        }
                    )
    return records, quality


def common_support(frame):
    keys = ["day", "symbol", "session", "minute", "field", "horizon"]
    count = frame.groupby(keys).delta.transform("nunique")
    return frame[count == 5].copy()
