"""V3.3 full-universe gate test for the frozen STAR50 V3.2 precursor score.

No classifier is fitted and no new morphology feature is defined. 2022-2023
only calibrate time-of-day 80th-percentile thresholds; 2024 and 2025 are then
scored unchanged. Missing fine-path measurements remain unavailable.
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

SYMBOL = "000688.SH"
CAL_YEARS = (2022, 2023)
EVAL_YEARS = (2024, 2025)
DECISION_MINUTE_LO = 31
DECISION_MINUTE_HI = 105
FUTURE_LO = 2
FUTURE_HI = 15
PAST_FIRST_LOOKBACK = 30
CAL_QUANTILE = 0.80
MIN_CAL_ROWS = 100
RANDOM_REPEATS = 5000
SEED = 20260908


def _bool_series(s: pd.Series) -> pd.Series:
    return s.fillna(False).astype(bool)


def add_causal_event_context(q: pd.DataFrame) -> pd.DataFrame:
    """Add past-only first-tail context and the fixed future quiet-first label."""
    z = q.copy()
    z["past_first_tail_30m"] = False
    z["quiet_first_future_2_15"] = False
    quiet = _bool_series(z["quiet_pre"])
    first = z["first"].fillna(0).to_numpy(float) == 1.0

    for _, ix0 in z.groupby("session", sort=False).groups.items():
        ix = np.asarray(ix0)
        part = z.loc[ix]
        minutes = part["minute"].to_numpy(int)
        first_local = first[ix]
        quiet_local = quiet.loc[ix].to_numpy(bool)

        past = np.zeros(len(ix), dtype=bool)
        first_pos = np.flatnonzero(first_local)
        for j in first_pos:
            m0 = minutes[j]
            past |= (minutes > m0) & (minutes <= m0 + PAST_FIRST_LOOKBACK)
        z.loc[ix, "past_first_tail_30m"] = past

        quiet_event_minutes = minutes[first_local & quiet_local]
        future = np.zeros(len(ix), dtype=bool)
        for j, m in enumerate(minutes):
            if len(quiet_event_minutes):
                future[j] = bool(np.any((quiet_event_minutes >= m + FUTURE_LO) &
                                        (quiet_event_minutes <= m + FUTURE_HI)))
        z.loc[ix, "quiet_first_future_2_15"] = future
    return z


def decision_frame(q: pd.DataFrame) -> pd.DataFrame:
    z = add_causal_event_context(q)
    finite = np.isfinite(z["primary_scale_score"].to_numpy(float)) & np.isfinite(z["log_sigma_pre"].to_numpy(float))
    mask = (
        (z["minute"] >= DECISION_MINUTE_LO)
        & (z["minute"] <= DECISION_MINUTE_HI)
        & _bool_series(z["quiet_pre"])
        & ~(z["first"].fillna(0).to_numpy(float) == 1.0)
        & ~_bool_series(z["past_first_tail_30m"])
        & finite
    )
    keep = [
        "year", "day", "session", "afternoon", "minute", "primary_scale_score",
        "log_sigma_pre", "quiet_first_future_2_15"
    ]
    out = z.loc[mask, keep].copy()
    out["year"] = out["year"].astype(int)
    out["minute"] = out["minute"].astype(int)
    out["afternoon"] = out["afternoon"].astype(int)
    out["quiet_first_future_2_15"] = _bool_series(out["quiet_first_future_2_15"])
    return out.sort_values(["year", "session", "minute"], kind="stable").reset_index(drop=True)


def calibrate_thresholds(decisions: pd.DataFrame) -> pd.DataFrame:
    cal = decisions[decisions.year.isin(CAL_YEARS)].copy()
    rows = []
    for (aft, minute), part in cal.groupby(["afternoon", "minute"], sort=True):
        n = len(part)
        rows.append({
            "afternoon": int(aft),
            "minute": int(minute),
            "calibration_rows": int(n),
            "primary_threshold_q80": float(part.primary_scale_score.quantile(CAL_QUANTILE)) if n >= MIN_CAL_ROWS else np.nan,
            "sigma_threshold_q80": float(part.log_sigma_pre.quantile(CAL_QUANTILE)) if n >= MIN_CAL_ROWS else np.nan,
        })
    return pd.DataFrame(rows)


def attach_gates(decisions: pd.DataFrame, thresholds: pd.DataFrame) -> pd.DataFrame:
    z = decisions.merge(thresholds, on=["afternoon", "minute"], how="left", validate="many_to_one")
    z["primary_gate_available"] = np.isfinite(z.primary_threshold_q80.to_numpy(float))
    z["sigma_gate_available"] = np.isfinite(z.sigma_threshold_q80.to_numpy(float))
    z["primary_risk"] = z.primary_gate_available & (z.primary_scale_score >= z.primary_threshold_q80)
    z["sigma_risk"] = z.sigma_gate_available & (z.log_sigma_pre >= z.sigma_threshold_q80)
    return z


def roc_auc_rank(labels: np.ndarray, scores: np.ndarray) -> float | None:
    y = np.asarray(labels, bool)
    x = np.asarray(scores, float)
    ok = np.isfinite(x)
    y = y[ok]
    x = x[ok]
    n1 = int(y.sum())
    n0 = int((~y).sum())
    if n1 == 0 or n0 == 0:
        return None
    ranks = pd.Series(x).rank(method="average").to_numpy(float)
    u = float(ranks[y].sum() - n1 * (n1 + 1) / 2)
    return u / (n1 * n0)


def alarm_segments(part: pd.DataFrame, flag_col: str) -> int:
    total = 0
    for _, s in part.groupby("session", sort=False):
        s = s.sort_values("minute", kind="stable")
        minute = s.minute.to_numpy(int)
        flag = s[flag_col].to_numpy(bool)
        prev_flag = False
        prev_minute = None
        for m, f in zip(minute, flag):
            if f and (not prev_flag or prev_minute is None or m != prev_minute + 1):
                total += 1
            prev_flag = bool(f)
            prev_minute = int(m)
    return int(total)


def row_metrics(part: pd.DataFrame, flag_col: str, score_col: str) -> dict:
    z = part.copy()
    y = z.quiet_first_future_2_15.to_numpy(bool)
    risk = z[flag_col].to_numpy(bool)
    clean = ~risk
    p_all = float(y.mean()) if len(y) else None
    p_risk = float(y[risk].mean()) if risk.any() else None
    p_clean = float(y[clean].mean()) if clean.any() else None
    diff_pp = (p_risk - p_clean) * 100 if p_risk is not None and p_clean is not None else None
    rr = p_risk / p_clean if p_risk is not None and p_clean not in (None, 0.0) else None
    return {
        "rows": int(len(z)),
        "positive_rows": int(y.sum()),
        "label_rate": p_all,
        "risk_rows": int(risk.sum()),
        "risk_coverage": float(risk.mean()) if len(risk) else None,
        "risk_label_rate": p_risk,
        "clean_label_rate": p_clean,
        "risk_difference_pp": diff_pp,
        "risk_ratio": rr,
        "continuous_auc": roc_auc_rank(y, z[score_col].to_numpy(float)),
        "alarm_segments": alarm_segments(z, flag_col),
    }


def frozen_quiet_events(q: pd.DataFrame, year: int) -> pd.DataFrame:
    mask = (
        (q.year == year)
        & (q["first"].fillna(0).to_numpy(float) == 1.0)
        & _bool_series(q["quiet_pre"])
        & (q.minute >= 33)
    )
    e = q.loc[mask, ["year", "day", "session", "afternoon", "minute"]].copy()
    e = e.rename(columns={"minute": "event_minute"})
    e["year"] = e.year.astype(int)
    e["afternoon"] = e.afternoon.astype(int)
    e["event_minute"] = e.event_minute.astype(int)
    e["event_id"] = [f"{SYMBOL}/{s}/{m}" for s, m in zip(e.session, e.event_minute)]
    return e.reset_index(drop=True)


def event_detail(decisions: pd.DataFrame, events: pd.DataFrame, flag_col: str) -> pd.DataFrame:
    rows = []
    by_session = {s: z.sort_values("minute", kind="stable") for s, z in decisions.groupby("session", sort=False)}
    for _, event in events.iterrows():
        e = int(event.event_minute)
        lo = max(DECISION_MINUTE_LO, e - FUTURE_HI)
        hi = min(DECISION_MINUTE_HI, e - FUTURE_LO)
        expected = max(0, hi - lo + 1)
        s = by_session.get(event.session, decisions.iloc[0:0])
        pre = s[(s.minute >= lo) & (s.minute <= hi)] if expected else s.iloc[0:0]
        flagged = pre[pre[flag_col].astype(bool)] if len(pre) else pre
        hit = bool(len(flagged))
        max_lead = int((e - flagged.minute).max()) if hit else None
        rows.append({
            "event_id": event.event_id,
            "year": int(event.year),
            "day": event.day,
            "session": event.session,
            "afternoon": int(event.afternoon),
            "event_minute": e,
            "expected_prewindow_points": int(expected),
            "available_prewindow_points": int(len(pre)),
            "prewindow_support_fraction": float(len(pre) / expected) if expected else None,
            "complete_prewindow": bool(expected > 0 and len(pre) == expected),
            "hit": hit,
            "max_strict_lead_minutes": max_lead,
        })
    return pd.DataFrame(rows)


def summarize_events(detail: pd.DataFrame) -> dict:
    eligible = detail[detail.available_prewindow_points > 0].copy()
    complete = eligible[eligible.complete_prewindow].copy()
    hit = eligible[eligible.hit]
    return {
        "all_frozen_quiet_events": int(len(detail)),
        "events_with_any_eligible_prewindow": int(len(eligible)),
        "event_recall": float(eligible.hit.mean()) if len(eligible) else None,
        "hit_events": int(eligible.hit.sum()) if len(eligible) else 0,
        "median_max_strict_lead_minutes": float(hit.max_strict_lead_minutes.median()) if len(hit) else None,
        "mean_prewindow_support_fraction": float(eligible.prewindow_support_fraction.mean()) if len(eligible) else None,
        "complete_prewindow_events": int(len(complete)),
        "complete_prewindow_recall": float(complete.hit.mean()) if len(complete) else None,
        "complete_prewindow_hit_events": int(complete.hit.sum()) if len(complete) else 0,
    }


def session_permutation_reference(decisions: pd.DataFrame, events: pd.DataFrame, flag_col: str,
                                  repeats: int = RANDOM_REPEATS, seed: int = SEED) -> dict:
    detail = event_detail(decisions, events, flag_col)
    eligible_events = detail[detail.available_prewindow_points > 0].copy()
    if eligible_events.empty:
        return {"status": "no_eligible_events"}
    observed = float(eligible_events.hit.mean())

    seq = {}
    valid_minutes = {}
    for session, s in decisions.groupby("session", sort=False):
        seq[session] = {int(m): bool(f) for m, f in zip(s.minute, s[flag_col])}
        valid_minutes[session] = set(int(m) for m in s.minute)

    session_meta = decisions[["session", "year", "afternoon"]].drop_duplicates()
    pools = {}
    for (year, aft), p in session_meta.groupby(["year", "afternoon"], sort=False):
        pools[(int(year), int(aft))] = list(p.session)

    rng = np.random.default_rng(seed)
    ref = np.empty(repeats, dtype=float)
    for r in range(repeats):
        mapping = {}
        for key, sessions in pools.items():
            perm = rng.permutation(sessions)
            mapping.update({target: source for target, source in zip(sessions, perm)})
        hits = 0
        for _, event in eligible_events.iterrows():
            target = event.session
            source = mapping[target]
            e = int(event.event_minute)
            lo = max(DECISION_MINUTE_LO, e - FUTURE_HI)
            hi = min(DECISION_MINUTE_HI, e - FUTURE_LO)
            hit = False
            for m in range(lo, hi + 1):
                if m in valid_minutes[target] and seq[source].get(m, False):
                    hit = True
                    break
            hits += int(hit)
        ref[r] = hits / len(eligible_events)
    return {
        "status": "computed",
        "repeats": int(repeats),
        "eligible_events": int(len(eligible_events)),
        "observed_event_recall": observed,
        "reference_recall_quantiles": [float(x) for x in np.quantile(ref, [0.025, 0.5, 0.975])],
        "fraction_reference_recall_gte_observed_descriptive": float(np.mean(ref >= observed)),
    }


def evaluate_year(q: pd.DataFrame, gated: pd.DataFrame, year: int) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    part = gated[gated.year == year].copy()
    part = part[part.primary_gate_available & part.sigma_gate_available].copy()
    events = frozen_quiet_events(q, year)
    primary_detail = event_detail(part, events, "primary_risk")
    sigma_detail = event_detail(part, events, "sigma_risk")
    primary_detail["gate"] = "primary_scale"
    sigma_detail["gate"] = "log_sigma_pre"
    summary = {
        "year": int(year),
        "primary_scale": {
            "rows": row_metrics(part, "primary_risk", "primary_scale_score"),
            "events": summarize_events(primary_detail),
            "session_permutation_reference": session_permutation_reference(part, events, "primary_risk"),
        },
        "common_volatility_baseline": {
            "rows": row_metrics(part, "sigma_risk", "log_sigma_pre"),
            "events": summarize_events(sigma_detail),
            "session_permutation_reference": session_permutation_reference(part, events, "sigma_risk", seed=SEED + 1),
        },
    }
    return summary, primary_detail, sigma_detail


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
    thresholds = calibrate_thresholds(decisions)
    gated = attach_gates(decisions, thresholds)

    thresholds.to_csv(out / "calibration_thresholds.csv", index=False)
    summary = {
        "schema": "first_shock_quiet_precursor_gate_v3.3_results",
        "symbol": SYMBOL,
        "calibration_years": list(CAL_YEARS),
        "evaluation_years": list(EVAL_YEARS),
        "calibration_uses_labels": False,
        "frozen_primary_score": "0.5*((logE30-logE240)+(logE60-logE240))",
        "risk_quantile": CAL_QUANTILE,
        "decision_minutes": [DECISION_MINUTE_LO, DECISION_MINUTE_HI],
        "future_event_window": [FUTURE_LO, FUTURE_HI],
        "calibration_rows": int(decisions.year.isin(CAL_YEARS).sum()),
        "threshold_groups": int(len(thresholds)),
        "threshold_groups_available": int((thresholds.calibration_rows >= MIN_CAL_ROWS).sum()),
        "by_year": {},
        "fresh_oos": False,
        "classifier_fit": False,
        "new_morphology_feature_defined": False,
        "read_2026": False,
        "trading_or_production_evaluated": False,
    }
    all_details = []
    for year in EVAL_YEARS:
        s, p, b = evaluate_year(q, gated, year)
        summary["by_year"][str(year)] = s
        all_details.extend([p, b])
        p.to_csv(out / f"{year}_primary_event_details.csv", index=False)
        b.to_csv(out / f"{year}_sigma_event_details.csv", index=False)

    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "source_audit.json").write_text(json.dumps(source_audit, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
