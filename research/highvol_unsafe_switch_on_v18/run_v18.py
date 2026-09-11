from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
REF_YEARS = (2020, 2021, 2022, 2023)
DEV_YEARS = (2021, 2022, 2023)
SOURCE_STATES = ("NORMAL", "RECOVERING")
LEADS = (60, 30, 15, 6, 3)
PRIMARY_LEAD = 15
FROZEN_V9_BLOB = "ae2a7e095df58692ef9df0dfee5856cac727ca44"

HERE = Path(__file__).resolve().parent
FROZEN_V9 = HERE / "frozen_v9.py"


def load_v9():
    got = subprocess.check_output(["git", "hash-object", str(FROZEN_V9)], text=True).strip()
    if got != FROZEN_V9_BLOB:
        raise RuntimeError(f"frozen V9 blob drift: {got}")
    spec = importlib.util.spec_from_file_location("v18_frozen_v9", FROZEN_V9)
    if spec is None or spec.loader is None:
        raise RuntimeError(FROZEN_V9)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SYMBOLS = SYMBOLS
    mod.REF_YEARS = REF_YEARS
    mod.DEV_YEARS = DEV_YEARS
    if (mod.RV_WINDOW, mod.BG_WINDOW, mod.HIGHVOL_RATIO, mod.RECOVERY_NORMAL_RATIO, mod.SHOCK_SIGMA) != (12, 48, 1.5, 1.1, 3.0):
        raise RuntimeError("V9 state constants drift")
    return mod


