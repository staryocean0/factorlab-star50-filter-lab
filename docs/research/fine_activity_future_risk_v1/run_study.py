#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
WARMUP_START = "2022-05-16"
DEV_START = "2023-01-01"
DEV_END = "2023-12-31"
MIN_HISTORY = 60
RANGE_BP = 30.0
EPS = 1e-16
M3_BANDS = [(-np.inf, 0.0, "<=0"), (0.0, 1.0, "(0,1]"), (1.0, 2.0, "(1,2]"), (2.0, np.inf, ">2")]


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sample_session(times, prices, rows) -> dict:
    """Strict 15-second grid; endpoint age <=3s and no crossed source gap >3s."""
    t = np.asarray(times, float)
    p = np.asarray(prices, float)
    r = np.asarray(rows)
    if not (len(t) == len(p) == len(r)):
        raise ValueError("3s shape mismatch")
    grid = np.arange(0, 7201, 15)
    value = np.full(len(grid), np.nan)
    returns = np.full(len(grid), np.nan)
    if not len(t):
        return {"second": grid, "price": value, "return_bp": returns}
    order = np.lexsort((r, t))
    t, p, r = t[order], p[order], r[order]
    if np.any((np.diff(t) == 0) & (np.diff(r) == 0)):
        raise ValueError("duplicate composite source key")
    pos = np.searchsorted(t, grid, side="right") - 1
    known = pos >= 0
    age = np.full(len(grid), np.nan)
    age[known] = grid[known] - t[pos[known]]
    good = known & (age <= 3)
    value[good] = p[pos[good]]
    gap_prefix = np.r_[0, np.cumsum(np.diff(t) > 3)]
    for j in range(1, len(grid)):
        if np.isfinite(value[j - 1 : j + 1]).all():
            a, b = pos[j - 1], pos[j]
            if gap_prefix[b] == gap_prefix[a]:
                returns[j] = np.log(value[j] / value[j - 1]) * 1e4
    return {"second": grid, "price": value, "return_bp": returns}


def attach_clock_z(frame: pd.DataFrame, raw_col: str, out_col: str, min_history: int = MIN_HISTORY) -> pd.DataFrame:
    out = frame.copy()
    out[out_col] = np.nan
    out["_day_order"] = pd.to_datetime(out["day"])
    for _, ix in out.groupby(["symbol", "afternoon", "minute"], sort=False).groups.items():
        idx = list(ix)
        idx.sort(key=lambda i: (out.at[i, "_day_order"], i))
        prior: list[float] = []
        for i in idx:
            x = out.at[i, raw_col]
            if pd.notna(x) and np.isfinite(float(x)) and float(x) > 0:
                lx = float(np.log(float(x)))
                if len(prior) >= min_history:
                    v = np.asarray(prior, float)
                    med = float(np.median(v))
                    mad = float(np.median(np.abs(v - med)))
                    scale = max(1.4826 * mad, 1e-8)
                    out.at[i, out_col] = (lx - med) / scale
                prior.append(lx)
    return out.drop(columns="_day_order")


def minute_panel(native: pd.DataFrame, symbol: str) -> pd.DataFrame:
    q = native.copy()
    q = q[q["symbol"] == symbol].copy()
    local = q["market_time_shanghai"].dt.tz_localize(None)
    q["afternoon"] = (local.dt.hour >= 13).astype(int)
    q["day"] = q["trading_day"].astype(str)
    q["session"] = q["day"] + "/" + q["afternoon"].astype(str)
    q = q.sort_values(["market_time_shanghai"], kind="stable").reset_index(drop=True)
    q["minute"] = q.groupby("session", sort=False).cumcount() + 1
    counts = q.groupby("session").size()
    keep = set(counts[counts == 120].index)
    q = q[q.session.isin(keep)].copy().reset_index(drop=True)
    if q.duplicated(["session", "minute"]).any():
        raise ValueError("duplicate minute key")
    q["eligible"] = q.get("high_frequency_analysis_eligible", True)
    q["eligible"] = q["eligible"].fillna(False).astype(bool)
    q["return_bp"] = np.nan
    for _, ix in q.groupby("session", sort=False).groups.items():
        idx = np.asarray(list(ix))
        close = q.loc[idx, "close"].to_numpy(float)
        ret = np.r_[np.nan, np.diff(np.log(close)) * 1e4]
        q.loc[idx, "return_bp"] = ret
    return q


