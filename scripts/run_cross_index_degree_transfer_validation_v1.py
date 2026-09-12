#!/usr/bin/env python3
"""Execution-only compatibility entrypoint for cross-index degree V1.

The frozen scientific runner is unchanged. Its descriptive output used ``g.tail``
for a DataFrame column named ``tail``; pandas resolves that expression to the
DataFrame.tail method. This wrapper replaces only that descriptive helper with
an equivalent bracket-access implementation and delegates all fitting, scoring,
gates, model identity checks, and CLI handling to the frozen runner.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.cross_index_degree_transfer_utility_v1 import run_study as study


def descriptive_outputs(q: pd.DataFrame, probes: dict, h: int, out):
    corr_cols = [
        "shock_intensity", "vol_ratio", "other_shock_intensity", "other_vol_ratio",
        "other_lag_intensity", "other_lag_ratio",
    ]
    corr = q[corr_cols].corr().to_dict()
    ages = {}
    for name in ("observation_age_seconds", "other_observation_age_seconds"):
        s = q[name].dropna().to_numpy(float)
        ages[name] = {
            "n": int(len(s)), "median": float(study.np.median(s)),
            "p95": float(study.np.quantile(s, .95)), "max": float(study.np.max(s)),
        } if len(s) else {"n": 0}
    slice_rows = []
    decile_rows = []
    for endpoint in study.ENDPOINTS:
        pc = study.predict(q, "C", probes[f"{h}|{endpoint}|C"], endpoint)
        px = study.predict(q, "X", probes[f"{h}|{endpoint}|X"], endpoint)
        pl = study.predict(q, "L", probes[f"{h}|{endpoint}|L"], endpoint)
        y = q[endpoint].to_numpy(float)
        for b, pb in (("C", pc), ("L", pl)):
            gain = (y-pb)**2 - (y-px)**2
            for col in ("symbol", "year", "previous_state", "slot"):
                for key, inds in q.groupby(col, sort=True).indices.items():
                    slice_rows.append({
                        "horizon": h, "endpoint": endpoint, "comparison": f"X_vs_{b}",
                        "slice_type": col, "slice": str(key), "n": int(len(inds)),
                        "absolute_gain": float(gain[inds].mean()),
                    })
        increment = px - pc
        dec = pd.qcut(pd.Series(increment), 10, labels=False, duplicates="drop")
        tmp = pd.DataFrame({
            "decile": dec, "sigma": q.sigma.to_numpy(float),
            "tail": q.future_tail.to_numpy(float), "increment": increment,
        })
        for d, g in tmp.groupby("decile", dropna=False, sort=True):
            decile_rows.append({
                "horizon": h, "endpoint": endpoint,
                "increment_decile": None if pd.isna(d) else int(d),
                "n": int(len(g)), "increment_mean": float(g["increment"].mean()),
                "sigma_mean": float(g["sigma"].mean()),
                "tail_rate": float(g["tail"].mean()),
            })
    pd.DataFrame(slice_rows).to_csv(out / f"slice_gains_{h}.csv", index=False)
    pd.DataFrame(decile_rows).to_csv(out / f"increment_deciles_{h}.csv", index=False)
    return {"correlations": corr, "observation_age": ages, "n": int(len(q))}


study.descriptive_outputs = descriptive_outputs

if __name__ == "__main__":
    raise SystemExit(study.main())
