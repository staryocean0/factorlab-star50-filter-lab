from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
REF_YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
VAL_YEARS = (2024, 2025)
HORIZONS = (15, 30, 60)
PRIMARY_LEAD_SECONDS = 15
EXPECTED_FROZEN_TRANSFER_BLOB = "5aca30ff398f73173a5424aa14b535bd461df5b4"
EXPECTED_V17_RUNNER_BLOB = "397d80037806ba11cadf7f77717d36d55fbafc91"
EXPECTED_V9_BLOB = "ae2a7e095df58692ef9df0dfee5856cac727ca44"
EXPECTED_V11_BLOB = "713f0dcc41e7f32f75934fc7709a406ff71579e6"

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
V17_DIR = RESEARCH / "highvol_realtime_horizon_adaptive_v17"
FROZEN_TRANSFER = V17_DIR / "FROZEN_REALTIME_TRANSFER.json"
V17_RUNNER = V17_DIR / "run_v17.py"
V17_PROTOCOL = V17_DIR / "PROTOCOL.md"
FROZEN_V17 = HERE / "frozen_v17.py"
FROZEN_V9 = HERE / "frozen_v9.py"
FROZEN_V11 = HERE / "frozen_v11.py"


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


def frozen_transfer_authority() -> dict:
    if git_blob_sha(FROZEN_TRANSFER) != EXPECTED_FROZEN_TRANSFER_BLOB:
        raise RuntimeError("frozen V17 transfer blob drift")
    frozen = json.loads(FROZEN_TRANSFER.read_text())
    if frozen.get("schema") != "highvol_realtime_horizon_adaptive_v17_frozen_transfer_v1":
        raise RuntimeError("unexpected frozen V17 schema")
    if frozen.get("validation_authorized") is not True:
        raise RuntimeError("V17 Development did not authorize Validation")
    if frozen.get("checkpoint_seconds_before_5m_close") != PRIMARY_LEAD_SECONDS:
        raise RuntimeError("V17 checkpoint drift")
    if tuple(frozen.get("horizons_minutes", [])) != HORIZONS:
        raise RuntimeError("V17 horizon drift")
    if git_blob_sha(V17_RUNNER) != frozen["source_runner_blob_sha"]:
        raise RuntimeError("V17 Development runner blob drift")
    if git_blob_sha(V17_PROTOCOL) != frozen["source_protocol_blob_sha"]:
        raise RuntimeError("V17 Development protocol blob drift")
    return frozen


def load_frozen_modules():
    if git_blob_sha(FROZEN_V17) != EXPECTED_V17_RUNNER_BLOB:
        raise RuntimeError("materialized frozen V17 runner drift")
    if git_blob_sha(FROZEN_V9) != EXPECTED_V9_BLOB:
        raise RuntimeError("materialized frozen V9 runner drift")
    if git_blob_sha(FROZEN_V11) != EXPECTED_V11_BLOB:
        raise RuntimeError("materialized frozen V11 runner drift")
    v17 = load_module(FROZEN_V17, "v17_frozen_for_validation")
    v9 = load_module(FROZEN_V9, "v9_frozen_for_v17_validation")
    v11 = load_module(FROZEN_V11, "v11_frozen_for_v17_validation")
    v9.REF_YEARS = REF_YEARS
    v9.DEV_YEARS = VAL_YEARS
    v9.SYMBOLS = SYMBOLS
    v9.PRIMARY_LEAD_SECONDS = PRIMARY_LEAD_SECONDS
    v11.REF_YEARS = REF_YEARS
    v11.DEV_YEARS = VAL_YEARS
    v11.SYMBOLS = SYMBOLS
    v11.HORIZONS = HORIZONS
    constants9 = (v9.RV_WINDOW, v9.BG_WINDOW, v9.HIGHVOL_RATIO, v9.RECOVERY_NORMAL_RATIO, v9.SHOCK_SIGMA)
    constants11 = (v11.RV_WINDOW, v11.BG_WINDOW, v11.HIGHVOL_RATIO, v11.RECOVERY_NORMAL_RATIO, v11.SHOCK_SIGMA)
    if constants9 != constants11 or constants9 != (12, 48, 1.5, 1.1, 3.0):
        raise RuntimeError("risk-state constant drift")
    return v17, v9, v11