def build_fine(root: Path, panel: pd.DataFrame, symbol: str) -> pd.DataFrame:
    sys.path.insert(0, str(root / "src"))
    from star50_filter.cloud_market_data import load_market_data

    rows = []
    for year in (2022, 2023):
        sec = load_market_data(symbol, "3s", f"{year}-01-01", f"{year}-12-31", root=root)
        ts = sec.market_time_shanghai.dt.tz_localize(None)
        s = sec[["trading_day", "row_index", "price"]].copy()
        s["second_day"] = (ts.dt.hour * 3600 + ts.dt.minute * 60 + ts.dt.second).to_numpy()
        s["afternoon"] = (s.second_day >= 13 * 3600).astype(int)
        s["session"] = s.trading_day.astype(str) + "/" + s.afternoon.astype(str)
        s["second"] = s.second_day - np.where(s.afternoon == 1, 13 * 3600, 9 * 3600 + 30 * 60)
        s = s[s.second.between(0, 7200)].copy()
        groups = {k: z for k, z in s.groupby("session", sort=False)}
        pyear = panel[pd.to_datetime(panel.day).dt.year == year]
        for session, part in pyear.groupby("session", sort=False):
            raw = groups.get(session)
            if raw is None:
                sample = sample_session([], [], [])
            else:
                sample = sample_session(raw.second.to_numpy(float), raw.price.to_numpy(float), raw.row_index.to_numpy())
            price = sample["price"]
            r15 = sample["return_bp"]
            coarse = part.sort_values("minute").return_bp.to_numpy(float)
            elig = part.sort_values("minute").eligible.to_numpy(bool)
            for minute in range(1, 121):
                item = {"symbol": symbol, "session": session, "day": str(part.day.iloc[0]),
                        "afternoon": int(part.afternoon.iloc[0]), "minute": minute,
                        "fine_complete5": False, "pre5m_range_bp": np.nan,
                        "A5": np.nan, "M1": np.nan, "rms1m5": np.nan}
                if minute >= 5:
                    j = minute * 4
                    fine = r15[j - 19 : j + 1]
                    px = price[j - 20 : j + 1]
                    c = coarse[minute - 5 : minute]
                    e = elig[minute - 5 : minute]
                    complete = (len(fine) == 20 and len(px) == 21 and np.isfinite(fine).all()
                                and np.isfinite(px).all() and (px > 0).all()
                                and len(c) == 5 and np.isfinite(c).all() and bool(e.all()))
                    item["fine_complete5"] = bool(complete)
                    if complete:
                        rel = np.log(px / px[0]) * 1e4
                        item["pre5m_range_bp"] = float(rel.max() - rel.min())
                        item["A5"] = float(np.sqrt(np.mean(fine * fine)))
                        rvf = float(np.sum(fine * fine))
                        rvc = float(np.sum(c * c))
                        item["M1"] = float(np.log((rvf + EPS) / (rvc + EPS)))
                        item["rms1m5"] = float(np.sqrt(np.mean(c * c)))
                rows.append(item)
        del sec, s, groups
    return pd.DataFrame(rows)


