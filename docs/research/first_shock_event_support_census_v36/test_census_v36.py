import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
import census_v36 as c


def one_session_with_shock(shock_minute=40):
    r = np.zeros(120, float)
    r[shock_minute - 1] = 50.0
    return pd.DataFrame({
        "session": ["2024-01-02/0"] * 120,
        "day": ["2024-01-02"] * 120,
        "year": [2024] * 120,
        "minute": np.arange(1, 121),
        "afternoon": [0] * 120,
        "return_bp": r,
        "source_valid": [True] * 120,
    })


def test_frozen_v1_first_tail_definition_has_no_future_target():
    z = c.past_only_state(one_session_with_shock(40))
    assert "target" not in z.columns
    assert z.loc[z.minute == 40, "tail_event"].iloc[0] == 1.0
    assert z.loc[z.minute == 40, "first_tail"].iloc[0] == 1.0
    assert z.loc[z.minute == 39, "first_tail"].iloc[0] == 0.0


def synthetic_reference(n=130, minute=48):
    rows = []
    for i in range(n):
        rows.append({
            "year": 2022 if i < n // 2 else 2023,
            "day": f"2022-01-{i % 28 + 1:02d}",
            "session": f"r{i:03d}",
            "afternoon": 0,
            "minute": minute,
            "log_sigma_pre": (i - n / 2) / 50.0,
            "log_rv480": ((i * 11) % n - n / 2) / 50.0,
        })
    return pd.DataFrame(rows)


def test_state_support_has_no_clock_fallback():
    ref = synthetic_reference(minute=48)
    meta = c.reference_table(ref)
    ev = pd.DataFrame([
        {"year": 2024, "day": "2024-01-02", "session": "e48", "afternoon": 0, "minute": 48,
         "log_sigma_pre": 0.0, "log_rv480": 0.0},
        {"year": 2024, "day": "2024-01-02", "session": "e49", "afternoon": 0, "minute": 49,
         "log_sigma_pre": 0.0, "log_rv480": 0.0},
    ])
    out = c.attach_eval_state(ev, ref, meta)
    assert set(out.session) == {"e48"}
    assert 0.0 <= out.sigma_pct.iloc[0] <= 1.0
    assert 0.0 <= out.rv480_pct.iloc[0] <= 1.0


def test_support_class_and_fixed_upper_bins():
    assert c.support_class(True, True, True) == "both_supported"
    assert c.support_class(False, True, True) == "target_extrapolated_only"
    assert c.support_class(True, False, True) == "peer_extrapolated_only"
    assert c.support_class(False, False, True) == "both_extrapolated"
    assert c.support_class(np.nan, True, False) == "peer_or_target_state_unavailable"
    assert c.upper_state_bin(0.50) == "q00_50"
    assert c.upper_state_bin(0.80) == "q50_80"
    assert c.upper_state_bin(0.95) == "q80_95"
    assert c.upper_state_bin(0.951) == "q95_100"


def test_peer_tail_proximity_is_exact_plus_minus_two_and_expost_only():
    peer = pd.DataFrame({
        "day": ["2024-01-02"] * 3,
        "afternoon": [0] * 3,
        "minute": [47, 52, 53],
        "tail_event": [0.0, 1.0, 1.0],
    })
    assert c.peer_tail_nearby(peer, "2024-01-02", 0, 50) is True
    peer.loc[peer.minute == 52, "tail_event"] = 0.0
    assert c.peer_tail_nearby(peer, "2024-01-02", 0, 50) is False


def test_event_state_mapping_uses_e_minus_2_not_e_minus_1():
    target = pd.DataFrame({
        "year": [2024], "day": ["2024-01-02"], "session": ["2024-01-02/0"],
        "afternoon": [0], "minute": [50], "first_tail": [1.0], "tail_event": [1.0]
    })
    peer = pd.DataFrame({
        "year": [2024], "day": ["2024-01-02"], "session": ["2024-01-02/0"],
        "afternoon": [0], "minute": [50], "first_tail": [0.0], "tail_event": [0.0]
    })
    paired = pd.DataFrame({
        "year": [2024, 2024], "day": ["2024-01-02", "2024-01-02"], "afternoon": [0, 0],
        "minute": [48, 49],
        "s0_session": ["2024-01-02/0"] * 2, "s1_session": ["2024-01-02/0"] * 2,
        "s0_state_supported": [True, False], "s1_state_supported": [True, False],
        "s0_sigma_pct": [0.2, 0.99], "s0_rv480_pct": [0.3, 0.99],
        "s1_sigma_pct": [0.4, 0.99], "s1_rv480_pct": [0.5, 0.99],
        "s0_kth_neighbor_distance": [1.0, 9.0], "s1_kth_neighbor_distance": [1.0, 9.0],
        "s0_support_limit_q99": [2.0, 2.0], "s1_support_limit_q99": [2.0, 2.0],
        "_merge": ["both", "both"],
    })
    out = c.build_event_table({"000688.SH": target, "000852.SH": peer}, paired)
    row = out[out.target_symbol == "000688.SH"].iloc[0]
    assert row.state_minute_e_minus_2 == 48
    assert row.support_class == "both_supported"
    assert np.isclose(row.joint_upper_state_rank, 0.5)
    assert bool(row.ordinary_common_state)


def make_events(symbol, year, n, ordinary=True, isolated=True):
    return pd.DataFrame({
        "target_symbol": [symbol] * n,
        "year": [year] * n,
        "ordinary_isolated_first_tail": [bool(ordinary and isolated)] * n,
    })


def test_downstream_admission_requires_ten_in_each_year_separately():
    good = pd.concat([
        make_events("000688.SH", 2024, 10), make_events("000688.SH", 2025, 12),
        make_events("000852.SH", 2024, 9), make_events("000852.SH", 2025, 20),
    ], ignore_index=True)
    result = c.admission(good)
    by_symbol = {x["target_symbol"]: x for x in result["target_checks"]}
    assert by_symbol["000688.SH"]["model_free_residual_precursor_existence_may_open"] is True
    assert by_symbol["000852.SH"]["model_free_residual_precursor_existence_may_open"] is False
    assert result["classifier_or_gate_model"] == "prohibited"