def build_validation_rows(root: Path, v11) -> pd.DataFrame:
    frames = v11.restrict_common_days({s: v11.load_symbol(root, s) for s in SYMBOLS})
    frames = {s: v11.add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([v11.build_rows(frames[s]) for s in SYMBOLS], ignore_index=True)
    if rows.empty:
        raise RuntimeError("empty V17 Validation cohort")
    if set(rows.year.unique()) - set(VAL_YEARS):
        raise RuntimeError(f"non-Validation year entered cohort: {sorted(rows.year.unique())}")
    rows["bar_end"] = pd.to_datetime(rows["timestamp"], errors="coerce")
    if rows.bar_end.isna().any():
        raise RuntimeError("Validation cohort timestamp parse failure")
    return rows


def attach_realtime(v17, v9, root: Path, rows: pd.DataFrame):
    pieces = []
    alignment = []
    for symbol in SYMBOLS:
        ref = v9.load_reference(root, symbol)
        r = rows[rows.symbol.eq(symbol)].copy()
        aligned, receipt = v17.align_to_v9_reference(v9, ref, r)
        receipt["symbol"] = symbol
        alignment.append(receipt)
        pieces.append(v9.attach_realtime(root, ref, aligned, symbol))
    return pd.concat(pieces, ignore_index=True), alignment


def clean(v17, obj):
    return v17.clean(obj)


def run(root: Path, out: Path) -> dict:
    frozen = frozen_transfer_authority()
    v17, v9, v11 = load_frozen_modules()
    v16 = v17.frozen_authority()
    adaptive, age_only = v17.prediction_maps(v16)

    rows = build_validation_rows(root, v11)
    detail, alignment = attach_realtime(v17, v9, root, rows)
    detail = v17.add_v16_predictions(detail, adaptive, age_only)

    pooled = v17.summarize(v11, detail, "pooled", "pooled")
    yearly = {str(y): v17.summarize(v11, detail[detail.year.eq(y)], "year", str(y)) for y in VAL_YEARS}
    by_symbol = {s: v17.summarize(v11, detail[detail.symbol.eq(s)], "symbol", s) for s in SYMBOLS}
    guard = v17.rowwise_guard(detail)
    year_counts = {str(y): int(detail.year.eq(y).sum()) for y in VAL_YEARS}

    acceptance = {
        "pooled_common_cohort_rows_ge_3000": int(len(detail)) >= 3000,
        "each_validation_year_nonempty": all(year_counts[str(y)] > 0 for y in VAL_YEARS),
        "v11_v9_final_state_alignment_exact": all(r["passed"] for r in alignment),
        "pooled_coverage_ge_098": pooled["realtime_coverage"] >= 0.98,
        "each_year_coverage_ge_095": all(yearly[str(y)]["realtime_coverage"] >= 0.95 for y in VAL_YEARS),
        "pooled_probability_mae_le_001_15m_30m": all(pooled["horizons"][str(h)]["probability_mae_vs_reference"] <= 0.01 for h in (15, 30)),
        "pooled_brier_degradation_le_0002_15m_30m": all(pooled["horizons"][str(h)]["brier_degradation_matched"] <= 0.002 for h in (15, 30)),
        "each_year_brier_degradation_le_0005_15m_30m": all(yearly[str(y)]["horizons"][str(h)]["brier_degradation_matched"] <= 0.005 for y in VAL_YEARS for h in (15, 30)),
        "realtime_rowwise_monotone": guard["monotone_all_rows"],
        "sixty_minute_exact_frozen_age_anchor": bool(
            guard["sixty_minute_anchor_exact"]
            and abs(pooled["horizons"]["60"]["probability_mae_vs_reference"]) <= 1e-12
            and abs(pooled["horizons"]["60"]["brier_degradation_matched"]) <= 1e-12
            and abs(pooled["horizons"]["60"]["logloss_degradation_matched"]) <= 1e-12
        ),
        "frozen_v17_transfer_unchanged": True,
        "frozen_v16_surface_unchanged": True,
        "frozen_v9_state_measurement_unchanged": True,
        "frozen_v11_cohort_unchanged": True,
        "probability_fit_performed_false": True,
        "threshold_search_performed_false": True,
        "lead_time_search_performed_false": True,
        "projection_change_performed_false": True,
        "posthoc_horizon_selection_false": True,
        "no_2026_3s_queried": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True
    }

    summary = {
        "schema": "highvol_realtime_horizon_adaptive_v17_reusable_validation_v1",
        "reusable_validation": True,
        "validation_period": ["2024-01-01", "2025-12-31"],
        "validation_years": list(VAL_YEARS),
        "symbols": list(SYMBOLS),
        "horizons_minutes": list(HORIZONS),
        "primary_lead_seconds": PRIMARY_LEAD_SECONDS,
        "row_count": int(len(detail)),
        "year_row_counts": year_counts,
        "frozen_development_authority": {
            "source_execution_commit": frozen["source_execution_commit"],
            "source_run_id": frozen["source_run_id"],
            "source_artifact_id": frozen["source_artifact_id"],
            "frozen_transfer_blob": EXPECTED_FROZEN_TRANSFER_BLOB,
            "frozen_runner_blob": EXPECTED_V17_RUNNER_BLOB
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
        "validation_queried": True,
        "queried_3s_years": [2024, 2025],
        "queried_2026_3s": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
        "acceptance": acceptance,
        "full_validation_supported": bool(all(acceptance.values()))
    }

    out.mkdir(parents=True, exist_ok=True)
    detail.to_parquet(out / "detail.parquet", index=False)
    (out / "summary.json").write_text(json.dumps(clean(v17, summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(clean(v17, summary), sort_keys=True))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.repo_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
