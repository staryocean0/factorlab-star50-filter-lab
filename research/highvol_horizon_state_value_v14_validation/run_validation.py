from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
VAL_YEARS = (2024, 2025, 2026)
REF_YEARS = (2020, 2021, 2022, 2023, 2024, 2025, 2026)
HORIZONS = (15, 30, 60)
CUTOFF = "2026-08-21"
EXPECTED_2026_BLOBS = {
    "000688.SH": "4626fb307bbcae1c417ddcd69ac694cf322c8bbc",
    "000852.SH": "8de5cd3caab99dbacae229a2c87f15c4ff2f8558",
}
EXPECTED_FROZEN_SURFACE_BLOB = "be06a4988fb4a602e2b72d115268c926421aa1f5"

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
V11_RUNNER = RESEARCH / "highvol_recovery_survival_v11" / "run_survival.py"
V14_DIR = RESEARCH / "highvol_horizon_state_value_v14"
FROZEN_PATH = V14_DIR / "FROZEN_HORIZON_SURFACE.json"
V14_RUNNER = V14_DIR / "run_state_value.py"
V14_PROTOCOL = V14_DIR / "PROTOCOL.md"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def wallclock(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str).str.slice(0, 19), errors="coerce")


def standardize(path: Path, symbol: str) -> pd.DataFrame:
    x = pd.read_parquet(path)
    if "close" not in x.columns:
        raise RuntimeError(f"{path}: missing close")
    if "trading_day" in x.columns:
        day = pd.to_datetime(x.trading_day, errors="coerce")
    else:
        tcol = "timestamp" if "timestamp" in x.columns else "bar_end_shanghai"
        if tcol not in x.columns:
            raise RuntimeError(f"{path}: missing trading_day/timestamp")
        day = wallclock(x[tcol]).dt.normalize()
    if "timestamp" in x.columns:
        ts = wallclock(x.timestamp)
    elif "bar_end_shanghai" in x.columns:
        ts = wallclock(x.bar_end_shanghai)
    else:
        raise RuntimeError(f"{path}: missing timestamp/bar_end_shanghai")
    z = pd.DataFrame({
        "symbol": symbol,
        "trading_day": day.dt.strftime("%Y-%m-%d"),
        "timestamp": ts,
        "close": pd.to_numeric(x.close, errors="coerce"),
    }).dropna()
    return z.sort_values(["trading_day", "timestamp"], kind="stable").drop_duplicates(
        ["trading_day", "timestamp"], keep="last"
    ).reset_index(drop=True)


