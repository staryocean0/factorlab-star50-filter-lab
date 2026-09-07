import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "code"))
import quiet_precursor_gate_v33 as g


def _base_session(first_minutes=(), quiet_first_minutes=()):
    rows = []
    for m in range(1, 121):
        rows.append({
            "year": 2024,
            "day": "2024-01-02",
            "session": "2024-01-02/0",
            "afternoon": 0,
            "minute": m,
            "first": 1.0 if m in first_minutes else 0.0,
            "quiet_pre": True if m in quiet_first_minutes or m not in first_minutes else False,
            "primary_scale_score": float(m) / 100.0,
            "log_sigma_pre": float(m) / 200.0,
        })
    return pd.DataFrame(rows)


def test_past_first_marker_is_causal_not_future():
    q = _base_session(first_minutes=(50,), quiet_first_minutes=(50,))
    z = g.add_causal_event_context(q)
    assert not bool(z.loc[z.minute == 49, "past_first_tail_30m"].iloc[0])
    assert bool(z.loc[z.minute == 51, "past_first_tail_30m"].iloc[0])
    assert bool(z.loc[z.minute == 80, "past_first_tail_30m"].iloc[0])
    assert not bool(z.loc[z.minute == 81, "past_first_tail_30m"].iloc[0])


def test_future_label_starts_at_t_plus_2_not_t_plus_1():
    q = _base_session(first_minutes=(50,), quiet_first_minutes=(50,))
    z = g.add_causal_event_context(q)
    assert bool(z.loc[z.minute == 48, "quiet_first_future_2_15"].iloc[0])
    assert not bool(z.loc[z.minute == 49, "quiet_first_future_2_15"].iloc[0])
    assert bool(z.loc[z.minute == 35, "quiet_first_future_2_15"].iloc[0])
    assert not bool(z.loc[z.minute == 34, "quiet_first_future_2_15"].iloc[0])


def test_calibration_thresholds_use_only_2022_2023_and_groupwise_q80():
    rows = []
    for year, values in ((2022, range(100)), (2023, range(100, 200)), (2024, range(1000, 1100))):
        for v in values:
            rows.append({"year": year, "afternoon": 0, "minute": 31,
                         "primary_scale_score": float(v), "log_sigma_pre": float(v),
                         "quiet_first_future_2_15": False})
    d = pd.DataFrame(rows)
    t = g.calibrate_thresholds(d)
    assert len(t) == 1
    expected = pd.Series(np.arange(200, dtype=float)).quantile(0.8)
    assert t.calibration_rows.iloc[0] == 200
    assert np.isclose(t.primary_threshold_q80.iloc[0], expected)
    assert np.isclose(t.sigma_threshold_q80.iloc[0], expected)


def test_event_detail_uses_strict_e_minus_15_to_e_minus_2_window():
    decisions = pd.DataFrame({
        "year": [2024] * 4,
        "day": ["2024-01-02"] * 4,
        "session": ["2024-01-02/0"] * 4,
        "afternoon": [0] * 4,
        "minute": [35, 40, 48, 49],
        "primary_risk": [False, True, True, True],
    })
    events = pd.DataFrame({
        "event_id": ["x"], "year": [2024], "day": ["2024-01-02"],
        "session": ["2024-01-02/0"], "afternoon": [0], "event_minute": [50]
    })
    d = g.event_detail(decisions, events, "primary_risk")
    # minute 49 is e-1 and must not count; earliest flagged eligible minute is 40 -> lead 10.
    assert bool(d.hit.iloc[0])
    assert d.max_strict_lead_minutes.iloc[0] == 10
    assert d.available_prewindow_points.iloc[0] == 3


def test_alarm_segments_respect_session_and_minute_gaps():
    d = pd.DataFrame({
        "session": ["a", "a", "a", "a", "b"],
        "minute": [31, 32, 34, 35, 31],
        "risk": [True, True, True, False, True],
    })
    assert g.alarm_segments(d, "risk") == 3


def test_rank_auc_ties_and_direction():
    y = np.array([0, 0, 1, 1], dtype=bool)
    assert np.isclose(g.roc_auc_rank(y, np.array([0.0, 1.0, 2.0, 3.0])), 1.0)
    assert np.isclose(g.roc_auc_rank(y, np.array([3.0, 2.0, 1.0, 0.0])), 0.0)
