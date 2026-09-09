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
SCALES_BP = (20.0, 40.0)
PRIMARY_H = 5
SECONDARY_H = 15


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
    return q[["day", "session", "minute", "eligible", "close"]]


def move_bp(a: float, b: float) -> float:
    return float(np.log(b / a) * 1e4)


def dc_events_for_session(part: pd.DataFrame, symbol: str, delta_bp: float) -> list[dict]:
    z = part.sort_values("minute", kind="stable").reset_index(drop=True)
    if len(z) != 120:
        return []
    p = z.close.to_numpy(float)
    elig = z.eligible.to_numpy(bool)
    if not np.isfinite(p).all() or (p <= 0).any():
        return []

    mode = 0  # 0 unknown, +1 up, -1 down
    run_high = p[0]
    run_low = p[0]
    extreme = p[0]
    confirm_price = np.nan
    overshoot_fired = False
    raw_events: list[tuple[int, str, int]] = []

    for j in range(1, 120):
        if not elig[j]:
            # Broken support resets the event engine; do not bridge gaps.
            mode = 0
            run_high = run_low = p[j]
            extreme = p[j]
            confirm_price = np.nan
            overshoot_fired = False
            continue

        price = p[j]
        if mode == 0:
            run_high = max(run_high, price)
            run_low = min(run_low, price)
            up = move_bp(run_low, price) >= delta_bp
            down = -move_bp(run_high, price) >= delta_bp
            if up and not down:
                mode = 1
                confirm_price = price
                extreme = price
                overshoot_fired = False
                raw_events.append((j, "confirmation", mode))
            elif down and not up:
                mode = -1
                confirm_price = price
                extreme = price
                overshoot_fired = False
                raw_events.append((j, "confirmation", mode))
            continue

        if mode == 1:
            if price > extreme:
                extreme = price
            if not overshoot_fired and move_bp(confirm_price, extreme) >= delta_bp:
                raw_events.append((j, "overshoot", mode))
                overshoot_fired = True
            if -move_bp(extreme, price) >= delta_bp:
                mode = -1
                confirm_price = price
                extreme = price
                overshoot_fired = False
                raw_events.append((j, "confirmation", mode))
        else:
            if price < extreme:
                extreme = price
            if not overshoot_fired and -move_bp(confirm_price, extreme) >= delta_bp:
                raw_events.append((j, "overshoot", mode))
                overshoot_fired = True
            if move_bp(extreme, price) >= delta_bp:
                mode = 1
                confirm_price = price
                extreme = price
                overshoot_fired = False
                raw_events.append((j, "confirmation", mode))

    rows = []
    for j, event_type, direction in raw_events:
        if j + SECONDARY_H >= 120:
            continue
        if not elig[j : j + SECONDARY_H + 1].all():
            continue
        f5 = move_bp(p[j], p[j + PRIMARY_H])
        f15 = move_bp(p[j], p[j + SECONDARY_H])
        rows.append({
            "symbol": symbol,
            "day": z.loc[j, "day"],
            "session": z.loc[j, "session"],
            "minute": int(z.loc[j, "minute"]),
            "year": int(str(z.loc[j, "day"])[:4]),
            "scale_bp": float(delta_bp),
            "event_type": event_type,
            "direction": "UP" if direction > 0 else "DOWN",
            "signed_F5_bp": float(direction * f5),
            "signed_F15_bp": float(direction * f15),
            "reversal5": bool(direction * f5 < 0),
        })
    return rows


def build_events(panel: pd.DataFrame, symbol: str) -> pd.DataFrame:
    rows = []
    for _, part in panel.groupby("session", sort=False):
        for delta in SCALES_BP:
            rows.extend(dc_events_for_session(part, symbol, delta))
    return pd.DataFrame(rows)


