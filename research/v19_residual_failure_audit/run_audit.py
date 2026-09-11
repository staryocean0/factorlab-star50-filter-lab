from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
REF_YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
AUDIT_YEARS = (2021, 2022, 2023, 2024, 2025)
LATER_LEADS = (6, 3)
RISK_STATES = ("UNSAFE", "RECOVERING")
EXPECTED_V19_BLOB = "ee2fce299d5ee21abf1ab2c2c5183bac101ae822"
EXPECTED_V9_BLOB = "ae2a7e095df58692ef9df0dfee5856cac727ca44"
EXPECTED_V18_BLOB = "62c207badff1c3e37cbb1a8e17ef89feeea611d8"
EXPECTED_V17_BLOB = "397d80037806ba11cadf7f77717d36d55fbafc91"
EXPECTED_V16_BLOB = "1f88966cf5dd3fb102f0d75746d5d00434555647"

HERE = Path(__file__).resolve().parent
FROZEN_V19 = HERE / "frozen_v19.py"


def git_blob_sha(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def is_risk(v) -> bool:
    return str(v) in RISK_STATES


def intensity_band(v) -> str:
    if pd.isna(v):
        return "missing"
    x = float(v)
    if x < 2.5:
        return "LT2_5"
    if x < 3.0:
        return "M2_5_3_0"
    if x < 3.5:
        return "M3_0_3_5"
    if x < 4.0:
        return "M3_5_4_0"
    return "GE4_0"


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
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    return v


def configure_frozen_v19():
    if git_blob_sha(FROZEN_V19) != EXPECTED_V19_BLOB:
        raise RuntimeError("frozen V19 runner drift")
    v19 = load_module(FROZEN_V19, "v19_frozen_for_residual_audit")
    v19.REF_YEARS = REF_YEARS
    v19.DEV_YEARS = AUDIT_YEARS
    v19.SYMBOLS = SYMBOLS
    v9, adaptive, age_only, receipt = v19.load_frozen_authority()
    expected = {
        "frozen_v9.py": EXPECTED_V9_BLOB,
        "frozen_v18.py": EXPECTED_V18_BLOB,
        "frozen_v17.py": EXPECTED_V17_BLOB,
        "frozen_v16_surface.json": EXPECTED_V16_BLOB,
    }
    if receipt != expected:
        raise RuntimeError(f"upstream receipt drift: {receipt}")
    return v19, v9, adaptive, age_only, receipt


def partial_at(v9, rr: pd.Series, windows: dict, sec: pd.DataFrame, lead: int) -> dict:
    idx = int(rr.name)
    if idx not in windows or pd.isna(rr.prev_close) or pd.isna(rr.bg_vol48):
        return {"state": None, "shock": None, "ratio": None, "intensity": None}
    target = pd.Timestamp(rr.bar_end) - pd.Timedelta(seconds=lead)
    start = pd.Timestamp(rr.bar_end) - pd.Timedelta(minutes=5)
    sel = v9.select_checkpoint(sec, start, target)
    if sel is None:
        return {"state": None, "shock": None, "ratio": None, "intensity": None}
    price, _ = sel
    pret = float(np.log(price) - np.log(float(rr.prev_close)))
    prv = float(np.std(np.concatenate([windows[idx], [pret]]), ddof=0))
    ratio = prv / float(rr.bg_vol48)
    intensity = abs(pret) / float(rr.bg_vol48)
    shock = bool(intensity >= v9.SHOCK_SIGMA)
    state = str(v9.transition(str(rr.prev_state), ratio, shock))
    return {"state": state, "shock": shock, "ratio": ratio, "intensity": intensity}


def build_detail(root: Path, v19, v9, adaptive, age_only):
    pieces = []
    refs = {}
    windows_by_symbol = {}
    obs_by_symbol_day = {}
    boundaries = {}
    for symbol in SYMBOLS:
        x, b = v19.build_symbol_rows(root, v9, symbol)
        x["role"] = np.where(x.year <= 2023, "development", "validation")
        ref = v9.load_reference(root, symbol)
        refs[symbol] = ref
        windows_by_symbol[symbol] = v9.prior_windows(ref)
        for year in AUDIT_YEARS:
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
    for lead in LATER_LEADS:
        for col in ("state", "shock", "ratio", "intensity"):
            detail[f"e{lead}_{col}"] = None if col == "state" else np.nan

    for i, r in detail[residual_mask].iterrows():
        symbol = str(r.symbol)
        ref = refs[symbol]
        rr = ref.loc[int(r.global_idx)]
        sec = obs_by_symbol_day[(symbol, int(r.year), str(r.trading_day))]
        for lead in LATER_LEADS:
            q = partial_at(v9, rr, windows_by_symbol[symbol], sec, lead)
            detail.at[i, f"e{lead}_state"] = q["state"]
            detail.at[i, f"e{lead}_shock"] = q["shock"]
            detail.at[i, f"e{lead}_ratio"] = q["ratio"]
            detail.at[i, f"e{lead}_intensity"] = q["intensity"]

    detail["fn_timing_class"] = None
    m = detail.residual_type.eq("risk_fn")
    detail.loc[m & detail.e6_state.map(is_risk), "fn_timing_class"] = "late_by_e6"
    detail.loc[m & ~detail.e6_state.map(is_risk) & detail.e3_state.map(is_risk), "fn_timing_class"] = "late_by_e3"
    detail.loc[m & ~detail.e6_state.map(is_risk) & ~detail.e3_state.map(is_risk), "fn_timing_class"] = "after_e3_or_close_only"

    detail["fp_timing_class"] = None
    m = detail.residual_type.eq("risk_fp")
    detail.loc[m & ~detail.e6_state.map(is_risk), "fp_timing_class"] = "resolved_by_e6"
    detail.loc[m & detail.e6_state.map(is_risk) & ~detail.e3_state.map(is_risk), "fp_timing_class"] = "resolved_by_e3"
    detail.loc[m & detail.e6_state.map(is_risk) & detail.e3_state.map(is_risk), "fp_timing_class"] = "persists_through_e3_then_resolves_by_close"

    detail["state_mismatch_class"] = None
    m = detail.residual_type.eq("within_risk_state_mismatch")
    detail.loc[m & detail.reference_e15_state.eq("UNSAFE") & detail.machine_state.eq("RECOVERING"), "state_mismatch_class"] = "reference_UNSAFE_machine_RECOVERING"
    detail.loc[m & detail.reference_e15_state.eq("RECOVERING") & detail.machine_state.eq("UNSAFE"), "state_mismatch_class"] = "reference_RECOVERING_machine_UNSAFE"
    detail["state_converges_by_e6"] = m & detail.e6_state.eq(detail.reference_e15_state)
    detail["state_converges_by_e3"] = m & detail.e3_state.eq(detail.reference_e15_state)

    detail["e15_intensity_band"] = detail.partial_shock_intensity.map(intensity_band)
    detail["final_intensity_band"] = detail.final_shock_intensity.map(intensity_band)
    return detail, boundaries


def count_map(s: pd.Series) -> dict:
    return {str(k): int(v) for k, v in s.fillna("<null>").value_counts().to_dict().items()}


def quantiles(s: pd.Series) -> dict:
    z = pd.to_numeric(s, errors="coerce").dropna()
    if z.empty:
        return {"n": 0, "p10": None, "p50": None, "p90": None, "min": None, "max": None}
    return {
        "n": int(len(z)), "p10": float(z.quantile(.1)), "p50": float(z.quantile(.5)),
        "p90": float(z.quantile(.9)), "min": float(z.min()), "max": float(z.max())
    }


def summarize_rows(x: pd.DataFrame) -> dict:
    available = x[x.checkpoint_available].copy()
    fn = available[available.residual_type.eq("risk_fn")]
    fp = available[available.residual_type.eq("risk_fp")]
    sm = available[available.residual_type.eq("within_risk_state_mismatch")]
    return {
        "candidate_rows": int(len(x)),
        "available_rows": int(len(available)),
        "risk_fn": {
            "rows": int(len(fn)),
            "timing_class": count_map(fn.fn_timing_class),
            "prev_state": count_map(fn.prev_state),
            "final_state": count_map(fn.final_state),
            "final_shock_true": int(fn.final_shock.fillna(False).astype(bool).sum()),
            "e15_partial_shock_true": int(fn.partial_shock.fillna(False).astype(bool).sum()),
            "e15_intensity_band": count_map(fn.e15_intensity_band),
            "final_intensity_band": count_map(fn.final_intensity_band),
            "e15_intensity": quantiles(fn.partial_shock_intensity),
            "final_intensity": quantiles(fn.final_shock_intensity),
        },
        "risk_fp": {
            "rows": int(len(fp)),
            "timing_class": count_map(fp.fp_timing_class),
            "prev_state": count_map(fp.prev_state),
            "final_state": count_map(fp.final_state),
            "final_shock_true": int(fp.final_shock.fillna(False).astype(bool).sum()),
            "e15_partial_shock_true": int(fp.partial_shock.fillna(False).astype(bool).sum()),
            "e15_intensity_band": count_map(fp.e15_intensity_band),
            "final_intensity_band": count_map(fp.final_intensity_band),
            "e15_intensity": quantiles(fp.partial_shock_intensity),
            "final_intensity": quantiles(fp.final_shock_intensity),
        },
        "within_risk_state_mismatch": {
            "rows": int(len(sm)),
            "class": count_map(sm.state_mismatch_class),
            "converges_by_e6": int(sm.state_converges_by_e6.sum()),
            "converges_by_e3": int(sm.state_converges_by_e3.sum()),
        },
        "exact_state_disagreement_rows": int(available.machine_state.ne(available.reference_e15_state).sum()),
    }


def episode_audit(detail: pd.DataFrame, v19) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    ref_ep, mach_ep, _ = v19.episode_tables(detail)
    if len(ref_ep):
        ref_ep["role"] = np.where(ref_ep.year <= 2023, "development", "validation")
        ref_ep["failure_kind"] = "none"
        ref_ep.loc[~ref_ep.captured, "failure_kind"] = "uncaptured"
        ref_ep.loc[ref_ep.fragmented, "failure_kind"] = "fragmented"
        causes = {}
        for ep_id, g in detail.dropna(subset=["reference_episode_id"]).groupby("reference_episode_id", sort=False):
            residuals = sorted(set(g.loc[g.residual_type.ne("correct"), "residual_type"].astype(str)))
            transitions = sorted(set(g.loc[g.residual_type.ne("correct"), "transition_class"].astype(str)))
            causes[str(ep_id)] = {"residual_types": residuals, "transition_classes": transitions}
        ref_ep["residual_types"] = ref_ep.reference_episode_id.map(lambda x: ",".join(causes.get(str(x), {}).get("residual_types", [])))
        ref_ep["transition_classes"] = ref_ep.reference_episode_id.map(lambda x: ",".join(causes.get(str(x), {}).get("transition_classes", [])))
    if len(mach_ep):
        mach_ep["role"] = np.where(mach_ep.year <= 2023, "development", "validation")
        fp_counts = detail[detail.residual_type.eq("risk_fp")].groupby("machine_episode_id").size().to_dict()
        fp_classes = detail[detail.residual_type.eq("risk_fp")].groupby("machine_episode_id").fp_timing_class.apply(lambda s: ",".join(sorted(set(s.dropna().astype(str))))).to_dict()
        mach_ep["risk_fp_rows"] = mach_ep.machine_episode_id.map(fp_counts).fillna(0).astype(int)
        mach_ep["fp_timing_classes"] = mach_ep.machine_episode_id.map(fp_classes).fillna("")

    out = {}
    for role in ("development", "validation"):
        r = ref_ep[ref_ep.role.eq(role)] if len(ref_ep) else ref_ep
        m = mach_ep[mach_ep.role.eq(role)] if len(mach_ep) else mach_ep
        unc = r[~r.captured] if len(r) else r
        frag = r[r.fragmented] if len(r) else r
        false = m[m.false_episode] if len(m) else m
        out[role] = {
            "reference_episodes": int(len(r)),
            "uncaptured_reference_episodes": int(len(unc)),
            "fragmented_reference_episodes": int(len(frag)),
            "machine_episodes": int(len(m)),
            "false_machine_episodes": int(len(false)),
            "false_episode_lengths": count_map(false.checkpoint_count.astype(str)) if len(false) else {},
            "uncaptured_residual_types": count_map(unc.residual_types) if len(unc) else {},
            "fragmented_residual_types": count_map(frag.residual_types) if len(frag) else {},
            "fragmented_transition_classes": count_map(frag.transition_classes) if len(frag) else {},
            "false_episode_fp_timing_classes": count_map(false.fp_timing_classes) if len(false) else {},
        }
    return ref_ep, mach_ep, out


def run(root: Path, out: Path) -> dict:
    v19, v9, adaptive, age_only, receipt = configure_frozen_v19()
    detail, boundaries = build_detail(root, v19, v9, adaptive, age_only)
    ref_ep, mach_ep, episodes = episode_audit(detail, v19)

    roles = {
        "development": summarize_rows(detail[detail.role.eq("development")]),
        "validation": summarize_rows(detail[detail.role.eq("validation")]),
    }
    val = roles["validation"]
    fn = detail[(detail.role.eq("validation")) & detail.residual_type.eq("risk_fn")]
    fp = detail[(detail.role.eq("validation")) & detail.residual_type.eq("risk_fp")]
    sm = detail[(detail.role.eq("validation")) & detail.residual_type.eq("within_risk_state_mismatch")]

    structural = {
        "validation_fn_all_normal_to_unsafe_final_shocks": bool(
            len(fn) > 0
            and fn.prev_state.eq("NORMAL").all()
            and fn.final_state.eq("UNSAFE").all()
            and fn.final_shock.fillna(False).astype(bool).all()
            and (~fn.partial_shock.fillna(False).astype(bool)).all()
        ),
        "validation_fp_all_transient_e15_partial_shocks_from_normal": bool(
            len(fp) > 0
            and fp.prev_state.eq("NORMAL").all()
            and fp.final_state.eq("NORMAL").all()
            and fp.partial_shock.fillna(False).astype(bool).all()
            and (~fp.final_shock.fillna(False).astype(bool)).all()
        ),
        "validation_binary_risk_errors_exhausted_by_fn_fp": bool(
            val["risk_fn"]["rows"] + val["risk_fp"]["rows"] == 99
        ),
        "validation_within_risk_mismatch_rate": float(len(sm) / val["available_rows"]) if val["available_rows"] else None,
    }

    # A new E-15 causal model is not justified when binary errors are entirely
    # threshold-crossing timing reversals and the remaining within-risk mismatch is tiny.
    no_v20 = bool(
        structural["validation_fn_all_normal_to_unsafe_final_shocks"]
        and structural["validation_fp_all_transient_e15_partial_shocks_from_normal"]
        and structural["validation_binary_risk_errors_exhausted_by_fn_fp"]
        and structural["validation_within_risk_mismatch_rate"] is not None
        and structural["validation_within_risk_mismatch_rate"] < 0.005
    )

    summary = {
        "schema": "v19_residual_failure_audit_v1",
        "diagnostic_only": True,
        "years": list(AUDIT_YEARS),
        "roles": {"development": [2021, 2022, 2023], "validation_consumed": [2024, 2025]},
        "frozen_v19_blob": EXPECTED_V19_BLOB,
        "frozen_upstream_receipt": receipt,
        "boundary_exclusions": boundaries,
        "row_diagnostics": roles,
        "episode_diagnostics": episodes,
        "structural_checks": structural,
        "decision": "NO_V20_FROM_V19_RESIDUALS" if no_v20 else "V20_HYPOTHESIS_EXISTS_BUT_NO_FRESH_REALTIME_VALIDATION_REMAINS",
        "v20_started": False,
        "threshold_search_performed": False,
        "lead_time_selection_performed": False,
        "persistence_length_search_performed": False,
        "feature_search_performed": False,
        "probability_fit_performed": False,
        "posthoc_subgroup_optimization": False,
        "queried_2026_3s": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
    }

    out.mkdir(parents=True, exist_ok=True)
    detail[detail.residual_type.ne("correct")].to_parquet(out / "residual_rows.parquet", index=False)
    ref_ep[(~ref_ep.captured) | ref_ep.fragmented].to_parquet(out / "reference_episode_failures.parquet", index=False)
    mach_ep[mach_ep.false_episode].to_parquet(out / "false_machine_episodes.parquet", index=False)
    (out / "summary.json").write_text(json.dumps(clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(clean(summary), sort_keys=True))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.repo_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
