"""V3.4 historical-state conditioned gate for the frozen STAR50 V3.2 score.

This is a post-V3.3 consumed-history diagnostic. It does not fit labels or a
classifier. The only transformation is the preregistered historical conditional
percentile: within exact half-session/minute, compare the frozen primary score to
100 nearest 2022-2023 quiet decision rows in (log_sigma_pre, log_rv480).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
import precursor_existence_v32 as v32
import quiet_precursor_gate_v33 as v33

SYMBOL = "000688.SH"
CAL_YEARS = (2022, 2023)
EVAL_YEARS = (2024, 2025)
K = 100
RISK_PERCENTILE = 0.80
SUPPORT_Q = 0.99
MAX_EXTRAPOLATED_FRACTION = 0.05
MATCH_COLS = ("log_sigma_pre", "log_rv480")


def decision_frame(q: pd.DataFrame) -> pd.DataFrame:
    """Reuse V3.3 causal universe and additionally require finite rv480 state."""
    z = v33.add_causal_event_context(q)
    finite = (
        np.isfinite(z["primary_scale_score"].to_numpy(float))
        & np.isfinite(z["log_sigma_pre"].to_numpy(float))
        & np.isfinite(z["log_rv480"].to_numpy(float))
    )
    mask = (
        (z["minute"] >= v33.DECISION_MINUTE_LO)
        & (z["minute"] <= v33.DECISION_MINUTE_HI)
        & z["quiet_pre"].fillna(False).astype(bool)
        & ~(z["first"].fillna(0).to_numpy(float) == 1.0)
        & ~z["past_first_tail_30m"].fillna(False).astype(bool)
        & finite
    )
    keep = [
        "year", "day", "session", "afternoon", "minute", "primary_scale_score",
        "log_sigma_pre", "log_rv480", "quiet_first_future_2_15"
    ]
    out = z.loc[mask, keep].copy()
    out["year"] = out.year.astype(int)
    out["minute"] = out.minute.astype(int)
    out["afternoon"] = out.afternoon.astype(int)
    out["quiet_first_future_2_15"] = out.quiet_first_future_2_15.fillna(False).astype(bool)
    return out.sort_values(["year", "session", "minute"], kind="stable").reset_index(drop=True)


def _scales(cal: pd.DataFrame) -> np.ndarray:
    scale = np.std(cal[list(MATCH_COLS)].to_numpy(float), axis=0, ddof=0)
    return np.maximum(scale, 1e-8)


def _distance_rows(target: np.ndarray, cal: pd.DataFrame, scale: np.ndarray) -> np.ndarray:
    x = cal[list(MATCH_COLS)].to_numpy(float)
    return np.sqrt(np.sum(((x - target) / scale) ** 2, axis=1))


def _stable_nearest(cal: pd.DataFrame, distances: np.ndarray, k: int = K) -> pd.DataFrame:
    z = cal.copy()
    z["_distance"] = np.asarray(distances, float)
    return z.sort_values(["_distance", "year", "session", "day"], kind="stable").head(k)


def calibration_support_limits(calibration: pd.DataFrame) -> pd.DataFrame:
    """Label-free leave-one-out 100th-neighbor support limit for each exact group."""
    rows = []
    for (aft, minute), group in calibration.groupby(["afternoon", "minute"], sort=True):
        g = group.sort_values(["year", "session", "day"], kind="stable").reset_index(drop=True)
        scale = _scales(g)
        kth = []
        if len(g) >= K + 1:
            x = g[list(MATCH_COLS)].to_numpy(float)
            for i in range(len(g)):
                d = np.sqrt(np.sum(((x - x[i]) / scale) ** 2, axis=1))
                d[i] = np.inf
                kth.append(float(np.partition(d, K - 1)[K - 1]))
        limit = float(np.quantile(kth, SUPPORT_Q)) if kth else np.nan
        rows.append({
            "afternoon": int(aft),
            "minute": int(minute),
            "calibration_rows": int(len(g)),
            "sigma_scale": float(scale[0]),
            "rv480_scale": float(scale[1]),
            "support_limit_q99": limit,
            "loo_kth_distance_median": float(np.median(kth)) if kth else np.nan,
            "loo_kth_distance_max": float(np.max(kth)) if kth else np.nan,
        })
    return pd.DataFrame(rows)


def condition_evaluation(decisions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create conditional percentiles using only the frozen 2022-2023 library."""
    calibration = decisions[decisions.year.isin(CAL_YEARS)].copy()
    evaluation = decisions[decisions.year.isin(EVAL_YEARS)].copy()
    limits = calibration_support_limits(calibration)
    limit_map = limits.set_index(["afternoon", "minute"]).to_dict("index")

    groups = {
        (int(a), int(m)): z.sort_values(["year", "session", "day"], kind="stable").reset_index(drop=True)
        for (a, m), z in calibration.groupby(["afternoon", "minute"], sort=False)
    }
    rows = []
    for _, row in evaluation.iterrows():
        key = (int(row.afternoon), int(row.minute))
        cal = groups.get(key)
        if cal is None or len(cal) < K:
            continue
        scale = _scales(cal)
        target = row[list(MATCH_COLS)].to_numpy(float)
        distances = _distance_rows(target, cal, scale)
        nearest = _stable_nearest(cal, distances, K)
        kth = float(nearest["_distance"].iloc[-1])
        percentile = v32.percentile_rank(
            float(row.primary_scale_score), nearest.primary_scale_score.to_numpy(float)
        )
        meta = limit_map.get(key, {})
        support_limit = float(meta.get("support_limit_q99", np.nan))
        item = row.to_dict()
        item.update({
            "conditional_percentile": float(percentile),
            "neighbor_count": int(len(nearest)),
            "kth_neighbor_distance": kth,
            "support_limit_q99": support_limit,
            "state_extrapolated": bool(np.isfinite(support_limit) and kth > support_limit),
            "conditional_risk": bool(np.isfinite(percentile) and percentile >= RISK_PERCENTILE),
        })
        rows.append(item)
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values(["year", "session", "minute"], kind="stable").reset_index(drop=True)
    return out, limits


