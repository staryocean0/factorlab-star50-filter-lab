from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOL = "000852.SH"
DEV_YEARS = (2021, 2022, 2023)
HOLD_MIN = 3
COST_BP_PER_LEG = 1.0
FROZEN = {
    "highvol_ratio_min": 1.5,
    "highvol_fast_window_min": 5,
    "highvol_background_window_min": 30,
    "highvol_background_floor_bp": 1.0,
    "slow_window_min": 30,
    "tail2_share_min": 0.60,
    "tail1_share_max_exclusive": 0.60,
    "hold_min": 3,
    "cost_bp_per_leg": 1.0,
}
EXPECTED = {
    2021: {"trades": 37, "mean_gross_bp": 2.7611},
    2022: {"trades": 31, "mean_gross_bp": 3.1565},
    2023: {"trades": 36, "mean_gross_bp": 2.3531},
    "pooled": {"trades": 104, "mean_gross_bp": 2.7377},
}
PROVENANCE = {
    "frozen_candidate_blob_sha": "a1c0ee87f7fb34bcb3f2265e11fe7815e4de44e8",
    "dev_selector_blob_sha": "8b1bb8f0367348cc0ddeaecb6bb01d105d6b940b",
    "continuous_state_blob_sha": "e00dd3cec9c5e6ab7354deb538ea3262a12cdd13",
    "minute_grid_blob_sha": "64f7529d22353d45d03d2e9cad02372714933a34",
    "source_branch": "research/csi1000-long-accel-dev-v1-20260908",
    "data_blob_sha": {
        "2020": "25b7ebb894b8e27b7b8692aeffff613a170c6f1b",
        "2021": "a1b9327fcdc9939269ded4349364277848b8480c",
        "2022": "f5e699ddbe7fe26dc8e977bb8c72bad9ff83beef",
        "2023": "a915cc9a0e9259e2660558c07ffbe1d6c37c0e8f",
    },
}


def load_native(root: Path) -> pd.DataFrame:
    frames = []
    base = root / "data/cross_index_risk_gate_v1/1m" / SYMBOL
    expected = ["2020.parquet", "2021.parquet", "2022.parquet", "2023.parquet"]
    present = sorted(p.name for p in base.glob("*.parquet"))
    if present != expected:
        raise RuntimeError(f"Development physical boundary violated: {present}")
    for name in expected:
        frames.append(pd.read_parquet(base / name))
    x = pd.concat(frames, ignore_index=True)
    x["trading_day"] = x.trading_day.astype(str).str[:10]
    x["ts"] = pd.to_datetime(x.timestamp.astype(str).str[:19])
    return x.sort_values(["trading_day", "ts"], kind="stable").reset_index(drop=True)


