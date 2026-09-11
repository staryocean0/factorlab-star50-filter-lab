from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
REF_YEARS = (2020, 2021, 2022, 2023)
DEV_YEARS = (2021, 2022, 2023)
HORIZONS = (15, 30, 60)
PRIMARY_LEAD_SECONDS = 15
EXPECTED_ROW_COUNT = 7327
EXPECTED_V9_BLOB = "ae2a7e095df58692ef9df0dfee5856cac727ca44"
EXPECTED_V11_BLOB = "713f0dcc41e7f32f75934fc7709a406ff71579e6"
EXPECTED_V16_SURFACE_BLOB = "1f88966cf5dd3fb102f0d75746d5d00434555647"

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
FROZEN_V9 = HERE / "frozen_v9.py"
FROZEN_V11 = HERE / "frozen_v11.py"
V16_DIR = RESEARCH / "highvol_horizon_adaptive_v16"
V16_SURFACE = V16_DIR / "FROZEN_HORIZON_ADAPTIVE_SURFACE.json"
V16_RUNNER = V16_DIR / "run_surface.py"
V16_PROTOCOL = V16_DIR / "PROTOCOL.md"


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


def load_frozen_modules():
    if not FROZEN_V9.exists() or git_blob_sha(FROZEN_V9) != EXPECTED_V9_BLOB:
        raise RuntimeError("frozen V9 runner missing or drifted")
    if not FROZEN_V11.exists() or git_blob_sha(FROZEN_V11) != EXPECTED_V11_BLOB:
        raise RuntimeError("frozen V11 runner missing or drifted")
    v9 = load_module(FROZEN_V9, "v9_frozen_for_v17")
    v11 = load_module(FROZEN_V11, "v11_frozen_for_v17")
    v9.REF_YEARS = REF_YEARS
    v9.DEV_YEARS = DEV_YEARS
    v9.SYMBOLS = SYMBOLS
    v9.PRIMARY_LEAD_SECONDS = PRIMARY_LEAD_SECONDS
    v11.REF_YEARS = REF_YEARS
    v11.DEV_YEARS = DEV_YEARS
    v11.SYMBOLS = SYMBOLS
    v11.HORIZONS = HORIZONS
    constants9 = (v9.RV_WINDOW, v9.BG_WINDOW, v9.HIGHVOL_RATIO, v9.RECOVERY_NORMAL_RATIO, v9.SHOCK_SIGMA)
    constants11 = (v11.RV_WINDOW, v11.BG_WINDOW, v11.HIGHVOL_RATIO, v11.RECOVERY_NORMAL_RATIO, v11.SHOCK_SIGMA)
    if constants9 != constants11 or constants9 != (12, 48, 1.5, 1.1, 3.0):
        raise RuntimeError(f"risk-state constant drift: V9={constants9}, V11={constants11}")
    return v9, v11


def frozen_authority() -> dict:
    if git_blob_sha(V16_SURFACE) != EXPECTED_V16_SURFACE_BLOB:
        raise RuntimeError("frozen V16 surface blob drift")
    frozen = json.loads(V16_SURFACE.read_text())
    if frozen.get("schema") != "highvol_horizon_adaptive_surface_v16_frozen_v1":
        raise RuntimeError("unexpected V16 frozen schema")
    if frozen.get("validation_authorized") is not True or frozen.get("adaptive_surface_supported") is not True:
        raise RuntimeError("V16 frozen authority is not validation-authorized/supported")
    if git_blob_sha(V16_RUNNER) != frozen["source_runner_blob_sha"]:
        raise RuntimeError("V16 Development runner blob drift")
    if git_blob_sha(V16_PROTOCOL) != frozen["source_protocol_blob_sha"]:
        raise RuntimeError("V16 Development protocol blob drift")
    if tuple(frozen["horizons_minutes"]) != HORIZONS:
        raise RuntimeError("V16 horizon drift")
    return frozen


def prediction_maps(frozen: dict):
    adaptive = {}
    for r in frozen["adaptive_surface"]:
        adaptive[(r["current_state"], r["age_bucket"])] = {
            h: float(r[f"p_{h}m"]) for h in HORIZONS
        }
    age_only = {}
    for r in frozen["age_only_comparator"]:
        age_only[r["age_bucket"]] = {h: float(r[f"p_{h}m"]) for h in HORIZONS}
    if len(adaptive) != 8 or len(age_only) != 4:
        raise RuntimeError("V16 frozen map cardinality drift")
    for (state, bucket), p in adaptive.items():
        if not (p[15] <= p[30] <= p[60]):
            raise RuntimeError(f"V16 monotonicity drift: {state}/{bucket}")
        if abs(p[60] - age_only[bucket][60]) > 1e-15:
            raise RuntimeError(f"V16 60m anchor drift: {state}/{bucket}")
    return adaptive, age_only


