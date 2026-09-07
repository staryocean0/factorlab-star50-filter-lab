import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "code"))
import single_score_gate_v33 as v33


def test_opportunity_universe_requires_same_session_t_plus_2_and_ignores_labels():
    q = pd.DataFrame({
        "session": ["d/0"] * 4,
        "year": [2022] * 4,
        "day": ["d"] * 4,
        "minute": [31, 32, 33, 34],
        "primary_scale_score": [1.0, 2.0, 3.0, 4.0],
        "first": [1.0, 0.0, 1.0, 0.0],
        "quiet_pre": [False, True, False, True],
    })
    out = v33.build_opportunities(q)
    assert out.feature_minute.tolist() == [31, 32]
    assert out.target_minute.tolist() == [33, 34]
    assert "first" not in out.columns and "quiet_pre" not in out.columns


def test_unsupervised_budget_thresholds_are_empirical_higher_quantiles():
    q = pd.DataFrame({
        "year": [2022] * 50 + [2023] * 50,
        "primary_scale_score": np.arange(100, dtype=float),
    })
    result = v33.calibrate_thresholds(q)
    assert result["event_labels_used_for_calibration"] is False
    assert result["thresholds"]["10pct"]["threshold"] == 90.0
    assert result["thresholds"]["20pct"]["threshold"] == 80.0
    assert result["thresholds"]["30pct"]["threshold"] == 70.0


def test_unknown_quiet_first_event_is_retained_in_conservative_denominator():
    q = pd.DataFrame([
        {"session": "2024-01-02/0", "year": 2024, "day": "2024-01-02", "minute": 48,
         "first": 0.0, "quiet_pre": True, "primary_scale_score": np.nan},
        {"session": "2024-01-02/0", "year": 2024, "day": "2024-01-02", "minute": 50,
         "first": 1.0, "quiet_pre": True, "primary_scale_score": 999.0},
    ])
    events = v33.build_quiet_first_events(q)
    assert len(events) == 1
    assert events.feature_minute.iloc[0] == 48
    assert not bool(events.evaluable.iloc[0])
    assert bool(events.unknown.iloc[0])


def test_budget_summary_counts_unknown_as_unflagged_conservatively():
    calibration = {"thresholds": {
        "10pct": {"threshold": 9.0},
        "20pct": {"threshold": 5.0},
        "30pct": {"threshold": 1.0},
    }}
    events = pd.DataFrame([
        {"year": 2024, "time_stratum": "ordinary", "primary_scale_score": 10.0,
         "evaluable": True, "unknown": False},
        {"year": 2024, "time_stratum": "ordinary", "primary_scale_score": np.nan,
         "evaluable": False, "unknown": True},
    ])
    rows = []
    for period in ("2024", "2025", "2024_2025"):
        for stratum in ("all", "early_post_warmup", "ordinary"):
            for budget in v33.BUDGETS:
                rows.append({"period": period, "time_stratum": stratum,
                             "nominal_budget": budget, "threshold": 0.0,
                             "eligible_opportunities": 100,
                             "flagged_opportunities": 20,
                             "realized_flagged_time_share": 0.20})
    coverage = pd.DataFrame(rows)
    summary = v33.budget_summary(events, coverage, calibration)
    row = summary[(summary.period == "2024") & (summary.time_stratum == "all") &
                  np.isclose(summary.nominal_budget, 0.20)].iloc[0]
    assert row.quiet_first_events_all == 2
    assert row.quiet_first_events_evaluable == 1
    assert row.quiet_first_events_unknown == 1
    assert row.flagged_quiet_first_events == 1
    assert row.recall_evaluable == 1.0
    assert row.recall_conservative == 0.5
    assert row.lift_vs_time_share == 2.5


def test_primary_decision_only_survives_as_future_confirmation_candidate():
    summary = pd.DataFrame([{
        "period": "2024_2025", "time_stratum": "all", "nominal_budget": 0.20,
        "recall_conservative": 0.50, "realized_flagged_time_share": 0.20,
        "lift_vs_time_share": 2.5, "quiet_first_events_all": 16,
        "quiet_first_events_unknown": 0,
    }])
    decision = v33.primary_decision(summary)
    assert decision["status"] == "prospective_confirmation_candidate_only"
