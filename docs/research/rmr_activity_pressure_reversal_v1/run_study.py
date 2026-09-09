#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
YEARS = (2021, 2022, 2023)
BG = 30
RECENT = 5
PRIMARY_H = 5
SECONDARY_H = 15
SEV_TRIGGER = 2.0
SEV_EXTREME = 3.0
ACTIVITY_TRIGGER = 1.5


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    return q[["day", "session", "minute", "eligible", "return_bp", "amount"]]


def build_events(panel: pd.DataFrame, symbol: str) -> pd.DataFrame:
    rows = []
    for session, part in panel.groupby("session", sort=False):
        z = part.sort_values("minute", kind="stable").reset_index(drop=True)
        if len(z) != 120:
            continue
        r = z.return_bp.to_numpy(float)
        amount = pd.to_numeric(z.amount, errors="coerce").to_numpy(float)
        elig = z.eligible.to_numpy(bool)
        sev = np.full(120, np.nan)
        act = np.full(120, np.nan)
        recent_net = np.full(120, np.nan)
        first_decision = BG + RECENT - 1
        for t in range(first_decision, 120 - SECONDARY_H):
            bg_lo = t - RECENT - BG + 1
            bg_hi = t - RECENT + 1
            rec_lo = t - RECENT + 1
            rec_hi = t + 1
            idx = np.r_[np.arange(bg_lo, bg_hi), np.arange(rec_lo, rec_hi)]
            if not elig[idx].all():
                continue
            bg = r[bg_lo:bg_hi]
            rec = r[rec_lo:rec_hi]
            abg = amount[bg_lo:bg_hi]
            arec = amount[rec_lo:rec_hi]
            if not (np.isfinite(bg).all() and np.isfinite(rec).all() and np.isfinite(abg).all() and np.isfinite(arec).all()):
                continue
            if (abg <= 0).any() or (arec <= 0).any():
                continue
            sigma = max(float(np.sqrt(np.mean(bg * bg))), 1.0)
            recent_net[t] = float(rec.sum())
            sev[t] = abs(recent_net[t]) / (sigma * np.sqrt(RECENT))
            act[t] = float(arec.mean() / abg.mean())

        for t in range(first_decision + 1, 120 - SECONDARY_H):
            if not (np.isfinite(sev[t]) and np.isfinite(sev[t-1])):
                continue
            if not (sev[t] >= SEV_TRIGGER and sev[t-1] < SEV_TRIGGER):
                continue
            fut5 = r[t+1:t+1+PRIMARY_H]
            fut15 = r[t+1:t+1+SECONDARY_H]
            efut = elig[t+1:t+1+SECONDARY_H]
            if not (np.isfinite(fut5).all() and np.isfinite(fut15).all() and efut.all()):
                continue
            sign = float(np.sign(recent_net[t]))
            if sign == 0:
                continue
            signed5 = sign * float(fut5.sum())
            signed15 = sign * float(fut15.sum())
            rows.append({
                "symbol": symbol,
                "day": z.loc[t, "day"],
                "session": session,
                "minute": int(z.loc[t, "minute"]),
                "year": int(str(z.loc[t, "day"])[:4]),
                "R5_bp": float(recent_net[t]),
                "direction": "UP" if recent_net[t] > 0 else "DOWN",
                "severity": float(sev[t]),
                "severity_view": "extreme" if sev[t] >= SEV_EXTREME else "moderate",
                "activity_ratio": float(act[t]),
                "activity_state": "ElevatedActivity" if act[t] >= ACTIVITY_TRIGGER else "NormalActivity",
                "signed_F5_bp": signed5,
                "signed_F15_bp": signed15,
                "reversal5": bool(signed5 < 0),
            })
    return pd.DataFrame(rows)


