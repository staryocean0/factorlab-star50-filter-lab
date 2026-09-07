import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "code"))
import conditioned_precursor_gate_v34 as g


def synthetic_decisions(n_cal=120, eval_state=(0.0, 0.0), eval_score=0.75, minute=40):
    rows = []
    for i in range(n_cal):
        year = 2022 if i < n_cal // 2 else 2023
        rows.append({
            "year": year,
            "day": f"{year}-01-{(i % 28) + 1:02d}",
            "session": f"{year}-s{i:03d}",
            "afternoon": 0,
            "minute": minute,
            "primary_scale_score": i / max(1, n_cal - 1),
            "log_sigma_pre": (i - n_cal / 2) / 100.0,
            "log_rv480": ((i * 7) % n_cal - n_cal / 2) / 100.0,
            "quiet_first_future_2_15": bool(i % 11 == 0),
        })
    rows.append({
        "year": 2024,
        "day": "2024-06-01",
        "session": "2024-eval",
        "afternoon": 0,
        "minute": minute,
        "primary_scale_score": eval_score,
        "log_sigma_pre": eval_state[0],
        "log_rv480": eval_state[1],
        "quiet_first_future_2_15": True,
    })
    return pd.DataFrame(rows)


def test_conditioning_uses_only_2022_2023_and_exact_group():
    d = synthetic_decisions()
    # Add an evaluation-year row with an extreme score/state that must never enter the neighbor library.
    extra = d.iloc[[-1]].copy()
    extra["year"] = 2025
    extra["session"] = "2025-extreme"
    extra["primary_scale_score"] = 999.0
    extra["log_sigma_pre"] = 999.0
    extra["log_rv480"] = 999.0
    d = pd.concat([d, extra], ignore_index=True)
    out, limits = g.condition_evaluation(d)
    row = out[out.session == "2024-eval"].iloc[0]
    assert row.neighbor_count == 100
    assert 0.0 <= row.conditional_percentile <= 1.0
    assert len(limits) == 1
    assert int(limits.calibration_rows.iloc[0]) == 120


def test_no_clock_group_fallback():
    d = synthetic_decisions(minute=40)
    extra = d.iloc[[-1]].copy()
    extra["minute"] = 41
    extra["session"] = "2024-no-group"
    d = pd.concat([d, extra], ignore_index=True)
    out, _ = g.condition_evaluation(d)
    assert "2024-eval" in set(out.session)
    assert "2024-no-group" not in set(out.session)


def test_label_changes_do_not_change_conditioned_score_or_gate():
    d = synthetic_decisions()
    out1, _ = g.condition_evaluation(d)
    d2 = d.copy()
    d2["quiet_first_future_2_15"] = ~d2.quiet_first_future_2_15.astype(bool)
    out2, _ = g.condition_evaluation(d2)
    a = out1[out1.session == "2024-eval"].iloc[0]
    b = out2[out2.session == "2024-eval"].iloc[0]
    assert np.isclose(a.conditional_percentile, b.conditional_percentile)
    assert bool(a.conditional_risk) == bool(b.conditional_risk)
    assert np.isclose(a.kth_neighbor_distance, b.kth_neighbor_distance)


def test_state_extrapolation_is_flagged_but_not_dropped():
    d = synthetic_decisions(eval_state=(100.0, -100.0))
    out, limits = g.condition_evaluation(d)
    row = out[out.session == "2024-eval"].iloc[0]
    assert np.isfinite(limits.support_limit_q99.iloc[0])
    assert bool(row.state_extrapolated)
    assert row.session == "2024-eval"


def test_midrank_percentile_is_inherited_from_v32():
    controls = np.array([0.0, 1.0, 1.0, 2.0])
    assert np.isclose(g.v32.percentile_rank(1.0, controls), 0.5)


def _year_block(diff, auc, recall, ref_median, extrap):
    return {
        "conditioned_primary_scale": {
            "rows": {"risk_difference_pp": diff, "continuous_auc": auc,
                     "state_extrapolated_fraction": extrap},
            "events": {"event_recall": recall},
            "session_permutation_reference": {
                "reference_recall_quantiles": [0.0, ref_median, 1.0]
            },
        }
    }


def test_candidate_rule_requires_both_years_and_support():
    good = {"by_year": {
        "2024": _year_block(0.1, 0.6, 0.5, 0.4, 0.01),
        "2025": _year_block(0.2, 0.55, 1.0, 0.5, 0.05),
    }}
    assert g.candidate_rule(good)["candidate_for_future_locked_validation"] is True
    bad = {"by_year": {
        "2024": _year_block(0.1, 0.6, 0.5, 0.4, 0.01),
        "2025": _year_block(-0.01, 0.49, 0.5, 0.5, 0.01),
    }}
    assert g.candidate_rule(bad)["candidate_for_future_locked_validation"] is False