def build_v11_rows(root: Path, v11) -> pd.DataFrame:
    frames = v11.restrict_common_days({s: v11.load_symbol(root, s) for s in SYMBOLS})
    frames = {s: v11.add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([v11.build_rows(frames[s]) for s in SYMBOLS], ignore_index=True)
    if len(rows) != EXPECTED_ROW_COUNT:
        raise RuntimeError(f"V11 cohort drift: {len(rows)} != {EXPECTED_ROW_COUNT}")
    if set(rows.year.unique()) != set(DEV_YEARS):
        raise RuntimeError(f"V11 Development years drift: {sorted(rows.year.unique())}")
    rows["bar_end"] = pd.to_datetime(rows["timestamp"], errors="coerce")
    if rows.bar_end.isna().any():
        raise RuntimeError("V11 cohort timestamp parse failure")
    return rows


def align_to_v9_reference(v9, ref: pd.DataFrame, rows: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    ref_key = ref.reset_index().rename(columns={"index": "global_idx"})[
        ["global_idx", "trading_day", "bar_end", "risk_state"]
    ].copy()
    z = rows.merge(ref_key, on=["trading_day", "bar_end"], how="left", validate="one_to_one")
    if z.global_idx.isna().any():
        raise RuntimeError("V11/V9 bar alignment missing row(s)")
    z["global_idx"] = z.global_idx.astype(int)
    matched = z.current_state.eq(z.risk_state)
    receipt = {
        "rows": int(len(z)),
        "state_match_rows": int(matched.sum()),
        "state_match_rate": float(matched.mean()),
        "passed": bool(matched.all()),
    }
    if not receipt["passed"]:
        bad = z.loc[~matched, ["trading_day", "bar_end", "current_state", "risk_state"]].head().to_dict("records")
        raise RuntimeError(f"V11/V9 final state alignment drift: {bad}")
    z = z.drop(columns=["risk_state"])
    z["reference_state"] = z["current_state"]
    z["reference_probability"] = np.nan
    z["normal_within_next15"] = z["normal_within_15m"].astype(bool)
    return z, receipt


def attach_realtime(v9, root: Path, rows: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    pieces = []
    alignment = []
    for symbol in SYMBOLS:
        ref = v9.load_reference(root, symbol)
        r = rows[rows.symbol.eq(symbol)].copy()
        aligned, receipt = align_to_v9_reference(v9, ref, r)
        receipt["symbol"] = symbol
        alignment.append(receipt)
        pieces.append(v9.attach_realtime(root, ref, aligned, symbol))
    out = pd.concat(pieces, ignore_index=True)
    if len(out) != EXPECTED_ROW_COUNT:
        raise RuntimeError("realtime attach changed cohort row count")
    return out, alignment


def add_v16_predictions(detail: pd.DataFrame, adaptive: dict, age_only: dict) -> pd.DataFrame:
    z = detail.copy()
    scored = z.realtime_reason.eq("scored")
    for h in HORIZONS:
        z[f"reference_p_{h}m"] = [adaptive[(s, b)][h] for s, b in zip(z.current_state, z.age_bucket)]
        z[f"realtime_p_{h}m"] = np.nan
    idx = z.index[scored]
    for i in idx:
        state = str(z.at[i, "partial_state"])
        bucket = str(z.at[i, "age_bucket"])
        z.at[i, "realtime_p_15m"] = adaptive[(state, bucket)][15]
        z.at[i, "realtime_p_30m"] = adaptive[(state, bucket)][30]
        z.at[i, "realtime_p_60m"] = age_only[bucket][60]
    return z


def score(v11, y, p) -> dict:
    return v11.score(np.asarray(y, int), np.asarray(p, float))


def summarize(v11, x: pd.DataFrame, group_type: str, group_value: str) -> dict:
    matched = x[x.realtime_reason.eq("scored")].copy()
    n = int(len(x))
    m = int(len(matched))
    out = {
        "group_type": group_type,
        "group_value": group_value,
        "reference_rows": n,
        "realtime_scored_rows": m,
        "realtime_coverage": float(m / n) if n else None,
        "exact_state_agreement": float(matched.partial_state.eq(matched.current_state).mean()) if m else None,
        "fresh_shock_unscorable": int(x.realtime_reason.eq("fresh_shock").sum()),
        "partial_normal_unscorable": int(x.realtime_reason.eq("partial_normal").sum()),
        "missing_checkpoint_unscorable": int(x.realtime_reason.eq("missing_3s_checkpoint").sum()),
        "missing_reference_window_unscorable": int(x.realtime_reason.eq("missing_reference_window").sum()),
        "horizons": {},
    }
    for h in HORIZONS:
        ycol = f"normal_within_{h}m"
        rp = f"reference_p_{h}m"
        tp = f"realtime_p_{h}m"
        ref_all = score(v11, x[ycol].astype(int), x[rp]) if n else None
        ref_match = score(v11, matched[ycol].astype(int), matched[rp]) if m else None
        realtime = score(v11, matched[ycol].astype(int), matched[tp]) if m else None
        mae = float(np.mean(np.abs(matched[tp] - matched[rp]))) if m else None
        max_diff = float(np.max(np.abs(matched[tp] - matched[rp]))) if m else None
        out["horizons"][str(h)] = {
            "reference_all": ref_all,
            "reference_matched": ref_match,
            "realtime_matched": realtime,
            "probability_mae_vs_reference": mae,
            "max_abs_probability_diff_vs_reference": max_diff,
            "exact_probability_cell_agreement": float(np.isclose(matched[tp], matched[rp], rtol=0, atol=1e-15).mean()) if m else None,
            "brier_degradation_matched": float(realtime["brier"] - ref_match["brier"]) if m else None,
            "logloss_degradation_matched": float(realtime["log_loss"] - ref_match["log_loss"]) if m else None,
        }
    return out


def rowwise_guard(z: pd.DataFrame) -> dict:
    m = z[z.realtime_reason.eq("scored")].copy()
    mono = (m.realtime_p_15m <= m.realtime_p_30m) & (m.realtime_p_30m <= m.realtime_p_60m)
    anchor = np.abs(m.realtime_p_60m.to_numpy(float) - m.reference_p_60m.to_numpy(float))
    return {
        "scored_rows": int(len(m)),
        "monotone_rows": int(mono.sum()),
        "monotone_all_rows": bool(mono.all()),
        "max_abs_60m_anchor_diff": float(anchor.max()) if len(anchor) else None,
        "sixty_minute_anchor_exact": bool(len(anchor) > 0 and np.max(anchor) <= 1e-15),
    }


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


def run(root: Path, out: Path) -> dict:
    frozen = frozen_authority()
    adaptive, age_only = prediction_maps(frozen)
    v9, v11 = load_frozen_modules()
    rows = build_v11_rows(root, v11)
    detail, alignment = attach_realtime(v9, root, rows)
    detail = add_v16_predictions(detail, adaptive, age_only)

    pooled = summarize(v11, detail, "pooled", "pooled")
    yearly = {str(y): summarize(v11, detail[detail.year.eq(y)], "year", str(y)) for y in DEV_YEARS}
    by_symbol = {s: summarize(v11, detail[detail.symbol.eq(s)], "symbol", s) for s in SYMBOLS}
    guard = rowwise_guard(detail)

    acceptance = {
        "exact_v11_common_cohort_7327": int(len(detail)) == EXPECTED_ROW_COUNT,
        "v11_v9_final_state_alignment_exact": all(r["passed"] for r in alignment),
        "pooled_coverage_ge_098": pooled["realtime_coverage"] >= 0.98,
        "each_year_coverage_ge_095": all(yearly[str(y)]["realtime_coverage"] >= 0.95 for y in DEV_YEARS),
        "pooled_probability_mae_le_001_15m_30m": all(pooled["horizons"][str(h)]["probability_mae_vs_reference"] <= 0.01 for h in (15, 30)),
        "pooled_brier_degradation_le_0002_15m_30m": all(pooled["horizons"][str(h)]["brier_degradation_matched"] <= 0.002 for h in (15, 30)),
        "each_year_brier_degradation_le_0005_15m_30m": all(yearly[str(y)]["horizons"][str(h)]["brier_degradation_matched"] <= 0.005 for y in DEV_YEARS for h in (15, 30)),
        "realtime_rowwise_monotone": guard["monotone_all_rows"],
        "sixty_minute_exact_frozen_age_anchor": bool(
            guard["sixty_minute_anchor_exact"]
            and abs(pooled["horizons"]["60"]["probability_mae_vs_reference"]) <= 1e-12
            and abs(pooled["horizons"]["60"]["brier_degradation_matched"]) <= 1e-12
            and abs(pooled["horizons"]["60"]["logloss_degradation_matched"]) <= 1e-12
        ),
        "frozen_v16_surface_unchanged": True,
        "frozen_v9_state_measurement_unchanged": True,
        "frozen_v11_cohort_unchanged": True,
        "lead_time_search_performed_false": True,
        "probability_fit_performed_false": True,
        "threshold_search_performed_false": True,
        "projection_change_performed_false": True,
        "posthoc_horizon_selection_false": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }

    summary = {
        "schema": "highvol_realtime_horizon_adaptive_v17_development_v1",
        "development_only": True,
        "development_period": ["2021-01-01", "2023-12-31"],
        "symbols": list(SYMBOLS),
        "horizons_minutes": list(HORIZONS),
        "primary_lead_seconds": PRIMARY_LEAD_SECONDS,
        "row_count": int(len(detail)),
        "frozen_authority": {
            "v16_surface_blob": EXPECTED_V16_SURFACE_BLOB,
            "v16_source_execution_commit": frozen["source_execution_commit"],
            "v16_source_run_id": frozen["source_run_id"],
            "v9_runner_blob": EXPECTED_V9_BLOB,
            "v11_runner_blob": EXPECTED_V11_BLOB,
        },
        "construction": frozen["construction"],
        "v11_v9_alignment": alignment,
        "pooled": pooled,
        "yearly": yearly,
        "by_symbol": by_symbol,
        "rowwise_guard": guard,
        "probability_fit_performed": False,
        "threshold_search_performed": False,
        "lead_time_search_performed": False,
        "projection_change_performed": False,
        "posthoc_horizon_selection": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
        "acceptance": acceptance,
        "validation_eligible": bool(all(acceptance.values())),
    }

    out.mkdir(parents=True, exist_ok=True)
    detail.to_parquet(out / "detail.parquet", index=False)
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
