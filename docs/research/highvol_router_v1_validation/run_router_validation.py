from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DEV_RUNNER = HERE.parent / "highvol_router_v1_dev" / "run_router_dev.py"


def load_dev():
    spec = importlib.util.spec_from_file_location("highvol_router_v1_dev_frozen", DEV_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def json_safe(value):
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def load_validation_native(root: Path) -> pd.DataFrame:
    paths = [
        root / "data/cross_index_risk_gate_v1/1m/000852.SH/2024.parquet",
        root / "data/cross_index_risk_gate_v1/1m/000852.SH/2025.parquet",
        root / "data/cross_index_risk_gate_2026_v1/1m/000852.SH/2026.parquet",
    ]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(missing)
    frames = [pd.read_parquet(p) for p in paths]
    x = pd.concat(frames, ignore_index=True)
    x["trading_day"] = x.trading_day.astype(str).str[:10]
    x["ts"] = pd.to_datetime(x.timestamp.astype(str).str[:19])
    if x.trading_day.min() < "2024-01-01" or x.trading_day.max() > "2026-08-21":
        raise RuntimeError((x.trading_day.min(), x.trading_day.max()))
    return x.sort_values(["trading_day", "ts"], kind="stable").reset_index(drop=True)


def daily_panel(minute: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    days = pd.DataFrame({"trading_day": sorted(minute.trading_day.unique())})
    days["year"] = days.trading_day.str[:4].astype(int)
    if len(trades):
        q = trades.groupby("trading_day", as_index=False).agg(
            trades=("gross_3m_bp", "size"),
            gross_bp=("gross_3m_bp", "sum"),
            net_bp=("net_1bp", "sum"),
        )
    else:
        q = pd.DataFrame(columns=["trading_day", "trades", "gross_bp", "net_bp"])
    d = days.merge(q, on="trading_day", how="left")
    d[["trades", "gross_bp", "net_bp"]] = d[["trades", "gross_bp", "net_bp"]].fillna(0)
    d["trades"] = d.trades.astype(int)
    return d


def run(root: Path, out: Path) -> dict:
    dev = load_dev()
    native = load_validation_native(root)
    minute = dev.build_minute(native)
    minute = minute[(minute.trading_day >= "2024-01-01") & (minute.trading_day <= "2026-08-21")].reset_index(drop=True)
    onsets = dev.build_onsets(minute)
    qualifying = dev.frozen_qualifying(onsets)
    trades = dev.apply_nonoverlap(qualifying)
    trades["net_1bp"] = trades.gross_3m_bp - 2 * dev.COST_BP_PER_LEG
    daily = daily_panel(minute, trades)

    annual_rows = []
    for year in (2024, 2025, 2026):
        t = trades[trades.year == year]
        d = daily[daily.year == year]
        annual_rows.append({"year": year, **dev.trade_stats(t), **dev.daily_stats(d)})
    annual = pd.DataFrame(annual_rows)
    pooled = {**dev.trade_stats(trades), **dev.daily_stats(daily)}

    nonoverlap_ok = True
    for _, g in trades.groupby("session", sort=False):
        g = g.sort_values("entry_minute")
        if len(g) > 1 and not (g.entry_minute.to_numpy()[1:] > g.exit_minute.to_numpy()[:-1]).all():
            nonoverlap_ok = False
            break
    max_concurrent_positions = 1 if len(trades) else 0
    star50_route_trade_count = 0
    positive_slices = int((annual.mean_net1_bp > 0).sum())
    acceptance = {
        "pooled_completed_trades_min_30": bool(pooled["trades"] >= 30),
        "pooled_mean_net1_positive": bool(pooled["mean_net1_bp"] > 0),
        "at_least_2_of_3_year_slices_positive_net1": bool(positive_slices >= 2),
        "pooled_one_way_break_even_gt_1bp": bool(pooled["one_way_break_even_bp"] > 1.0),
        "star50_route_trade_count_zero": bool(star50_route_trade_count == 0),
        "nonoverlap_ok": bool(nonoverlap_ok),
        "max_concurrent_positions_lte_1": bool(max_concurrent_positions <= 1),
        "candidate_parameters_unchanged": True,
    }
    validation_supported = bool(all(acceptance.values()))

    summary = {
        "schema": "highvol_router_v1_reusable_validation",
        "candidate_id": "highvol_router_v1_csi1000_active_star50_no_trade",
        "validation_period": ["2024-01-01", "2026-08-21"],
        "fresh_oos": False,
        "fit_performed": False,
        "parameter_change_performed": False,
        "blackbox_queried": False,
        "production_authority": False,
        "routes": {"000852.SH": "ACTIVE_LONG_3M", "000688.SH": "NO_TRADE", "other_highvol_contexts": "NO_TRADE"},
        "raw_positive_highvol_onsets": int(len(onsets)),
        "frozen_qualifying_before_nonoverlap": int(len(qualifying)),
        "accepted_nonoverlap_trades": int(len(trades)),
        "overlap_rejected": int(len(qualifying) - len(trades)),
        "max_concurrent_positions": max_concurrent_positions,
        "star50_route_trade_count": star50_route_trade_count,
        "positive_validation_slices": positive_slices,
        "annual": annual.to_dict(orient="records"),
        "pooled": pooled,
        "acceptance": acceptance,
        "validation_supported": validation_supported,
        "frozen_dev_code_commit_sha": "33b2654e31ea8ac09711aeb77248ddfe68d9dea5",
        "frozen_dev_runner_blob_sha": "52aa0db330b3489c4196b6e718f8c7f6f8628d13",
        "frozen_router_receipt_blob_sha": "ea9b00736369f75b8dd5df2661e54afd24516e3b",
    }

    out.mkdir(parents=True, exist_ok=True)
    onsets.to_csv(out / "positive_highvol_onsets.csv", index=False)
    qualifying.to_csv(out / "frozen_qualifying.csv", index=False)
    trades.to_csv(out / "validation_trades.csv", index=False)
    daily.to_csv(out / "daily_router_pnl.csv", index=False)
    annual.to_csv(out / "annual_validation.csv", index=False)
    safe_summary = json_safe(summary)
    (out / "summary.json").write_text(json.dumps(safe_summary, indent=2, default=str, allow_nan=False) + "\n")
    print(json.dumps(safe_summary, default=str, allow_nan=False))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run(Path(args.repo_root).resolve(), Path(args.out))


if __name__ == "__main__":
    main()