def synthesize_5m(one_minute: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for day, g0 in one_minute.groupby("trading_day", sort=False):
        g = g0.sort_values("timestamp", kind="stable").drop_duplicates("timestamp", keep="last").reset_index(drop=True)
        if len(g) != 240:
            raise RuntimeError(f"{day}: expected 240 one-minute rows, got {len(g)}")
        chosen = []
        for start in (0, 120):
            half = g.iloc[start:start + 120].reset_index(drop=True)
            if len(half) != 120:
                raise RuntimeError(f"{day}: incomplete half-day")
            chosen.append(half.iloc[np.arange(4, 120, 5)])
        z = pd.concat(chosen, ignore_index=True)[["symbol", "trading_day", "timestamp", "close"]]
        if len(z) != 48:
            raise RuntimeError(f"{day}: expected 48 synthesized 5m rows")
        parts.append(z)
    if not parts:
        raise RuntimeError("no one-minute rows to synthesize")
    return pd.concat(parts, ignore_index=True).reset_index(drop=True)


def equivalence_guard(root: Path, symbol: str) -> dict:
    src = standardize(root / "data/cross_index_risk_gate_v1/1m" / symbol / "2023.parquet", symbol)
    syn = synthesize_5m(src)
    native = standardize(root / "data/market/5m" / symbol / "2023.parquet", symbol)
    common = sorted(set(syn.trading_day).intersection(native.trading_day))
    if not common:
        raise RuntimeError(f"{symbol}: no common 2023 days for synthesis guard")
    s = syn[syn.trading_day.isin(common)].sort_values(["trading_day", "timestamp"], kind="stable").reset_index(drop=True)
    n = native[native.trading_day.isin(common)].sort_values(["trading_day", "timestamp"], kind="stable").reset_index(drop=True)
    if len(s) != len(n):
        raise RuntimeError(f"{symbol}: 2023 synthesized/native row mismatch {len(s)} != {len(n)}")
    if not (s.groupby("trading_day").size().eq(48).all() and n.groupby("trading_day").size().eq(48).all()):
        raise RuntimeError(f"{symbol}: 2023 non-48-row day")
    diff = np.abs(s.close.to_numpy(float) - n.close.to_numpy(float))
    max_abs = float(diff.max()) if len(diff) else np.nan
    if not np.isfinite(max_abs) or max_abs > 1e-9:
        raise RuntimeError(f"{symbol}: 1m->5m equivalence failed: {max_abs}")
    return {"symbol": symbol, "days": len(common), "rows": len(s), "max_abs_close_diff": max_abs, "passed": True}


def prepare_2026(root: Path, symbol: str) -> dict:
    src_path = root / "data/cross_index_risk_gate_v1/1m" / symbol / "2026.parquet"
    physical_blob = git_blob_sha(src_path)
    if physical_blob != EXPECTED_2026_BLOBS[symbol]:
        raise RuntimeError(f"{symbol}: sealed 2026 blob drift {physical_blob}")
    one = standardize(src_path, symbol)
    max_day = str(one.trading_day.max())
    min_day = str(one.trading_day.min())
    if max_day > CUTOFF:
        raise RuntimeError(f"{symbol}: 2026 source crosses cutoff: {max_day}")
    counts = one.groupby("trading_day").size()
    if not counts.eq(240).all():
        raise RuntimeError(f"{symbol}: 2026 one-minute incomplete day(s): {counts[counts.ne(240)].head().to_dict()}")
    syn = synthesize_5m(one)
    target = root / "data/market/5m" / symbol / "2026.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    syn.to_parquet(target, index=False)
    return {
        "symbol": symbol,
        "source_blob": physical_blob,
        "min_trading_day": min_day,
        "max_trading_day": max_day,
        "trading_days": int(one.trading_day.nunique()),
        "one_minute_rows": int(len(one)),
        "synthesized_5m_rows": int(len(syn)),
        "passed": True,
    }


def frozen_authority() -> dict:
    if git_blob_sha(FROZEN_PATH) != EXPECTED_FROZEN_SURFACE_BLOB:
        raise RuntimeError("frozen horizon surface blob drift")
    frozen = json.loads(FROZEN_PATH.read_text())
    if git_blob_sha(V14_RUNNER) != frozen["source_runner_blob_sha"]:
        raise RuntimeError("V14 Development runner blob drift")
    if git_blob_sha(V14_PROTOCOL) != frozen["source_protocol_blob_sha"]:
        raise RuntimeError("V14 Development protocol blob drift")
    if tuple(frozen["horizons_minutes"]) != HORIZONS:
        raise RuntimeError("frozen horizons drift")
    return frozen


def prediction_maps(frozen: dict):
    state_map = {}
    for r in frozen["state_plus_age_surface"]:
        state_map[(r["current_state"], r["age_bucket"])] = {h: float(r[f"p_{h}m"]) for h in HORIZONS}
    age_map = {}
    for r in frozen["age_only_comparator"]:
        age_map[r["age_bucket"]] = {h: float(r[f"p_{h}m"]) for h in HORIZONS}
    return state_map, age_map


def clean(v):
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, (np.floating, float)):
        x = float(v)
        return x if np.isfinite(x) else None
    return v


def score_set(v11, rows: pd.DataFrame, state_map: dict, age_map: dict) -> dict:
    out = {}
    for h in HORIZONS:
        y = rows[f"normal_within_{h}m"].astype(int).to_numpy()
        ps = np.array([state_map[(s, b)][h] for s, b in zip(rows.current_state, rows.age_bucket)], float)
        pa = np.array([age_map[b][h] for b in rows.age_bucket], float)
        ss = v11.score(y, ps)
        sa = v11.score(y, pa)
        out[str(h)] = {
            "state_plus_age": ss,
            "age_only": sa,
            "brier_improvement_state_over_age": float(sa["brier"] - ss["brier"]),
            "logloss_improvement_state_over_age": float(sa["log_loss"] - ss["log_loss"]),
        }
    return out


