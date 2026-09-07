"""V3.3 STAR50 e-2 single-score fixed-risk-budget gate feasibility.

The score and quiet-first taxonomy are inherited from V3.2. Thresholds are
unsupervised quantiles of *all eligible market opportunities* in 2022-2023;
2024 and 2025 are evaluated sequentially without retuning. No 2026, returns,
P&L, trading labels, or event-conditioned threshold search are permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
RESEARCH = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import precursor_existence_v32 as v32

SYMBOL = "000688.SH"
CALIBRATION_YEARS = (2022, 2023)
EVALUATION_YEARS = (2024, 2025)
BUDGETS = (0.10, 0.20, 0.30)
PRIMARY_BUDGET = 0.20
QUANTILE_METHOD = "higher"
SCORE_FORMULA = "0.5*((logE30-logE240)+(logE60-logE240))"
PROTOCOL_RELATIVE = Path("docs/research/first_shock_morphology_v3/V33_FROZEN_PROTOCOL.md")


def _json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def write_json(path: Path, payload) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def budget_label(budget: float) -> str:
    return f"{int(round(100 * budget))}pct"


def time_stratum(target_minute: int) -> str:
    if 33 <= int(target_minute) <= 60:
        return "early_post_warmup"
    if int(target_minute) > 60:
        return "ordinary"
    return "outside_scope"


def build_opportunities(q: pd.DataFrame) -> pd.DataFrame:
    """Build label-free causal opportunity universe.

    Selection uses only session clock/support and the already-fixed score. Future
    event labels, quiet_pre, and near_first_tail are deliberately not referenced.
    """
    rows = []
    for session, z in q.groupby("session", sort=False):
        valid_minutes = {int(x) for x in z.minute.dropna().to_numpy()}
        for ix, row in z.iterrows():
            if pd.isna(row.minute):
                continue
            minute = int(row.minute)
            target_minute = minute + 2
            if minute < 31 or target_minute not in valid_minutes:
                continue
            score = float(row.primary_scale_score) if pd.notna(row.primary_scale_score) else np.nan
            if not np.isfinite(score):
                continue
            rows.append({
                "row_ix": int(ix),
                "year": int(row.year),
                "day": row.day,
                "session": session,
                "feature_minute": minute,
                "target_minute": target_minute,
                "time_stratum": time_stratum(target_minute),
                "primary_scale_score": score,
            })
    return pd.DataFrame(rows)


def calibrate_thresholds(opportunities: pd.DataFrame) -> dict:
    cal = opportunities[opportunities.year.isin(CALIBRATION_YEARS)].copy()
    scores = cal.primary_scale_score.to_numpy(float)
    scores = scores[np.isfinite(scores)]
    if not len(scores):
        raise RuntimeError("no finite calibration opportunities")
    thresholds = {}
    for budget in BUDGETS:
        threshold = float(np.quantile(scores, 1.0 - budget, method=QUANTILE_METHOD))
        realized = float(np.mean(scores >= threshold))
        thresholds[budget_label(budget)] = {
            "nominal_budget": budget,
            "threshold": threshold,
            "calibration_realized_flagged_share": realized,
        }
    return {
        "symbol": SYMBOL,
        "calibration_years": list(CALIBRATION_YEARS),
        "calibration_opportunities": int(len(scores)),
        "score_formula": SCORE_FORMULA,
        "quantile_method": QUANTILE_METHOD,
        "thresholds": thresholds,
        "event_labels_used_for_calibration": False,
    }


def build_quiet_first_events(q: pd.DataFrame) -> pd.DataFrame:
    """Return all in-scope 2024/2025 quiet-first events, preserving Unknown."""
    records = []
    for ix, row in q.iterrows():
        if int(row.year) not in EVALUATION_YEARS:
            continue
        if pd.isna(row["first"]) or float(row["first"]) != 1.0:
            continue
        quiet = row.get("quiet_pre")
        if pd.isna(quiet) or not bool(quiet):
            continue
        if pd.isna(row.minute) or int(row.minute) < 33:
            continue
        event_minute = int(row.minute)
        feature_minute = event_minute - 2
        f = q[(q.session == row.session) & (q.minute == feature_minute)]
        score = np.nan
        feature_row_ix = None
        if len(f) == 1:
            feature_row_ix = int(f.index[0])
            raw = f.iloc[0].primary_scale_score
            if pd.notna(raw):
                score = float(raw)
        evaluable = bool(np.isfinite(score))
        records.append({
            "event_row_ix": int(ix),
            "feature_row_ix": feature_row_ix,
            "symbol": SYMBOL,
            "year": int(row.year),
            "day": row.day,
            "session": row.session,
            "event_minute": event_minute,
            "feature_minute": feature_minute,
            "time_stratum": time_stratum(event_minute),
            "primary_scale_score": score,
            "evaluable": evaluable,
            "unknown": not evaluable,
        })
    return pd.DataFrame(records)


def apply_flags(frame: pd.DataFrame, calibration: dict, score_col: str = "primary_scale_score") -> pd.DataFrame:
    z = frame.copy()
    score = z[score_col].to_numpy(float) if len(z) else np.array([], dtype=float)
    finite = np.isfinite(score)
    for label, spec in calibration["thresholds"].items():
        threshold = float(spec["threshold"])
        z[f"flag_{label}"] = finite & (score >= threshold)
    return z


def _subset_stratum(frame: pd.DataFrame, stratum: str) -> pd.DataFrame:
    return frame if stratum == "all" else frame[frame.time_stratum == stratum]


def opportunity_coverage(opportunities: pd.DataFrame, calibration: dict) -> pd.DataFrame:
    flagged = apply_flags(opportunities, calibration)
    periods = [
        ("calibration_2022_2023", CALIBRATION_YEARS),
        ("2024", (2024,)),
        ("2025", (2025,)),
        ("2024_2025", EVALUATION_YEARS),
    ]
    rows = []
    for period, years in periods:
        base = flagged[flagged.year.isin(years)]
        for stratum in ("all", "early_post_warmup", "ordinary"):
            part = _subset_stratum(base, stratum)
            n = len(part)
            for budget in BUDGETS:
                label = budget_label(budget)
                count = int(part[f"flag_{label}"].sum()) if n else 0
                rows.append({
                    "period": period,
                    "time_stratum": stratum,
                    "nominal_budget": budget,
                    "threshold": float(calibration["thresholds"][label]["threshold"]),
                    "eligible_opportunities": int(n),
                    "flagged_opportunities": count,
                    "realized_flagged_time_share": float(count / n) if n else np.nan,
                })
    return pd.DataFrame(rows)


def budget_summary(events: pd.DataFrame, coverage: pd.DataFrame, calibration: dict) -> pd.DataFrame:
    flagged_events = apply_flags(events, calibration)
    periods = [("2024", (2024,)), ("2025", (2025,)), ("2024_2025", EVALUATION_YEARS)]
    rows = []
    for period, years in periods:
        event_base = flagged_events[flagged_events.year.isin(years)]
        for stratum in ("all", "early_post_warmup", "ordinary"):
            ev = _subset_stratum(event_base, stratum)
            all_events = int(len(ev))
            evaluable = int(ev.evaluable.sum()) if all_events else 0
            unknown = int(ev.unknown.sum()) if all_events else 0
            for budget in BUDGETS:
                label = budget_label(budget)
                flagged = int(ev[f"flag_{label}"].sum()) if all_events else 0
                cov = coverage[
                    (coverage.period == period)
                    & (coverage.time_stratum == stratum)
                    & np.isclose(coverage.nominal_budget, budget)
                ]
                if len(cov) != 1:
                    raise RuntimeError(f"coverage identity failure: {period}/{stratum}/{budget}")
                share = float(cov.iloc[0].realized_flagged_time_share)
                recall_eval = float(flagged / evaluable) if evaluable else np.nan
                recall_cons = float(flagged / all_events) if all_events else np.nan
                lift = float(recall_cons / share) if np.isfinite(recall_cons) and share > 0 else np.nan
                rows.append({
                    "period": period,
                    "time_stratum": stratum,
                    "nominal_budget": budget,
                    "threshold": float(calibration["thresholds"][label]["threshold"]),
                    "eligible_opportunities": int(cov.iloc[0].eligible_opportunities),
                    "realized_flagged_time_share": share,
                    "quiet_first_events_all": all_events,
                    "quiet_first_events_evaluable": evaluable,
                    "quiet_first_events_unknown": unknown,
                    "flagged_quiet_first_events": flagged,
                    "recall_evaluable": recall_eval,
                    "recall_conservative": recall_cons,
                    "lift_vs_time_share": lift,
                    "clean_time_share": float(1.0 - share) if np.isfinite(share) else np.nan,
                    "clean_event_leakage": float(1.0 - recall_cons) if np.isfinite(recall_cons) else np.nan,
                })
    return pd.DataFrame(rows)


def primary_decision(summary: pd.DataFrame) -> dict:
    row = summary[
        (summary.period == "2024_2025")
        & (summary.time_stratum == "all")
        & np.isclose(summary.nominal_budget, PRIMARY_BUDGET)
    ]
    if len(row) != 1:
        raise RuntimeError("primary summary row missing")
    r = row.iloc[0]
    recall = float(r.recall_conservative) if pd.notna(r.recall_conservative) else np.nan
    lift = float(r.lift_vs_time_share) if pd.notna(r.lift_vs_time_share) else np.nan
    if not np.isfinite(recall) or not np.isfinite(lift):
        status = "insufficient_evaluable_evidence"
    elif lift <= 1.0:
        status = "single_score_gate_not_supported"
    elif recall < 0.40 or lift < 2.0:
        status = "weak_descriptive_only"
    else:
        status = "prospective_confirmation_candidate_only"
    return {
        "primary_budget": PRIMARY_BUDGET,
        "status": status,
        "recall_conservative": recall,
        "realized_flagged_time_share": float(r.realized_flagged_time_share),
        "lift_vs_time_share": lift,
        "quiet_first_events_all": int(r.quiet_first_events_all),
        "quiet_first_events_unknown": int(r.quiet_first_events_unknown),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--research-ref", default=os.getenv("RESEARCH_REF", "unknown"))
    args = ap.parse_args()
    root = args.repo_root.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("immutable output directory")
    out.mkdir(parents=True, exist_ok=True)

    q, audits = v32.build_symbol_frame(root, SYMBOL)
    opportunities = build_opportunities(q)
    calibration = calibrate_thresholds(opportunities)
    events = build_quiet_first_events(q)
    events_flagged = apply_flags(events, calibration)
    coverage = opportunity_coverage(opportunities, calibration)
    summary_table = budget_summary(events, coverage, calibration)
    decision = primary_decision(summary_table)

    thresholds_path = out / "calibration_thresholds_v33.json"
    coverage_path = out / "opportunity_coverage_v33.csv"
    events_path = out / "quiet_first_event_gate_v33.csv"
    budget_path = out / "budget_summary_v33.csv"
    summary_path = out / "summary_v33.json"
    receipt_path = out / "run_receipt_v33.json"

    write_json(thresholds_path, calibration)
    coverage.to_csv(coverage_path, index=False)
    events_flagged.to_csv(events_path, index=False)
    summary_table.to_csv(budget_path, index=False)
    summary_payload = {
        "status": "completed STAR50 e-2 single-score fixed-budget feasibility diagnostic",
        "symbol": SYMBOL,
        "calibration_years": list(CALIBRATION_YEARS),
        "evaluation_years": list(EVALUATION_YEARS),
        "score_formula": SCORE_FORMULA,
        "thresholds": calibration["thresholds"],
        "primary_decision": decision,
        "in_scope_quiet_first_events_2024_2025": int(len(events)),
        "unknown_events_2024_2025": int(events.unknown.sum()) if len(events) else 0,
        "scope_limit": "score requires 30-minute scale; first 30 minutes after each half-session open are outside this gate's claim",
        "fresh_oos": False,
        "results_blind_gate_thresholds": True,
        "returns_or_pnl_evaluated": False,
        "production_authority": False,
    }
    write_json(summary_path, summary_payload)

    output_hashes = {
        p.name: file_sha256(p)
        for p in (thresholds_path, coverage_path, events_path, budget_path, summary_path)
    }
    protocol_path = root / PROTOCOL_RELATIVE
    receipt = {
        "schema": "star50_e2_single_score_gate_v33@1.0",
        "research_ref": args.research_ref,
        "v32_parent_result_commit": "e638ed1b92f5e5e8e2816c31d851b1604f64e5bc",
        "v32_code_commit": "5574f862068295a2b00a8e2bcc545ceb713216bd",
        "v32_test_commit": "3fd0a038f2f93827011e8f53cc92a94241243f00",
        "symbol": SYMBOL,
        "input_years": [2022, 2023, 2024, 2025],
        "source_audits": audits,
        "score_formula": SCORE_FORMULA,
        "calibration_years": list(CALIBRATION_YEARS),
        "evaluation_years": list(EVALUATION_YEARS),
        "budgets": list(BUDGETS),
        "primary_budget": PRIMARY_BUDGET,
        "quantile_method": QUANTILE_METHOD,
        "event_labels_used_for_threshold_calibration": False,
        "protocol_path": str(PROTOCOL_RELATIVE),
        "protocol_sha256": file_sha256(protocol_path),
        "runner_sha256": file_sha256(HERE),
        "outputs": output_hashes,
        "fresh_oos": False,
        "results_blind_gate_thresholds": True,
        "returns_or_pnl_evaluated": False,
        "trading_evaluated": False,
        "production_authority": False,
    }
    write_json(receipt_path, receipt)
    print(json.dumps(summary_payload, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