def attach_sigma_baseline(q: pd.DataFrame, conditioned: pd.DataFrame) -> pd.DataFrame:
    """Identity-check V3.3 sigma comparator without conditioning on rv480 availability."""
    raw = v33.decision_frame(q)
    thresholds = v33.calibrate_thresholds(raw)
    sigma = thresholds[["afternoon", "minute", "sigma_threshold_q80"]]
    z = conditioned.merge(sigma, on=["afternoon", "minute"], how="left", validate="many_to_one")
    z["sigma_gate_available"] = np.isfinite(z.sigma_threshold_q80.to_numpy(float))
    z["sigma_risk"] = z.sigma_gate_available & (z.log_sigma_pre >= z.sigma_threshold_q80)
    return z


def event_reference_median(reference: dict) -> float | None:
    q = reference.get("reference_recall_quantiles") if reference else None
    return float(q[1]) if q and len(q) == 3 else None


def evaluate_year(q: pd.DataFrame, frame: pd.DataFrame, year: int) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    part = frame[frame.year == year].copy()
    events = v33.frozen_quiet_events(q, year)
    primary_detail = v33.event_detail(part, events, "conditional_risk")
    sigma_detail = v33.event_detail(part, events, "sigma_risk")
    primary_detail["gate"] = "conditioned_primary_scale"
    sigma_detail["gate"] = "log_sigma_pre"

    primary_ref = v33.session_permutation_reference(part, events, "conditional_risk", seed=v33.SEED)
    sigma_ref = v33.session_permutation_reference(part, events, "sigma_risk", seed=v33.SEED + 1)
    primary_rows = v33.row_metrics(part, "conditional_risk", "conditional_percentile")
    sigma_rows = v33.row_metrics(part, "sigma_risk", "log_sigma_pre")
    primary_rows["state_extrapolated_rows"] = int(part.state_extrapolated.sum())
    primary_rows["state_extrapolated_fraction"] = float(part.state_extrapolated.mean()) if len(part) else None
    primary_rows["conditional_percentile_mean"] = float(part.conditional_percentile.mean()) if len(part) else None
    primary_rows["conditional_percentile_median"] = float(part.conditional_percentile.median()) if len(part) else None
    primary_rows["kth_neighbor_distance_median"] = float(part.kth_neighbor_distance.median()) if len(part) else None

    return ({
        "year": int(year),
        "conditioned_primary_scale": {
            "rows": primary_rows,
            "events": v33.summarize_events(primary_detail),
            "session_permutation_reference": primary_ref,
        },
        "common_volatility_baseline": {
            "rows": sigma_rows,
            "events": v33.summarize_events(sigma_detail),
            "session_permutation_reference": sigma_ref,
        },
    }, primary_detail, sigma_detail)