def candidate_rows(v9, ref: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    windows = v9.prior_windows(ref)
    base = ref[ref.year.isin(DEV_YEARS) & ref.prev_state.isin(SOURCE_STATES)].copy()
    boundary = {
        "source_state_rows_before_reference_guard": int(len(base)),
        "missing_prior_window": int(sum(int(i) not in windows for i in base.index)),
        "missing_prev_close": int(base.prev_close.isna().sum()),
        "missing_bg_vol48": int(base.bg_vol48.isna().sum()),
    }
    ok = pd.Series([int(i) in windows for i in base.index], index=base.index)
    ok &= base.prev_close.notna() & base.bg_vol48.notna()
    z = base[ok].copy()
    z["global_idx"] = z.index.astype(int)
    z["source_state"] = z.prev_state.astype(str)
    z["final_state"] = z.risk_state.astype(str)
    z["final_switch_on"] = z.final_state.eq("UNSAFE")
    z["final_shock"] = z.shock.fillna(False).astype(bool)
    z["switch_pathway"] = np.where(
        ~z.final_switch_on,
        "control",
        np.where(z.final_shock, "shock_entry", "recovery_reescalation"),
    )
    z["candidate_id"] = (
        z.symbol.astype(str) + "|" + z.trading_day.astype(str) + "|" + z.bar_end.astype(str)
    )
    cols = [
        "candidate_id", "symbol", "year", "trading_day", "global_idx", "bar_end",
        "source_state", "final_state", "final_switch_on", "final_shock", "vol_ratio",
        "shock_intensity", "switch_pathway", "prev_close", "bg_vol48",
    ]
    return z[cols].reset_index(drop=True), boundary


def attach_checkpoint(v9, root: Path, ref: pd.DataFrame, candidates: pd.DataFrame, symbol: str, lead: int) -> pd.DataFrame:
    windows = v9.prior_windows(ref)
    obs_day = {}
    for year in DEV_YEARS:
        sec = v9.load_3s(root, symbol, year)
        for day, g in sec.groupby("trading_day", sort=False):
            obs_day[(year, str(day))] = g.reset_index(drop=True)

    out = []
    for r in candidates[candidates.symbol.eq(symbol)].itertuples(index=False):
        row = r._asdict()
        row["lead_seconds"] = int(lead)
        idx = int(r.global_idx)
        rr = ref.loc[idx]
        sec = obs_day.get((int(r.year), str(r.trading_day)), pd.DataFrame())
        target = pd.Timestamp(r.bar_end) - pd.Timedelta(seconds=lead)
        start = pd.Timestamp(r.bar_end) - pd.Timedelta(minutes=5)
        sel = v9.select_checkpoint(sec, start, target)
        if sel is None:
            row.update({
                "checkpoint_available": False,
                "selected_observation_time": pd.NaT,
                "staleness_seconds": np.nan,
                "partial_state": None,
                "partial_shock": False,
                "partial_vol_ratio": np.nan,
                "partial_shock_intensity": np.nan,
                "switch_on_signal": False,
                "unavailable_reason": "missing_3s_checkpoint",
            })
            out.append(row)
            continue
        price, obs_time = sel
        pret = float(np.log(price) - np.log(float(rr.prev_close)))
        prv = float(np.std(np.concatenate([windows[idx], [pret]]), ddof=0))
        ratio = prv / float(rr.bg_vol48)
        intensity = abs(pret) / float(rr.bg_vol48)
        pshock = bool(intensity >= v9.SHOCK_SIGMA)
        pstate = v9.transition(str(rr.prev_state), ratio, pshock)
        row.update({
            "checkpoint_available": True,
            "selected_observation_time": obs_time,
            "staleness_seconds": float((target - obs_time).total_seconds()),
            "partial_state": pstate,
            "partial_shock": pshock,
            "partial_vol_ratio": ratio,
            "partial_shock_intensity": intensity,
            "switch_on_signal": bool(pstate == "UNSAFE"),
            "unavailable_reason": "",
        })
        out.append(row)
    return pd.DataFrame(out)


def qstats(s: pd.Series) -> dict:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:
        return {"n": 0, "p50": None, "p90": None, "max": None}
    return {
        "n": int(len(x)),
        "p50": float(x.quantile(0.50)),
        "p90": float(x.quantile(0.90)),
        "max": float(x.max()),
    }


def summarize(x: pd.DataFrame, group_type: str, group_value: str) -> dict:
    y = x.final_switch_on.astype(bool)
    sig = x.switch_on_signal.astype(bool)
    available = x.checkpoint_available.astype(bool)
    tp = int((y & sig).sum())
    fp = int((~y & sig).sum())
    fn = int(y.sum()) - tp
    tn = int((~y).sum()) - fp
    precision = float(tp / (tp + fp)) if tp + fp else None
    recall = float(tp / (tp + fn)) if tp + fn else None
    fpr = float(fp / (fp + tn)) if fp + tn else None
    specificity = float(tn / (fp + tn)) if fp + tn else None
    tp_rows = x[y & sig]
    fp_rows = x[(~y) & sig]
    return {
        "group_type": group_type,
        "group_value": str(group_value),
        "candidate_rows": int(len(x)),
        "checkpoint_available_rows": int(available.sum()),
        "checkpoint_coverage": float(available.mean()) if len(x) else None,
        "true_switch_on_events": int(y.sum()),
        "switch_on_prevalence": float(y.mean()) if len(x) else None,
        "signal_rows": int(sig.sum()),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision,
        "recall": recall,
        "false_positive_rate": fpr,
        "specificity": specificity,
        "tp_partial_shock_rate": float(tp_rows.partial_shock.mean()) if len(tp_rows) else None,
        "fp_partial_shock_rate": float(fp_rows.partial_shock.mean()) if len(fp_rows) else None,
        "tp_partial_vol_ratio": qstats(tp_rows.partial_vol_ratio),
        "fp_partial_vol_ratio": qstats(fp_rows.partial_vol_ratio),
        "missing_checkpoint_rows": int((~available).sum()),
    }


def evidence_curve(detail: pd.DataFrame, candidates: pd.DataFrame) -> dict:
    pivot = detail.pivot(index="candidate_id", columns="lead_seconds", values="switch_on_signal").reindex(columns=LEADS).fillna(False).astype(bool)
    targets = candidates[candidates.final_switch_on].set_index("candidate_id")
    p = pivot.reindex(targets.index).fillna(False)
    earliest = {}
    persistent = 0
    detected = 0
    late_after_15 = 0
    for cid, row in p.iterrows():
        hits = [lead for lead in LEADS if bool(row[lead])]
        if not hits:
            earliest[cid] = None
            continue
        first = hits[0]
        earliest[cid] = first
        detected += 1
        later = [lead for lead in LEADS if lead <= first]
        if all(bool(row[lead]) for lead in later):
            persistent += 1
        if not bool(row[15]) and (bool(row[6]) or bool(row[3])):
            late_after_15 += 1
    counts = {str(lead): int(sum(v == lead for v in earliest.values())) for lead in LEADS}
    counts["undetected"] = int(sum(v is None for v in earliest.values()))
    cumulative = {str(lead): float(p[lead].mean()) if len(p) else None for lead in LEADS}
    return {
        "true_switch_on_events": int(len(targets)),
        "detected_at_any_checkpoint": int(detected),
        "earliest_detection_counts": counts,
        "checkpoint_detection_fraction": cumulative,
        "persistent_after_first_detection_rate": float(persistent / detected) if detected else None,
        "late_forming_first_after_e15_count": int(late_after_15),
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
    v9 = load_v9()
    refs = {s: v9.load_reference(root, s) for s in SYMBOLS}
    candidate_parts = []
    boundary = {}
    for s in SYMBOLS:
        c, b = candidate_rows(v9, refs[s])
        candidate_parts.append(c)
        boundary[s] = b
    candidates = pd.concat(candidate_parts, ignore_index=True)
    if candidates.candidate_id.duplicated().any():
        raise RuntimeError("candidate_id collision")

    detail_parts = []
    for lead in LEADS:
        for s in SYMBOLS:
            detail_parts.append(attach_checkpoint(v9, root, refs[s], candidates, s, lead))
    detail = pd.concat(detail_parts, ignore_index=True)

    pooled_by_lead = {}
    for lead in LEADS:
        z = detail[detail.lead_seconds.eq(lead)]
        pooled_by_lead[str(lead)] = summarize(z, "pooled", "pooled")

    primary = detail[detail.lead_seconds.eq(PRIMARY_LEAD)].copy()
    yearly = {str(y): summarize(primary[primary.year.eq(y)], "year", y) for y in DEV_YEARS}
    by_symbol = {s: summarize(primary[primary.symbol.eq(s)], "symbol", s) for s in SYMBOLS}
    by_source_state = {s: summarize(primary[primary.source_state.eq(s)], "source_state", s) for s in SOURCE_STATES}
    pathway_counts = candidates[candidates.final_switch_on].switch_pathway.value_counts().to_dict()
    curve = evidence_curve(detail, candidates)

    p = pooled_by_lead[str(PRIMARY_LEAD)]
    acceptance = {
        "pooled_candidate_rows_ge_30000": p["candidate_rows"] >= 30000,
        "pooled_true_switch_on_events_ge_300": p["true_switch_on_events"] >= 300,
        "each_year_true_switch_on_events_ge_50": all(yearly[str(y)]["true_switch_on_events"] >= 50 for y in DEV_YEARS),
        "pooled_checkpoint_coverage_ge_098": p["checkpoint_coverage"] >= 0.98,
        "each_year_checkpoint_coverage_ge_095": all(yearly[str(y)]["checkpoint_coverage"] >= 0.95 for y in DEV_YEARS),
        "pooled_precision_ge_090": p["precision"] is not None and p["precision"] >= 0.90,
        "pooled_recall_ge_080": p["recall"] is not None and p["recall"] >= 0.80,
        "pooled_false_positive_rate_le_001": p["false_positive_rate"] is not None and p["false_positive_rate"] <= 0.01,
        "each_year_precision_ge_085": all(yearly[str(y)]["precision"] is not None and yearly[str(y)]["precision"] >= 0.85 for y in DEV_YEARS),
        "each_year_recall_ge_070": all(yearly[str(y)]["recall"] is not None and yearly[str(y)]["recall"] >= 0.70 for y in DEV_YEARS),
        "each_year_false_positive_rate_le_002": all(yearly[str(y)]["false_positive_rate"] is not None and yearly[str(y)]["false_positive_rate"] <= 0.02 for y in DEV_YEARS),
        "both_symbols_have_true_events_and_true_positives": all(by_symbol[s]["true_switch_on_events"] > 0 and by_symbol[s]["tp"] > 0 for s in SYMBOLS),
        "frozen_v9_runner_and_thresholds_unchanged": True,
        "threshold_search_performed_false": True,
        "feature_search_performed_false": True,
        "probability_fit_performed_false": True,
        "lead_time_selection_performed_false": True,
        "posthoc_subgroup_selection_false": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }

    summary = {
        "schema": "highvol_unsafe_switch_on_v18_development_v1",
        "development_only": True,
        "development_period": ["2021-01-01", "2023-12-31"],
        "symbols": list(SYMBOLS),
        "source_states": list(SOURCE_STATES),
        "fixed_leads_seconds": list(LEADS),
        "primary_lead_seconds": PRIMARY_LEAD,
        "frozen_v9_runner_blob": FROZEN_V9_BLOB,
        "candidate_rows": int(len(candidates)),
        "boundary_exclusions": boundary,
        "true_switch_on_events": int(candidates.final_switch_on.sum()),
        "switch_pathway_counts": pathway_counts,
        "pooled_by_lead": pooled_by_lead,
        "primary_yearly": yearly,
        "primary_by_symbol": by_symbol,
        "primary_by_source_state": by_source_state,
        "evidence_curve": curve,
        "threshold_search_performed": False,
        "feature_search_performed": False,
        "probability_fit_performed": False,
        "lead_time_selection_performed": False,
        "posthoc_subgroup_selection": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
        "acceptance": acceptance,
        "development_supported": bool(all(acceptance.values())),
        "validation_eligible_but_not_authorized": bool(all(acceptance.values())),
    }

    out.mkdir(parents=True, exist_ok=True)
    candidates.to_parquet(out / "candidate_rows.parquet", index=False)
    detail.to_parquet(out / "checkpoint_detail.parquet", index=False)
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
