from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

COSTS = (0.5, 1.0, 1.5, 2.0)
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20260909
PRIMARY_COST = 1.0
DEV_YEARS = (2021, 2022, 2023)
VAL_YEARS = (2024, 2025, 2026)

HERE = Path(__file__).resolve().parent
DEV_RUNNER = HERE.parent / "highvol_router_v1_dev" / "run_router_dev.py"


def load_dev():
    spec = importlib.util.spec_from_file_location("highvol_router_v1_dev_frozen", DEV_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(DEV_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clean_json(obj):
    if isinstance(obj, dict):
        return {str(k): clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [clean_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        x = float(obj)
        return x if np.isfinite(x) else None
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def load_native(root: Path) -> pd.DataFrame:
    base = root / "data/cross_index_risk_gate_v1/1m/000852.SH"
    expected = [base / f"{y}.parquet" for y in range(2020, 2026)]
    p26 = root / "data/cross_index_risk_gate_2026_v1/1m/000852.SH/2026.parquet"
    paths = expected + [p26]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(missing)
    frames = [pd.read_parquet(p) for p in paths]
    x = pd.concat(frames, ignore_index=True)
    x["trading_day"] = x.trading_day.astype(str).str[:10]
    x["ts"] = pd.to_datetime(x.timestamp.astype(str).str[:19])
    if x.trading_day.min() < "2020-01-01" or x.trading_day.max() > "2026-08-21":
        raise RuntimeError((x.trading_day.min(), x.trading_day.max()))
    return x.sort_values(["trading_day", "ts"], kind="stable").reset_index(drop=True)


def build_period(dev, minute: pd.DataFrame, start: str, end: str):
    m = minute[(minute.trading_day >= start) & (minute.trading_day <= end)].reset_index(drop=True)
    onsets = dev.build_onsets(m)
    qualifying = dev.frozen_qualifying(onsets)
    trades = dev.apply_nonoverlap(qualifying)
    return m, onsets, qualifying, trades


def basic_trade_stats(trades: pd.DataFrame, cost: float = PRIMARY_COST) -> dict:
    n = int(len(trades))
    if n == 0:
        return {"trades": 0, "mean_gross_bp": np.nan, "mean_net_bp": np.nan, "total_net_bp": 0.0, "one_way_break_even_bp": np.nan}
    gross = trades.gross_3m_bp.to_numpy(float)
    mean_gross = float(np.mean(gross))
    total_net = float(np.sum(gross) - 2.0 * cost * n)
    return {
        "trades": n,
        "mean_gross_bp": mean_gross,
        "mean_net_bp": float(mean_gross - 2.0 * cost),
        "total_net_bp": total_net,
        "one_way_break_even_bp": float(mean_gross / 2.0),
    }


def daily_panel(minute: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    days = pd.DataFrame({"trading_day": sorted(minute.trading_day.astype(str).unique())})
    days["year"] = days.trading_day.str[:4].astype(int)
    if len(trades):
        q = trades.groupby("trading_day", as_index=False).agg(
            trades=("gross_3m_bp", "size"), gross_bp=("gross_3m_bp", "sum")
        )
    else:
        q = pd.DataFrame(columns=["trading_day", "trades", "gross_bp"])
    d = days.merge(q, on="trading_day", how="left")
    d[["trades", "gross_bp"]] = d[["trades", "gross_bp"]].fillna(0)
    d["trades"] = d.trades.astype(int)
    for cost in COSTS:
        d[f"net_{cost:g}bp_leg"] = d.gross_bp - 2.0 * cost * d.trades
    return d


def cost_stress(period: str, trades: pd.DataFrame) -> list[dict]:
    rows = []
    for cost in COSTS:
        s = basic_trade_stats(trades, cost)
        rows.append({"period": period, "cost_bp_per_leg": cost, **s})
    return rows


def annual_primary(period: str, trades: pd.DataFrame, years) -> list[dict]:
    rows = []
    for y in years:
        rows.append({"period": period, "year": y, **basic_trade_stats(trades[trades.year == y], PRIMARY_COST)})
    return rows


def leave_one_year_out(period: str, trades: pd.DataFrame, years) -> list[dict]:
    rows = []
    for y in years:
        kept = trades[trades.year != y]
        rows.append({"period": period, "excluded_year": y, **basic_trade_stats(kept, PRIMARY_COST)})
    return rows


def concentration_sensitivity(period: str, daily: pd.DataFrame) -> list[dict]:
    net_col = f"net_{PRIMARY_COST:g}bp_leg"
    ranked = daily[daily[net_col] > 0].sort_values(net_col, ascending=False)
    rows = []
    for k in (1, 3, 5):
        removed_days = set(ranked.head(k).trading_day.astype(str))
        kept = daily[~daily.trading_day.astype(str).isin(removed_days)].copy()
        total_gross = float(kept.gross_bp.sum())
        n = int(kept.trades.sum())
        total_net = float(total_gross - 2.0 * PRIMARY_COST * n)
        rows.append({
            "period": period,
            "removed_top_positive_days": k,
            "removed_day_count": len(removed_days),
            "remaining_trades": n,
            "remaining_total_net_bp": total_net,
            "remaining_mean_net_bp_per_trade": float(total_net / n) if n else np.nan,
        })
    return rows


def bootstrap_daily(period: str, daily: pd.DataFrame) -> dict:
    gross = daily.gross_bp.to_numpy(float)
    counts = daily.trades.to_numpy(int)
    n_days = len(daily)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = np.full(BOOTSTRAP_DRAWS, np.nan, float)
    for j in range(BOOTSTRAP_DRAWS):
        idx = rng.integers(0, n_days, size=n_days)
        n = int(counts[idx].sum())
        if n:
            draws[j] = float((gross[idx].sum() - 2.0 * PRIMARY_COST * n) / n)
    finite = draws[np.isfinite(draws)]
    if not len(finite):
        raise RuntimeError("bootstrap produced no finite draws")
    return {
        "period": period,
        "resampling_unit": "complete_trading_day_including_zero_trade_days",
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
        "finite_draws": int(len(finite)),
        "mean_net_bp_per_trade": float(np.mean(finite)),
        "ci_2_5_bp": float(np.quantile(finite, 0.025)),
        "ci_97_5_bp": float(np.quantile(finite, 0.975)),
        "probability_mean_net_gt_zero": float(np.mean(finite > 0)),
    }


def run(root: Path, out: Path) -> dict:
    dev = load_dev()
    native = load_native(root)
    minute_all = dev.build_minute(native)

    dm, _, dq, dt = build_period(dev, minute_all, "2021-01-01", "2023-12-31")
    vm, _, vq, vt = build_period(dev, minute_all, "2024-01-01", "2026-08-21")

    dd = daily_panel(dm, dt)
    vd = daily_panel(vm, vt)

    cost_rows = cost_stress("Development", dt) + cost_stress("Validation", vt)
    annual_rows = annual_primary("Development", dt, DEV_YEARS) + annual_primary("Validation", vt, VAL_YEARS)
    loo_rows = leave_one_year_out("Development", dt, DEV_YEARS) + leave_one_year_out("Validation", vt, VAL_YEARS)
    conc_rows = concentration_sensitivity("Development", dd) + concentration_sensitivity("Validation", vd)
    boot = {
        "Development": bootstrap_daily("Development", dd),
        "Validation": bootstrap_daily("Validation", vd),
    }

    val_cost = {r["cost_bp_per_leg"]: r for r in cost_rows if r["period"] == "Validation"}
    val_annual = {r["year"]: r for r in annual_rows if r["period"] == "Validation"}
    val_conc = {r["removed_top_positive_days"]: r for r in conc_rows if r["period"] == "Validation"}
    reasons = []
    if boot["Validation"]["ci_2_5_bp"] <= 0:
        reasons.append("validation_day_block_bootstrap_interval_crosses_zero")
    if val_cost[1.5]["mean_net_bp"] <= 0:
        reasons.append("validation_mean_net_nonpositive_at_1_5bp_per_leg")
    if val_conc[5]["remaining_mean_net_bp_per_trade"] <= 0:
        reasons.append("validation_mean_net_nonpositive_after_removing_top5_positive_days")
    if val_annual[2026]["mean_net_bp"] <= 0:
        reasons.append("validation_2026_slice_nonpositive")

    conclusion = "PRIMARY_COST_EDGE_POSITIVE_WITH_MATERIAL_STABILITY_FRAGILITY" if reasons else "NO_PRESET_FRAGILITY_FLAG_TRIGGERED"

    summary = {
        "schema": "highvol_router_v1_stability_audit_v1",
        "diagnostic_only": True,
        "candidate_changed": False,
        "routing_changed": False,
        "production_authority": False,
        "blackbox_queried": False,
        "development_period": ["2021-01-01", "2023-12-31"],
        "validation_period": ["2024-01-01", "2026-08-21"],
        "frozen_router_receipt_blob_sha": "ea9b00736369f75b8dd5df2661e54afd24516e3b",
        "frozen_dev_runner_blob_sha": "52aa0db330b3489c4196b6e718f8c7f6f8628d13",
        "development_frozen_qualifying": int(len(dq)),
        "development_accepted_trades": int(len(dt)),
        "validation_frozen_qualifying": int(len(vq)),
        "validation_accepted_trades": int(len(vt)),
        "cost_stress": cost_rows,
        "annual_primary": annual_rows,
        "leave_one_year_out": loo_rows,
        "concentration_sensitivity": conc_rows,
        "bootstrap": boot,
        "preset_fragility_reasons": reasons,
        "diagnostic_conclusion": conclusion,
    }

    out.mkdir(parents=True, exist_ok=True)
    dt.to_csv(out / "development_trades.csv", index=False)
    vt.to_csv(out / "validation_trades.csv", index=False)
    dd.to_csv(out / "development_daily.csv", index=False)
    vd.to_csv(out / "validation_daily.csv", index=False)
    pd.DataFrame(cost_rows).to_csv(out / "cost_stress.csv", index=False)
    pd.DataFrame(annual_rows).to_csv(out / "annual_primary.csv", index=False)
    pd.DataFrame(loo_rows).to_csv(out / "leave_one_year_out.csv", index=False)
    pd.DataFrame(conc_rows).to_csv(out / "concentration_sensitivity.csv", index=False)
    (out / "bootstrap.json").write_text(json.dumps(clean_json(boot), indent=2, allow_nan=False) + "\n")
    clean = clean_json(summary)
    (out / "summary.json").write_text(json.dumps(clean, indent=2, allow_nan=False) + "\n")
    print(json.dumps(clean, allow_nan=False))
    return clean


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run(Path(args.repo_root).resolve(), Path(args.out))


if __name__ == "__main__":
    main()