def build_minute(native: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for day, zday in native.groupby("trading_day", sort=True):
        indexed = zday.set_index("ts")
        for half, start in ((0, pd.Timestamp(f"{day} 09:30:00")), (1, pd.Timestamp(f"{day} 13:00:00"))):
            times = pd.date_range(start, periods=120, freq="1min")
            z = indexed.reindex(times)
            close = pd.to_numeric(z.close, errors="coerce").to_numpy(float)
            opened = pd.to_numeric(z.open, errors="coerce").to_numpy(float)
            high = pd.to_numeric(z.high, errors="coerce").to_numpy(float)
            low = pd.to_numeric(z.low, errors="coerce").to_numpy(float)
            eligible = z.high_frequency_analysis_eligible.eq(True).to_numpy(bool)
            not_flat_fill = z.causal_flat_fill.eq(False).to_numpy(bool)
            close_valid = eligible & not_flat_fill & np.isfinite(close) & (close > 0)
            valid = close_valid & np.isfinite(opened) & (opened > 0) & np.isfinite(high) & (high > 0) & np.isfinite(low) & (low > 0)

            state_r = np.full(120, np.nan, float)
            for i in range(1, 120):
                if close_valid[i] and close_valid[i - 1]:
                    state_r[i] = np.log(close[i] / close[i - 1]) * 1e4
            sq = pd.Series(state_r * state_r)
            fast = np.sqrt(sq.rolling(5, min_periods=5).mean()).to_numpy()
            bg = np.sqrt(sq.shift(5).rolling(30, min_periods=30).mean()).to_numpy()
            ratio = fast / np.maximum(bg, FROZEN["highvol_background_floor_bp"])
            state = np.full(120, "Unknown", object)
            known = np.isfinite(ratio)
            state[known & (ratio >= FROZEN["highvol_ratio_min"])] = "HighVol"
            state[known & (ratio < FROZEN["highvol_ratio_min"])] = "NormalVol"

            session = f"{day}/{half}"
            for i in range(120):
                rows.append({
                    "symbol": SYMBOL,
                    "trading_day": day,
                    "year": int(day[:4]),
                    "session": session,
                    "minute": i + 1,
                    "timestamp": times[i],
                    "open": opened[i] if valid[i] else np.nan,
                    "close": close[i] if valid[i] else np.nan,
                    "valid": bool(valid[i]),
                    "route_state": state[i],
                    "vol_ratio": ratio[i] if np.isfinite(ratio[i]) else np.nan,
                })
    return pd.DataFrame(rows)


def build_onsets(minute: pd.DataFrame) -> pd.DataFrame:
    out = []
    for session, z0 in minute.groupby("session", sort=False):
        z = z0.sort_values("minute").reset_index(drop=True)
        st = z.route_state.to_numpy(object)
        c = z.close.to_numpy(float)
        op = z.open.to_numpy(float)
        valid = z.valid.to_numpy(bool)
        r = np.full(len(z), np.nan, float)
        for i in range(1, len(z)):
            if valid[i] and valid[i - 1] and np.isfinite(c[i]) and np.isfinite(c[i - 1]) and c[i] > 0 and c[i - 1] > 0:
                r[i] = np.log(c[i] / c[i - 1]) * 1e4
        for i in range(35, len(z)):
            if st[i] != "HighVol" or st[i - 1] != "NormalVol":
                continue
            recent = r[i - 4:i + 1]
            if not np.isfinite(recent).all():
                continue
            net5 = float(recent.sum())
            tv = float(np.abs(recent).sum())
            if net5 <= 0 or tv <= 0:
                continue
            slow = r[i - 34:i - 4]
            if len(slow) != 30 or not np.isfinite(slow).all():
                continue
            en = i + 1
            ex = en + HOLD_MIN
            gross = np.nan
            if ex < len(z) and valid[en:ex + 1].all() and np.isfinite(op[en]) and np.isfinite(op[ex]) and op[en] > 0 and op[ex] > 0:
                gross = float(np.log(op[ex] / op[en]) * 1e4)
            out.append({
                "year": int(z.year.iloc[0]),
                "trading_day": str(z.trading_day.iloc[0]),
                "session": session,
                "onset_row": i,
                "onset_minute": int(z.minute.iloc[i]),
                "entry_minute": int(z.minute.iloc[en]) if en < len(z) else None,
                "exit_minute": int(z.minute.iloc[ex]) if ex < len(z) else None,
                "vol_ratio": float(z.vol_ratio.iloc[i]),
                "net5_bp": net5,
                "slow30_net_bp": float(slow.sum()),
                "tail1_share": abs(float(recent[-1])) / tv,
                "tail2_share": float(np.abs(recent[-2:]).sum()) / tv,
                "gross_3m_bp": gross,
            })
    return pd.DataFrame(out)


def frozen_qualifying(events: pd.DataFrame) -> pd.DataFrame:
    z = events[
        (events.slow30_net_bp > 0)
        & (events.tail2_share >= FROZEN["tail2_share_min"])
        & (events.tail1_share < FROZEN["tail1_share_max_exclusive"])
        & np.isfinite(events.gross_3m_bp)
    ].copy()
    return z.sort_values(["session", "onset_row"], kind="stable").reset_index(drop=True)


def apply_nonoverlap(qualifying: pd.DataFrame, hold_min: int = HOLD_MIN) -> pd.DataFrame:
    rows = []
    for session, g in qualifying.groupby("session", sort=False):
        nxt = -1
        for _, row in g.sort_values("onset_row").iterrows():
            i = int(row.onset_row)
            if i < nxt:
                continue
            rows.append(row)
            nxt = i + 1 + hold_min
    if not rows:
        return qualifying.iloc[0:0].copy()
    return pd.DataFrame(rows).reset_index(drop=True)


def max_drawdown_bp(daily_net_bp: np.ndarray) -> float:
    cumulative = np.r_[0.0, np.cumsum(np.asarray(daily_net_bp, float))]
    peaks = np.maximum.accumulate(cumulative)
    return float(np.max(peaks - cumulative))


def daily_panel(minute: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    days = pd.DataFrame({"trading_day": sorted(minute[minute.year.isin(DEV_YEARS)].trading_day.unique())})
    days["year"] = days.trading_day.str[:4].astype(int)
    q = trades.groupby("trading_day", as_index=False).agg(
        trades=("gross_3m_bp", "size"), gross_bp=("gross_3m_bp", "sum"), net_bp=("net_1bp", "sum")
    ) if len(trades) else pd.DataFrame(columns=["trading_day", "trades", "gross_bp", "net_bp"])
    d = days.merge(q, on="trading_day", how="left")
    d[["trades", "gross_bp", "net_bp"]] = d[["trades", "gross_bp", "net_bp"]].fillna(0)
    d["trades"] = d.trades.astype(int)
    return d


def trade_stats(z: pd.DataFrame) -> dict:
    n = len(z)
    mean = float(z.gross_3m_bp.mean()) if n else np.nan
    return {
        "trades": n,
        "mean_gross_bp": mean,
        "mean_net1_bp": mean - 2 * COST_BP_PER_LEG if n else np.nan,
        "one_way_break_even_bp": mean / 2 if n else np.nan,
        "hit_rate": float((z.gross_3m_bp > 0).mean()) if n else np.nan,
    }


def daily_stats(d: pd.DataFrame) -> dict:
    arr = d.net_bp.to_numpy(float)
    std = float(np.std(arr, ddof=1)) if len(arr) > 1 else np.nan
    pos = np.sort(arr[arr > 0])[::-1]
    positive_sum = float(pos.sum())
    abs_sum = float(np.abs(arr).sum())
    total = float(arr.sum())
    def share(k: int) -> float:
        return float(pos[:k].sum() / positive_sum) if positive_sum > 0 else np.nan
    return {
        "trading_days": int(len(d)),
        "active_trade_days": int((d.trades > 0).sum()),
        "max_trades_per_day": int(d.trades.max()) if len(d) else 0,
        "mean_daily_net_bp": float(np.mean(arr)) if len(arr) else np.nan,
        "daily_net_std_bp": std,
        "daily_sharpe_proxy": float(np.mean(arr) / std * np.sqrt(252)) if np.isfinite(std) and std > 0 else np.nan,
        "max_drawdown_net_bp": max_drawdown_bp(arr),
        "total_net_bp": total,
        "top1_positive_day_share": share(1),
        "top3_positive_day_share": share(3),
        "top5_positive_day_share": share(5),
        "top5_net_share_of_total": float(np.sort(arr)[::-1][:5].sum() / total) if total > 0 else np.nan,
        "absolute_daily_pnl_hhi": float(np.sum((np.abs(arr) / abs_sum) ** 2)) if abs_sum > 0 else np.nan,
        "best_day_net_bp": float(np.max(arr)) if len(arr) else np.nan,
        "worst_day_net_bp": float(np.min(arr)) if len(arr) else np.nan,
    }


def reproduction_guard(annual: pd.DataFrame, pooled: dict) -> list[str]:
    errors = []
    tol = 0.01
    for year in DEV_YEARS:
        row = annual[annual.year == year].iloc[0]
        exp = EXPECTED[year]
        if int(row.trades) != exp["trades"]:
            errors.append(f"{year} trade count {int(row.trades)} != {exp['trades']}")
        if abs(float(row.mean_gross_bp) - exp["mean_gross_bp"]) > tol:
            errors.append(f"{year} gross mean drift {float(row.mean_gross_bp):.6f}")
    if int(pooled["trades"]) != EXPECTED["pooled"]["trades"]:
        errors.append(f"pooled trade count {pooled['trades']} != 104")
    if abs(float(pooled["mean_gross_bp"]) - EXPECTED["pooled"]["mean_gross_bp"]) > tol:
        errors.append(f"pooled gross mean drift {pooled['mean_gross_bp']:.6f}")
    return errors


def run(root: Path, out: Path) -> dict:
    native = load_native(root)
    minute = build_minute(native)
    minute = minute[(minute.trading_day >= "2021-01-01") & (minute.trading_day <= "2023-12-31")].reset_index(drop=True)
    onsets = build_onsets(minute)
    qualifying = frozen_qualifying(onsets)
    trades = apply_nonoverlap(qualifying)
    trades["net_1bp"] = trades.gross_3m_bp - 2 * COST_BP_PER_LEG

    annual_rows = []
    daily = daily_panel(minute, trades)
    for year in DEV_YEARS:
        t = trades[trades.year == year]
        d = daily[daily.year == year]
        annual_rows.append({"year": year, **trade_stats(t), **daily_stats(d)})
    annual = pd.DataFrame(annual_rows)
    pooled = {**trade_stats(trades), **daily_stats(daily)}

    overlap_rejected = int(len(qualifying) - len(trades))
    nonoverlap_ok = True
    for _, g in trades.groupby("session", sort=False):
        g = g.sort_values("entry_minute")
        if len(g) > 1 and not (g.entry_minute.to_numpy()[1:] > g.exit_minute.to_numpy()[:-1]).all():
            nonoverlap_ok = False
            break
    max_concurrent_positions = 1 if len(trades) else 0
    reproduction_errors = reproduction_guard(annual, pooled)
    star50_route_trade_count = 0
    router_freeze_eligible = bool(
        not reproduction_errors
        and nonoverlap_ok
        and max_concurrent_positions <= 1
        and star50_route_trade_count == 0
        and all(float(annual.loc[annual.year == y, "mean_net1_bp"].iloc[0]) > 0 for y in DEV_YEARS)
        and pooled["one_way_break_even_bp"] > 1.0
    )

    summary = {
        "schema": "highvol_router_v1_development_audit",
        "development_only": True,
        "validation_queried": False,
        "blackbox_queried": False,
        "production_authority": False,
        "routes": {"000852.SH": "ACTIVE_LONG_3M", "000688.SH": "NO_TRADE", "other_highvol_contexts": "NO_TRADE"},
        "frozen_parameters": FROZEN,
        "raw_positive_highvol_onsets": int(len(onsets)),
        "frozen_qualifying_before_nonoverlap": int(len(qualifying)),
        "accepted_nonoverlap_trades": int(len(trades)),
        "overlap_rejected": overlap_rejected,
        "max_concurrent_positions": max_concurrent_positions,
        "nonoverlap_ok": nonoverlap_ok,
        "star50_route_trade_count": star50_route_trade_count,
        "annual": annual.to_dict(orient="records"),
        "pooled": pooled,
        "reproduction_errors": reproduction_errors,
        "router_freeze_eligible": router_freeze_eligible,
        "provenance": PROVENANCE,
    }

    out.mkdir(parents=True, exist_ok=True)
    onsets.to_csv(out / "positive_highvol_onsets.csv", index=False)
    qualifying.to_csv(out / "frozen_qualifying.csv", index=False)
    trades.to_csv(out / "accepted_trades.csv", index=False)
    daily.to_csv(out / "daily_router_pnl.csv", index=False)
    annual.to_csv(out / "annual_audit.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str, allow_nan=False) + "\n")
    (out / "provenance.json").write_text(json.dumps(PROVENANCE, indent=2) + "\n")
    print(json.dumps(summary, default=str, allow_nan=False))
    if not router_freeze_eligible:
        raise SystemExit("Router V1 Development audit did not reproduce frozen candidate / mechanics")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run(Path(args.repo_root).resolve(), Path(args.out))


if __name__ == "__main__":
    main()