def summarize(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    annual_rows = []
    view_rows = []
    per_symbol = {}
    for symbol in SYMBOLS:
        s = events[events.symbol == symbol]
        for year in YEARS:
            for state in ("ElevatedActivity", "NormalActivity"):
                z = s[(s.year == year) & (s.activity_state == state)]
                annual_rows.append({
                    "symbol": symbol, "year": year, "activity_state": state,
                    "n": int(len(z)),
                    "median_signed_F5_bp": float(z.signed_F5_bp.median()) if len(z) else None,
                    "mean_signed_F5_bp": float(z.signed_F5_bp.mean()) if len(z) else None,
                    "reversal5_prob": float(z.reversal5.mean()) if len(z) else None,
                    "median_signed_F15_bp": float(z.signed_F15_bp.median()) if len(z) else None,
                })
        for severity_view in ("moderate", "extreme"):
            for state in ("ElevatedActivity", "NormalActivity"):
                z = s[(s.severity_view == severity_view) & (s.activity_state == state)]
                view_rows.append({
                    "symbol": symbol, "severity_view": severity_view, "activity_state": state,
                    "n": int(len(z)),
                    "median_signed_F5_bp": float(z.signed_F5_bp.median()) if len(z) else None,
                    "reversal5_prob": float(z.reversal5.mean()) if len(z) else None,
                    "median_severity": float(z.severity.median()) if len(z) else None,
                })
        for direction in ("UP", "DOWN"):
            for state in ("ElevatedActivity", "NormalActivity"):
                z = s[(s.direction == direction) & (s.activity_state == state)]
                view_rows.append({
                    "symbol": symbol, "severity_view": direction, "activity_state": state,
                    "n": int(len(z)),
                    "median_signed_F5_bp": float(z.signed_F5_bp.median()) if len(z) else None,
                    "reversal5_prob": float(z.reversal5.mean()) if len(z) else None,
                    "median_severity": float(z.severity.median()) if len(z) else None,
                })

        a = pd.DataFrame(annual_rows)
        ay = a[(a.symbol == symbol) & (a.activity_state == "ElevatedActivity")].set_index("year")
        v = pd.DataFrame(view_rows)
        vv = v[v.symbol == symbol]
        elev = s[s.activity_state == "ElevatedActivity"]
        norm = s[s.activity_state == "NormalActivity"]
        checks = {
            "elevated_n_ge_100_pooled": bool(len(elev) >= 100),
            "elevated_n_ge_20_each_year": bool((ay.n >= 20).all()),
            "elevated_median_reverts_each_year": bool((ay.median_signed_F5_bp < 0).all()),
            "elevated_reversal_advantage_ge_5pp": bool((float(elev.reversal5.mean()) - float(norm.reversal5.mean())) >= 0.05) if len(elev) and len(norm) else False,
        }
        severity_ok = True
        for sevname in ("moderate", "extreme"):
            e = vv[(vv.severity_view == sevname) & (vv.activity_state == "ElevatedActivity")]
            n = vv[(vv.severity_view == sevname) & (vv.activity_state == "NormalActivity")]
            if len(e) != 1 or len(n) != 1:
                severity_ok = False
                continue
            er = e.iloc[0]; nr = n.iloc[0]
            if er.n < 30 or nr.n < 30 or not (er.median_signed_F5_bp < nr.median_signed_F5_bp):
                severity_ok = False
        checks["elevated_lower_median_within_both_severity_views"] = bool(severity_ok)

        direction_ok = True
        for d in ("UP", "DOWN"):
            e = vv[(vv.severity_view == d) & (vv.activity_state == "ElevatedActivity")]
            if len(e) != 1:
                direction_ok = False
                continue
            er = e.iloc[0]
            if er.n < 30 or not (er.median_signed_F5_bp < 0):
                direction_ok = False
        checks["both_elevated_directions_supported"] = bool(direction_ok)
        per_symbol[symbol] = {"checks": checks, "pass": bool(all(checks.values()))}

    annual = pd.DataFrame(annual_rows)
    views = pd.DataFrame(view_rows)
    verdict = "broad_signal_source_supported" if all(x["pass"] for x in per_symbol.values()) else "broad_signal_source_not_established"
    return annual, views, {"verdict": verdict, "per_symbol": per_symbol}


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

    frames = []
    for symbol in SYMBOLS:
        native = load_market_data(symbol, "1m", "2021-01-01", "2023-12-31", root=root)
        panel = make_panel(native, symbol)
        frames.append(build_events(panel, symbol))
    events = pd.concat(frames, ignore_index=True)
    if set(events.year.unique()) - set(YEARS):
        raise RuntimeError("non-Development row reached study")

    annual, views, decision = summarize(events)
    events.to_csv(out / "events.csv", index=False)
    annual.to_csv(out / "annual_summary.csv", index=False)
    views.to_csv(out / "view_summary.csv", index=False)
    summary = {
        "schema": "rmr_activity_pressure_reversal_v1",
        "development_years": list(YEARS),
        "events": int(len(events)),
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
    print(views.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