def attach_future_targets(panel: pd.DataFrame) -> pd.DataFrame:
    q = panel[["symbol", "session", "day", "afternoon", "minute", "return_bp", "eligible"]].copy()
    q["future_rms15_bp"] = np.nan
    q["future_mean_abs15_bp"] = np.nan
    q["future_any_unsafe15"] = np.nan
    q["current_vol_ratio"] = np.nan
    for _, ix in q.groupby("session", sort=False).groups.items():
        idx = np.asarray(list(ix))
        r = q.loc[idx, "return_bp"].to_numpy(float)
        e = q.loc[idx, "eligible"].to_numpy(bool)
        z = np.full(120, np.nan)
        for u in range(34, 120):
            recent = r[u - 4 : u + 1]
            back = r[u - 34 : u - 4]
            ee = e[u - 34 : u + 1]
            if np.isfinite(recent).all() and np.isfinite(back).all() and ee.all():
                rr = float(np.sqrt(np.mean(recent * recent)))
                bb = max(float(np.sqrt(np.mean(back * back))), 1.0)
                z[u] = rr / bb
        q.loc[idx, "current_vol_ratio"] = z
        for t in range(34, 105):
            fut = r[t + 1 : t + 16]
            ef = e[t + 1 : t + 16]
            zf = z[t + 1 : t + 16]
            if len(fut) == 15 and np.isfinite(fut).all() and ef.all() and np.isfinite(zf).all():
                q.loc[idx[t], "future_rms15_bp"] = float(np.sqrt(np.mean(fut * fut)))
                q.loc[idx[t], "future_mean_abs15_bp"] = float(np.mean(np.abs(fut)))
                q.loc[idx[t], "future_any_unsafe15"] = float(np.any(zf >= 1.5))
    return q


def band_label(x: float) -> str | None:
    if not np.isfinite(x):
        return None
    if x <= 0:
        return "<=0"
    if x <= 1:
        return "(0,1]"
    if x <= 2:
        return "(1,2]"
    return ">2"


def summarize(frame: pd.DataFrame, score: str = "M3") -> pd.DataFrame:
    x = frame.copy()
    x["band"] = x[score].map(band_label)
    rows = []
    order = [b[2] for b in M3_BANDS]
    for symbol in SYMBOLS:
        s = x[x.symbol == symbol]
        for band in order:
            z = s[s.band == band]
            rows.append({"symbol": symbol, "score": score, "band": band, "n": int(len(z)),
                         "median_future_rms15_bp": float(z.future_rms15_bp.median()) if len(z) else None,
                         "mean_future_rms15_bp": float(z.future_rms15_bp.mean()) if len(z) else None,
                         "mean_future_abs15_bp": float(z.future_mean_abs15_bp.mean()) if len(z) else None,
                         "future_any_unsafe15_prob": float(z.future_any_unsafe15.mean()) if len(z) else None})
    return pd.DataFrame(rows)