def candidate_rule(summary: dict) -> dict:
    checks = []
    for year in EVAL_YEARS:
        z = summary["by_year"][str(year)]["conditioned_primary_scale"]
        rows = z["rows"]
        ref = z["session_permutation_reference"]
        events = z["events"]
        median_ref = event_reference_median(ref)
        checks.append({
            "year": int(year),
            "positive_risk_difference": rows.get("risk_difference_pp") is not None and rows["risk_difference_pp"] > 0,
            "auc_above_half": rows.get("continuous_auc") is not None and rows["continuous_auc"] > 0.5,
            "event_recall_not_below_reference_median": (
                events.get("event_recall") is not None and median_ref is not None
                and events["event_recall"] >= median_ref
            ),
            "state_support_ok": (
                rows.get("state_extrapolated_fraction") is not None
                and rows["state_extrapolated_fraction"] <= MAX_EXTRAPOLATED_FRACTION
            ),
        })
    passed = all(all(v for k, v in c.items() if k != "year") for c in checks)
    return {
        "candidate_for_future_locked_validation": bool(passed),
        "checks": checks,
        "if_passed": "freeze this exact candidate and wait for explicitly authorized truly new-period validation",
        "if_failed": "stop this V3.2 scale-score route without parameter scanning on 2024/2025",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.repo_root.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("immutable output directory")
    out.mkdir(parents=True, exist_ok=True)

    q, source_audit = v32.build_symbol_frame(root, SYMBOL)
    decisions = decision_frame(q)
    conditioned, support_limits = condition_evaluation(decisions)
    conditioned = attach_sigma_baseline(q, conditioned)

    support_limits.to_csv(out / "conditioning_support_limits.csv", index=False)
    summary = {
        "schema": "first_shock_conditioned_precursor_gate_v3.4_results",
        "symbol": SYMBOL,
        "historical_conditioning_years": list(CAL_YEARS),
        "evaluation_years": list(EVAL_YEARS),
        "neighbor_count": K,
        "risk_percentile": RISK_PERCENTILE,
        "conditioning_dimensions": list(MATCH_COLS),
        "labels_used_in_conditioning": False,
        "classifier_fit": False,
        "new_morphology_feature_defined": False,
        "fresh_oos": False,
        "read_2026": False,
        "by_year": {},
        "trading_or_production_evaluated": False,
    }
    for year in EVAL_YEARS:
        s, p, b = evaluate_year(q, conditioned, year)
        summary["by_year"][str(year)] = s
        p.to_csv(out / f"{year}_conditioned_event_details.csv", index=False)
        b.to_csv(out / f"{year}_sigma_event_details.csv", index=False)
    summary["decision_rule"] = candidate_rule(summary)

    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "source_audit.json").write_text(json.dumps(source_audit, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
