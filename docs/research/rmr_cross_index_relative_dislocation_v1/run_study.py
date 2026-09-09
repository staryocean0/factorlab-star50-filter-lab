#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOL_A = "000688.SH"
SYMBOL_B = "000852.SH"
YEARS = (2021, 2022, 2023)
BG = 60
RECENT = 5
HORIZON = 15


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def band(z: float) -> str | None:
    if not np.isfinite(z):
        return None
    if z <= 1.0:
        return "low"
    if z <= 2.0:
        return "mid"
    return "high"


def make_panel(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    q = frame[frame.symbol == symbol].copy()
    local = q.market_time_shanghai.dt.tz_localize(None)
    q["afternoon"] = (local.dt.hour >= 13).astype(int)
    q["day"] = q.trading_day.astype(str)
    q["session"] = q.day + "/" + q.afternoon.astype(str)
    q = q.sort_values("market_time_shanghai", kind="stable").reset_index(drop=True)
    q["minute"] = q.groupby("session", sort=False).cumcount() + 1
    counts = q.groupby("session").size()
    q = q[q.session.isin(set(counts[counts == 120].index))].copy().reset_index(drop=True)
    q["eligible"] = q.get("high_frequency_analysis_eligible", True)
    q["eligible"] = q.eligible.fillna(False).astype(bool)
    q["return_bp"] = np.nan
    for _, ix in q.groupby("session", sort=False).groups.items():
        idx = np.asarray(list(ix))
        close = q.loc[idx, "close"].to_numpy(float)
        q.loc[idx, "return_bp"] = np.r_[np.nan, np.diff(np.log(close)) * 1e4]
    return q[["market_time_shanghai", "day", "session", "minute", "eligible", "return_bp"]]


def ols_alpha_beta(x: np.ndarray, y: np.ndarray) -> tuple[float, float, np.ndarray]:
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if len(x) != len(y) or len(x) < 3 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("bad OLS inputs")
    xm = float(x.mean())
    ym = float(y.mean())
    vx = float(np.mean((x - xm) ** 2))
    if vx <= 1e-12:
        raise ValueError("degenerate regressor")
    beta = float(np.mean((x - xm) * (y - ym)) / vx)
    alpha = ym - beta * xm
    resid = y - (alpha + beta * x)
    return alpha, beta, resid


def study_rows(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    q = a.merge(b, on=["market_time_shanghai", "day", "session", "minute"], suffixes=("_a", "_b"), validate="one_to_one")
    rows = []
    for session, part in q.groupby("session", sort=False):
        z = part.sort_values("minute", kind="stable").reset_index(drop=True)
        if len(z) != 120:
            continue
        ra = z.return_bp_a.to_numpy(float)
        rb = z.return_bp_b.to_numpy(float)
        ea = z.eligible_a.to_numpy(bool)
        eb = z.eligible_b.to_numpy(bool)
        # t is zero-based decision index. Need 60 background returns, then 5 recent,
        # then 15 future rows, all inside the same half-session.
        for t in range(BG + RECENT, 120 - HORIZON):
            bg_lo = t - RECENT - BG + 1
            bg_hi = t - RECENT + 1
            recent_lo = t - RECENT + 1
            recent_hi = t + 1
            fut_lo = t + 1
            fut_hi = t + 1 + HORIZON
            idx_all = np.r_[np.arange(bg_lo, bg_hi), np.arange(recent_lo, recent_hi), np.arange(fut_lo, fut_hi)]
            if not (ea[idx_all].all() and eb[idx_all].all()):
                continue
            xa = rb[bg_lo:bg_hi]
            ya = ra[bg_lo:bg_hi]
            recent_a = ra[recent_lo:recent_hi]
            recent_b = rb[recent_lo:recent_hi]
            fut_a = ra[fut_lo:fut_hi]
            fut_b = rb[fut_lo:fut_hi]
            if not all(np.isfinite(v).all() for v in (xa, ya, recent_a, recent_b, fut_a, fut_b)):
                continue
            try:
                alpha, beta, resid_bg = ols_alpha_beta(xa, ya)
            except ValueError:
                continue
            sd = float(np.std(resid_bg, ddof=1))
            if not np.isfinite(sd) or sd <= 1e-8:
                continue
            d5 = float(np.sum(recent_a - (alpha + beta * recent_b)))
            if abs(d5) <= 1e-12:
                continue
            f15 = float(np.sum(fut_a - (alpha + beta * fut_b)))
            signed = float(np.sign(d5) * f15)
            sev = abs(d5) / (sd * np.sqrt(RECENT))
            rows.append({
                "day": z.loc[t, "day"],
                "session": session,
                "minute": int(z.loc[t, "minute"]),
                "year": int(str(z.loc[t, "day"])[:4]),
                "alpha": alpha,
                "beta": beta,
                "background_resid_sd_bp": sd,
                "D5_bp": d5,
                "Z": sev,
                "band": band(sev),
                "direction": "STAR50_rich" if d5 > 0 else "STAR50_cheap",
                "F15_bp": f15,
                "signed_F15_bp": signed,
                "recovery50": bool(signed <= -0.5 * abs(d5)),
            })
    return pd.DataFrame(rows)


def summarize(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    annual = []
    for year in YEARS:
        for b in ("low", "mid", "high"):
            z = rows[(rows.year == year) & (rows.band == b)]
            annual.append({
                "year": year,
                "band": b,
                "n": int(len(z)),
                "median_signed_F15_bp": float(z.signed_F15_bp.median()) if len(z) else None,
                "mean_signed_F15_bp": float(z.signed_F15_bp.mean()) if len(z) else None,
                "recovery50_prob": float(z.recovery50.mean()) if len(z) else None,
            })
    annual_df = pd.DataFrame(annual)

    pooled = []
    for direction in ("ALL", "STAR50_rich", "STAR50_cheap"):
        d = rows if direction == "ALL" else rows[rows.direction == direction]
        for b in ("low", "mid", "high"):
            z = d[d.band == b]
            pooled.append({
                "direction": direction,
                "band": b,
                "n": int(len(z)),
                "median_signed_F15_bp": float(z.signed_F15_bp.median()) if len(z) else None,
                "mean_signed_F15_bp": float(z.signed_F15_bp.mean()) if len(z) else None,
                "recovery50_prob": float(z.recovery50.mean()) if len(z) else None,
            })
    pooled_df = pd.DataFrame(pooled)

    high_annual = annual_df[annual_df.band == "high"].set_index("year")
    allp = pooled_df[pooled_df.direction == "ALL"].set_index("band")
    rich = pooled_df[(pooled_df.direction == "STAR50_rich") & (pooled_df.band == "high")].iloc[0]
    cheap = pooled_df[(pooled_df.direction == "STAR50_cheap") & (pooled_df.band == "high")].iloc[0]
    checks = {
        "high_n_ge_100_each_year": bool((high_annual.n >= 100).all()),
        "high_median_reverts_each_year": bool((high_annual.median_signed_F15_bp < 0).all()),
        "pooled_high_recovery_advantage_ge_5pp": bool(allp.loc["high", "recovery50_prob"] - allp.loc["low", "recovery50_prob"] >= 0.05),
        "high_rich_median_reverts": bool(rich.median_signed_F15_bp < 0),
        "high_cheap_median_reverts": bool(cheap.median_signed_F15_bp < 0),
        "high_rich_n_ge_100": bool(rich.n >= 100),
        "high_cheap_n_ge_100": bool(cheap.n >= 100),
    }
    verdict = "broad_signal_source_supported" if all(checks.values()) else "broad_signal_source_not_established"
    return annual_df, pooled_df, {"verdict": verdict, "checks": checks}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.repo_root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)

    sys.path.insert(0, str(root / "src"))
    from star50_filter.cloud_market_data import load_market_data

    fa = load_market_data(SYMBOL_A, "1m", "2021-01-01", "2023-12-31", root=root)
    fb = load_market_data(SYMBOL_B, "1m", "2021-01-01", "2023-12-31", root=root)
    a = make_panel(fa, SYMBOL_A)
    b = make_panel(fb, SYMBOL_B)
    rows = study_rows(a, b)
    if set(rows.year.unique()) - set(YEARS):
        raise RuntimeError("non-Development row reached study")
    annual, pooled, decision = summarize(rows)
    rows.to_csv(out / "decision_rows.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    annual.to_csv(out / "annual_summary.csv", index=False)
    pooled.to_csv(out / "pooled_summary.csv", index=False)
    summary = {
        "schema": "rmr_cross_index_relative_dislocation_v1",
        "development_years": list(YEARS),
        "rows": int(len(rows)),
        "decision": decision,
        "validation_queried": False,
        "blackbox_queried": False,
        "returns_or_pnl_evaluated": False,
        "candidate_nominated": bool(decision["verdict"] == "broad_signal_source_supported"),
        "production_authority": False,
        "git_sha": os.getenv("GITHUB_SHA"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
    }
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(annual.to_string(index=False))
    print(pooled.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
