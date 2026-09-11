from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "v19_residual_failure_audit" / "run_audit.py"


def load_original():
    spec = importlib.util.spec_from_file_location("v19_residual_audit_original", ORIGINAL)
    if spec is None or spec.loader is None:
        raise RuntimeError(ORIGINAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


m = load_original()


def fixed_build_detail(root: Path, v19, v9, adaptive, age_only):
    pieces = []
    refs = {}
    windows_by_symbol = {}
    obs_by_symbol_day = {}
    boundaries = {}
    for symbol in m.SYMBOLS:
        x, b = v19.build_symbol_rows(root, v9, symbol)
        x["role"] = np.where(x.year <= 2023, "development", "validation")
        ref = v9.load_reference(root, symbol)
        refs[symbol] = ref
        windows_by_symbol[symbol] = v9.prior_windows(ref)
        for year in m.AUDIT_YEARS:
            sec = v9.load_3s(root, symbol, year)
            for day, g in sec.groupby("trading_day", sort=False):
                obs_by_symbol_day[(symbol, int(year), str(day))] = g.reset_index(drop=True)
        final_intensity = ref.shock_intensity.to_dict()
        final_ratio = ref.vol_ratio.to_dict()
        x["final_shock_intensity"] = x.global_idx.map(final_intensity)
        x["final_vol_ratio"] = x.global_idx.map(final_ratio)
        pieces.append(x)
        boundaries[symbol] = b
    detail = pd.concat(pieces, ignore_index=True)
    detail = v19.attach_recovery_probabilities(detail, v9, adaptive, age_only)
    detail = v19.add_episode_ids(detail, "reference_risk", "reference_e15_state", "reference_episode_id", "REF")
    detail = v19.add_episode_ids(detail, "machine_risk", "machine_state", "machine_episode_id", "MACH")

    avail = detail.checkpoint_available.astype(bool)
    detail["residual_type"] = "correct"
    detail.loc[avail & detail.reference_risk & ~detail.machine_risk, "residual_type"] = "risk_fn"
    detail.loc[avail & ~detail.reference_risk & detail.machine_risk, "residual_type"] = "risk_fp"
    detail.loc[
        avail & detail.reference_risk & detail.machine_risk & ~detail.machine_state.eq(detail.reference_e15_state),
        "residual_type",
    ] = "within_risk_state_mismatch"

    residual_mask = detail.residual_type.ne("correct")
    # Implementation-only repair after failed run 34613545773: state/shock
    # diagnostic columns must be object dtype because they hold None + bool/string.
    for lead in m.LATER_LEADS:
        detail[f"e{lead}_state"] = pd.Series([None] * len(detail), dtype="object")
        detail[f"e{lead}_shock"] = pd.Series([None] * len(detail), dtype="object")
        detail[f"e{lead}_ratio"] = np.nan
        detail[f"e{lead}_intensity"] = np.nan

    for i, r in detail[residual_mask].iterrows():
        symbol = str(r.symbol)
        ref = refs[symbol]
        rr = ref.loc[int(r.global_idx)]
        sec = obs_by_symbol_day[(symbol, int(r.year), str(r.trading_day))]
        for lead in m.LATER_LEADS:
            q = m.partial_at(v9, rr, windows_by_symbol[symbol], sec, lead)
            detail.at[i, f"e{lead}_state"] = q["state"]
            detail.at[i, f"e{lead}_shock"] = q["shock"]
            detail.at[i, f"e{lead}_ratio"] = q["ratio"]
            detail.at[i, f"e{lead}_intensity"] = q["intensity"]

    detail["fn_timing_class"] = None
    qmask = detail.residual_type.eq("risk_fn")
    detail.loc[qmask & detail.e6_state.map(m.is_risk), "fn_timing_class"] = "late_by_e6"
    detail.loc[qmask & ~detail.e6_state.map(m.is_risk) & detail.e3_state.map(m.is_risk), "fn_timing_class"] = "late_by_e3"
    detail.loc[qmask & ~detail.e6_state.map(m.is_risk) & ~detail.e3_state.map(m.is_risk), "fn_timing_class"] = "after_e3_or_close_only"

    detail["fp_timing_class"] = None
    qmask = detail.residual_type.eq("risk_fp")
    detail.loc[qmask & ~detail.e6_state.map(m.is_risk), "fp_timing_class"] = "resolved_by_e6"
    detail.loc[qmask & detail.e6_state.map(m.is_risk) & ~detail.e3_state.map(m.is_risk), "fp_timing_class"] = "resolved_by_e3"
    detail.loc[qmask & detail.e6_state.map(m.is_risk) & detail.e3_state.map(m.is_risk), "fp_timing_class"] = "persists_through_e3_then_resolves_by_close"

    detail["state_mismatch_class"] = None
    qmask = detail.residual_type.eq("within_risk_state_mismatch")
    detail.loc[qmask & detail.reference_e15_state.eq("UNSAFE") & detail.machine_state.eq("RECOVERING"), "state_mismatch_class"] = "reference_UNSAFE_machine_RECOVERING"
    detail.loc[qmask & detail.reference_e15_state.eq("RECOVERING") & detail.machine_state.eq("UNSAFE"), "state_mismatch_class"] = "reference_RECOVERING_machine_UNSAFE"
    detail["state_converges_by_e6"] = qmask & detail.e6_state.eq(detail.reference_e15_state)
    detail["state_converges_by_e3"] = qmask & detail.e3_state.eq(detail.reference_e15_state)

    detail["e15_intensity_band"] = detail.partial_shock_intensity.map(m.intensity_band)
    detail["final_intensity_band"] = detail.final_shock_intensity.map(m.intensity_band)
    return detail, boundaries


m.build_detail = fixed_build_detail

if __name__ == "__main__":
    m.main()