def cell_metrics(z: pd.DataFrame) -> dict:
    return {
        "n": int(len(z)),
        "median_signed_F5_bp": float(z.signed_F5_bp.median()) if len(z) else None,
        "mean_signed_F5_bp": float(z.signed_F5_bp.mean()) if len(z) else None,
        "reversal5_prob": float(z.reversal5.mean()) if len(z) else None,
        "median_signed_F15_bp": float(z.signed_F15_bp.median()) if len(z) else None,
    }


def summarize(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    annual_rows = []
    pooled_rows = []
    passes: dict[str, dict[str, bool]] = {}

    for symbol in SYMBOLS:
        passes[symbol] = {}
        for scale in SCALES_BP:
            s = events[(events.symbol == symbol) & (events.scale_bp == scale)]
            for year in YEARS:
                for event_type in ("confirmation", "overshoot"):
                    z = s[(s.year == year) & (s.event_type == event_type)]
                    annual_rows.append({"symbol": symbol, "scale_bp": scale, "year": year,
                                        "event_type": event_type, **cell_metrics(z)})
            for event_type in ("confirmation", "overshoot"):
                z = s[s.event_type == event_type]
                pooled_rows.append({"symbol": symbol, "scale_bp": scale,
                                    "view": event_type, **cell_metrics(z)})
            for direction in ("UP", "DOWN"):
                z = s[(s.event_type == "overshoot") & (s.direction == direction)]
                pooled_rows.append({"symbol": symbol, "scale_bp": scale,
                                    "view": f"overshoot_{direction}", **cell_metrics(z)})

    annual = pd.DataFrame(annual_rows)
    pooled = pd.DataFrame(pooled_rows)
    checks = {}
    for symbol in SYMBOLS:
        checks[symbol] = {}
        for scale in SCALES_BP:
            a = annual[(annual.symbol == symbol) & (annual.scale_bp == scale)]
            oyear = a[a.event_type == "overshoot"].set_index("year")
            p = pooled[(pooled.symbol == symbol) & (pooled.scale_bp == scale)].set_index("view")
            o = p.loc["overshoot"]
            c = p.loc["confirmation"]
            up = p.loc["overshoot_UP"]
            down = p.loc["overshoot_DOWN"]
            cell_checks = {
                "overshoot_n_ge_100_pooled": bool(o.n >= 100),
                "overshoot_n_ge_20_each_year": bool((oyear.n >= 20).all()),
                "overshoot_median_reverts_each_year": bool((oyear.median_signed_F5_bp < 0).all()),
                "reversal_prob_advantage_ge_5pp": bool(o.reversal5_prob - c.reversal5_prob >= 0.05),
                "median_improvement_ge_2bp": bool(o.median_signed_F5_bp <= c.median_signed_F5_bp - 2.0),
                "up_n_ge_30_and_reverts": bool(up.n >= 30 and up.median_signed_F5_bp < 0),
                "down_n_ge_30_and_reverts": bool(down.n >= 30 and down.median_signed_F5_bp < 0),
            }
            passed = bool(all(cell_checks.values()))
            checks[symbol][str(int(scale))] = {"checks": cell_checks, "pass": passed}
            passes[symbol][str(int(scale))] = passed

    common_scales = [str(int(scale)) for scale in SCALES_BP
                     if all(passes[s][str(int(scale))] for s in SYMBOLS)]
    verdict = "broad_signal_source_supported" if common_scales else "broad_signal_source_not_established"
    decision = {"verdict": verdict, "common_passing_scales_bp": common_scales, "per_symbol_scale": checks}
    return annual, pooled, decision


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

    annual, pooled, decision = summarize(events)
    events.to_csv(out / "events.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    annual.to_csv(out / "annual_summary.csv", index=False)
    pooled.to_csv(out / "pooled_summary.csv", index=False)
    summary = {
        "schema": "rmr_event_overshoot_exhaustion_v1",
        "development_years": list(YEARS),
        "scales_bp": list(SCALES_BP),
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
    print(pooled.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