def incremental_control(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for symbol in SYMBOLS:
        s = frame[(frame.symbol == symbol) & (frame.C1z < 1)].copy()
        for group, z in (("M3<1", s[s.M3 < 1]), ("M3>=1", s[s.M3 >= 1])):
            rows.append({"symbol": symbol, "group": group, "n": int(len(z)),
                         "median_future_rms15_bp": float(z.future_rms15_bp.median()) if len(z) else None,
                         "future_any_unsafe15_prob": float(z.future_any_unsafe15.mean()) if len(z) else None})
    return pd.DataFrame(rows)


def adjudicate(summary_m3: pd.DataFrame, control: pd.DataFrame) -> dict:
    per_symbol = {}
    order = ["<=0", "(0,1]", "(1,2]", ">2"]
    for symbol in SYMBOLS:
        s = summary_m3[summary_m3.symbol == symbol].set_index("band").loc[order]
        med = s.median_future_rms15_bp.to_numpy(float)
        n = s.n.to_numpy(int)
        unsafe = s.future_any_unsafe15_prob.to_numpy(float)
        c = control[control.symbol == symbol].set_index("group")
        ok = {
            "all_bands_n_ge_100": bool((n >= 100).all()),
            "median_rms_nondecreasing": bool(np.all(np.diff(med) >= -1e-12)),
            "top_bottom_median_rms_ratio_ge_1_10": bool(med[-1] / med[0] >= 1.10),
            "top_bottom_unsafe_delta_ge_5pp": bool(unsafe[-1] - unsafe[0] >= 0.05),
            "control_groups_n_ge_500": bool((c.n >= 500).all()),
            "within_c1_m3_higher_rms": bool(c.loc["M3>=1", "median_future_rms15_bp"] > c.loc["M3<1", "median_future_rms15_bp"]),
            "within_c1_m3_higher_unsafe": bool(c.loc["M3>=1", "future_any_unsafe15_prob"] > c.loc["M3<1", "future_any_unsafe15_prob"]),
        }
        per_symbol[symbol] = {"checks": ok, "pass": bool(all(ok.values()))}
    verdict = "development_structure_supported" if all(v["pass"] for v in per_symbol.values()) else "development_structure_not_established"
    return {"verdict": verdict, "per_symbol": per_symbol}


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

    panels = []
    fines = []
    for symbol in SYMBOLS:
        native = load_market_data(symbol, "1m", WARMUP_START, DEV_END, root=root)
        p = minute_panel(native, symbol)
        panels.append(p)
        fines.append(build_fine(root, p, symbol))
    panel = pd.concat(panels, ignore_index=True)
    fine = pd.concat(fines, ignore_index=True)
    target = attach_future_targets(panel)
    keys = ["symbol", "session", "day", "afternoon", "minute"]
    frame = target.merge(fine, on=keys, how="inner", validate="one_to_one")
    frame = attach_clock_z(frame, "A5", "M3")
    frame = attach_clock_z(frame, "rms1m5", "C1z")
    frame["M4"] = frame.M3 + frame.M1

    day = pd.to_datetime(frame.day)
    eligible = ((day >= pd.Timestamp(DEV_START)) & (day <= pd.Timestamp(DEV_END))
                & frame.fine_complete5 & (frame.pre5m_range_bp < RANGE_BP)
                & frame.minute.between(35, 105)
                & np.isfinite(frame.M3) & np.isfinite(frame.C1z)
                & np.isfinite(frame.future_rms15_bp) & np.isfinite(frame.future_mean_abs15_bp)
                & np.isfinite(frame.future_any_unsafe15))
    dev = frame.loc[eligible].copy()
    if len(dev) < 1000:
        raise RuntimeError(f"insufficient development rows: {len(dev)}")

    s3 = summarize(dev, "M3")
    s4 = summarize(dev, "M4")
    ctl = incremental_control(dev)
    decision = adjudicate(s3, ctl)

    s3.to_csv(out / "m3_band_summary.csv", index=False)
    s4.to_csv(out / "m4_band_summary.csv", index=False)
    ctl.to_csv(out / "incremental_control.csv", index=False)
    dev[["symbol", "day", "session", "minute", "pre5m_range_bp", "M1", "M3", "M4", "C1z",
         "current_vol_ratio", "future_rms15_bp", "future_mean_abs15_bp", "future_any_unsafe15"]].to_csv(
             out / "development_rows.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})

    summary = {
        "schema": "fine_activity_future_risk_v1",
        "development_evaluation_year": 2023,
        "warmup_start": WARMUP_START,
        "development_rows": int(len(dev)),
        "rows_by_symbol": {k: int(v) for k, v in dev.groupby("symbol").size().items()},
        "decision": decision,
        "validation_queried": False,
        "blackbox_queried": False,
        "fresh_oos": False,
        "returns_or_pnl_evaluated": False,
        "candidate_nominated": False,
        "production_authority": False,
        "git_sha": os.getenv("GITHUB_SHA"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
    }
    write_json(out / "summary.json", summary)
    files = []
    for p in sorted(out.iterdir()):
        if p.is_file():
            files.append({"name": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)})
    write_json(out / "output_manifest.json", {"files": files})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(s3.to_string(index=False))
    print(ctl.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
