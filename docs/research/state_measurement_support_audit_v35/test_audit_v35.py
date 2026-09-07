import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
import audit_v35 as a


def minute_panel_one_session():
    r = np.zeros(120, float)
    r[39] = 50.0
    return pd.DataFrame({
        "session": ["2024-01-02/0"] * 120,
        "day": ["2024-01-02"] * 120,
        "year": [2024] * 120,
        "minute": np.arange(1, 121),
        "afternoon": [0] * 120,
        "return_bp": r,
        "source_valid": [True] * 120,
    })


def test_past_only_state_never_creates_future_target_columns():
    z = a.past_only_minute_state(minute_panel_one_session())
    assert "target" not in z.columns
    assert "quiet_now" not in z.columns
    assert z.loc[z.minute == 40, "first_tail"].iloc[0] == 1.0


def test_first_tail_history_is_strictly_past_only():
    z = pd.DataFrame({
        "session": ["s"] * 120,
        "minute": np.arange(1, 121),
        "first_tail": [1.0 if m == 50 else 0.0 for m in range(1, 121)],
    })
    out = a.add_past_first_30m(z)
    assert not bool(out.loc[out.minute == 50, "past_first_tail_30m"].iloc[0])
    assert bool(out.loc[out.minute == 51, "past_first_tail_30m"].iloc[0])
    assert bool(out.loc[out.minute == 80, "past_first_tail_30m"].iloc[0])
    assert not bool(out.loc[out.minute == 81, "past_first_tail_30m"].iloc[0])


def synthetic_state(n=130, eval_state=(0.0, 0.0)):
    rows = []
    for i in range(n):
        rows.append({
            "year": 2022 if i < n // 2 else 2023,
            "session": f"r{i:03d}", "day": f"2022-01-{i%28+1:02d}",
            "afternoon": 0, "minute": 40, "month": "2022-01", "minute_band": "31-55",
            "log_sigma_pre": (i - n / 2) / 50.0,
            "log_rv480": ((i * 11) % n - n / 2) / 50.0,
        })
    ref = pd.DataFrame(rows)
    ev = pd.DataFrame([{
        "year": 2024, "session": "e", "day": "2024-01-02", "afternoon": 0, "minute": 40,
        "month": "2024-01", "minute_band": "31-55",
        "log_sigma_pre": eval_state[0], "log_rv480": eval_state[1],
    }])
    return ref, ev


def test_state_support_uses_reference_only_and_keeps_evaluation_row():
    ref, ev = synthetic_state()
    rt = a.group_reference(ref)
    out = a.attach_state_support(ev, ref, rt)
    assert len(out) == 1
    before = float(out.kth_neighbor_distance.iloc[0])
    # Mutating unrelated evaluation rows cannot alter a frozen reference table.
    extra = ev.copy(); extra["session"] = "extreme"; extra["log_sigma_pre"] = 999.0
    out2 = a.attach_state_support(pd.concat([ev, extra], ignore_index=True), ref, rt)
    assert np.isclose(float(out2.loc[out2.session == "e", "kth_neighbor_distance"].iloc[0]), before)


def test_extrapolated_state_is_flagged_not_dropped():
    ref, ev = synthetic_state(eval_state=(100.0, -100.0))
    rt = a.group_reference(ref)
    out = a.attach_state_support(ev, ref, rt)
    assert len(out) == 1
    assert bool(out.state_extrapolated.iloc[0])


def test_fixed_minute_bands_are_not_data_driven():
    assert a.minute_band(31) == "31-55"
    assert a.minute_band(55) == "31-55"
    assert a.minute_band(56) == "56-80"
    assert a.minute_band(80) == "56-80"
    assert a.minute_band(81) == "81-105"
    assert a.minute_band(105) == "81-105"
    assert a.minute_band(106) == "outside"


def test_measurement_summary_reports_availability_without_imputation():
    q = pd.DataFrame({
        "year": [2024] * 3, "minute": [31, 32, 33],
        "primary_scale_score": [1.0, np.nan, 2.0],
        "fine_gap3_fraction5": [0.1, np.nan, 0.3],
        "fine_max_age5": [2.0, np.nan, 3.0],
        "fine_repeat_fraction5": [0.2, np.nan, 0.4],
    })
    s = a.measurement_summary(q, ["year"]).iloc[0]
    assert np.isclose(s.primary_score_available_fraction, 2 / 3)
    assert np.isclose(s.fine_gap3_fraction5_available_fraction, 2 / 3)
    assert np.isclose(s.fine_gap3_fraction5_mean, 0.2)