def run(root: Path, out: Path) -> dict:
    frozen = frozen_authority()
    equivalence = [equivalence_guard(root, s) for s in SYMBOLS]
    synthesis = [prepare_2026(root, s) for s in SYMBOLS]

    v11 = load_module(V11_RUNNER, "v11_frozen_for_v14_validation")
    v11.REF_YEARS = REF_YEARS
    v11.DEV_YEARS = VAL_YEARS
    v11.SYMBOLS = SYMBOLS
    v11.HORIZONS = HORIZONS
    if (v11.RV_WINDOW, v11.BG_WINDOW, v11.HIGHVOL_RATIO, v11.RECOVERY_NORMAL_RATIO, v11.SHOCK_SIGMA) != (12, 48, 1.5, 1.1, 3.0):
        raise RuntimeError("V11/V6 risk-state constants drift")

    frames = v11.restrict_common_days({s: v11.load_symbol(root, s) for s in SYMBOLS})
    frames = {s: v11.add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([v11.build_rows(frames[s]) for s in SYMBOLS], ignore_index=True)
    if rows.empty:
        raise RuntimeError("no V14 Validation cohort rows")
    if set(rows.year.unique()) - set(VAL_YEARS):
        raise RuntimeError("non-Validation year entered measured cohort")
    if rows.loc[rows.year.eq(2026), "trading_day"].max() > CUTOFF:
        raise RuntimeError("measured 2026 cohort crosses cutoff")

    state_map, age_map = prediction_maps(frozen)
    pooled = score_set(v11, rows, state_map, age_map)
    yearly = {str(y): score_set(v11, rows[rows.year.eq(y)], state_map, age_map) for y in VAL_YEARS}
    counts = {str(y): int(rows.year.eq(y).sum()) for y in VAL_YEARS}
    annual_brier_wins = {
        str(h): int(sum(yearly[str(y)][str(h)]["brier_improvement_state_over_age"] > 0 for y in VAL_YEARS))
        for h in HORIZONS
    }

    acceptance = {
        "pooled_common_cohort_rows_ge_3000": int(len(rows)) >= 3000,
        "each_validation_year_nonempty": all(counts[str(y)] > 0 for y in VAL_YEARS),
        "pooled_state_plus_age_brier_better_all_horizons": all(pooled[str(h)]["brier_improvement_state_over_age"] > 0 for h in HORIZONS),
        "pooled_state_plus_age_logloss_better_all_horizons": all(pooled[str(h)]["logloss_improvement_state_over_age"] > 0 for h in HORIZONS),
        "annual_brier_better_at_least_2_of_3_each_horizon": all(annual_brier_wins[str(h)] >= 2 for h in HORIZONS),
        "synthesis_equivalence_passed": all(r["passed"] for r in equivalence),
        "sealed_2026_source_and_cutoff_passed": all(r["passed"] for r in synthesis),
        "fit_performed_false": True,
        "parameter_change_performed_false": True,
        "threshold_search_performed_false": True,
        "posthoc_horizon_selection_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
        "blackbox_queried_false": True,
    }

    summary = {
        "schema": "highvol_horizon_specific_state_value_v14_full_validation_v1",
        "validation_period": ["2024-01-01", CUTOFF],
        "validation_years": list(VAL_YEARS),
        "symbols": list(SYMBOLS),
        "horizons_minutes": list(HORIZONS),
        "frozen_development_authority": {
            "source_branch": frozen["source_branch"],
            "source_execution_commit": frozen["source_execution_commit"],
            "source_run_id": frozen["source_run_id"],
            "source_artifact_id": frozen["source_artifact_id"],
            "frozen_surface_blob": EXPECTED_FROZEN_SURFACE_BLOB,
        },
        "row_count": int(len(rows)),
        "year_row_counts": counts,
        "synthesis_equivalence_2023": equivalence,
        "synthesis_2026": synthesis,
        "pooled_scores": pooled,
        "yearly_scores": yearly,
        "annual_brier_win_count": annual_brier_wins,
        "fit_performed": False,
        "parameter_change_performed": False,
        "threshold_search_performed": False,
        "posthoc_horizon_selection": False,
        "state_thresholds_unchanged": True,
        "age_buckets_unchanged": True,
        "sample_cohort_unchanged": True,
        "pnl_computed": False,
        "trading_rule_created": False,
        "blackbox_queried": False,
        "production_authority": False,
        "acceptance": acceptance,
        "full_validation_supported": bool(all(acceptance.values())),
    }

    out.mkdir(parents=True, exist_ok=True)
    rows.to_parquet(out / "validation_rows.parquet", index=False)
    (out / "synthesis_receipt.json").write_text(json.dumps(clean({"equivalence_2023": equivalence, "synthesis_2026": synthesis}), indent=2, sort_keys=True) + "\n")
    (out / "summary.json").write_text(json.dumps(clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(clean(summary), sort_keys=True))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.repo_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
