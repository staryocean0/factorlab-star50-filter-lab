from __future__ import annotations

import numpy as np
import pandas as pd

from research.activity_degree_incremental_utility_v1.run_study import (
    AGE_BUCKETS, M3_MIN_HISTORY, SLOTS, STATES, attach_m3, design, sample_session, transition,
)


def test_strict_sampler_uniform_path_and_age():
    t = np.arange(0, 301, 3, dtype=float)
    p = np.exp(t * 1e-6)
    rows = np.arange(len(t))
    got = sample_session(t, p, rows)
    j = 300 // 15
    assert np.isfinite(got["price"][:j+1]).all()
    assert np.nanmax(got["age"][:j+1]) <= 3
    r = got["return_bp"][1:j+1]
    assert np.isfinite(r).all()
    assert np.allclose(r, r[0], rtol=0, atol=1e-12)


def test_strict_sampler_refuses_crossed_source_gap():
    t = np.r_[np.arange(0, 121, 3), np.arange(129, 301, 3)].astype(float)
    p = np.exp(t * 1e-6)
    rows = np.arange(len(t))
    got = sample_session(t, p, rows)
    # A missing >3s source interval must make at least one affected 15s return unavailable.
    assert np.isnan(got["return_bp"]).any()


def test_same_second_rows_use_stable_last_row():
    t = np.array([0, 3, 3, 6, 9, 12, 15], float)
    p = np.array([100, 101, 102, 103, 104, 105, 106], float)
    rows = np.array([1, 1, 2, 1, 1, 1, 1])
    got = sample_session(t, p, rows)
    # endpoint 15 is exact; duplicate source keys are allowed when row_index differs.
    assert got["price"][1] == 106


def test_m3_reference_is_prior_only():
    n = M3_MIN_HISTORY + 3
    base = pd.DataFrame({
        "row_id": np.arange(n),
        "symbol": ["000688.SH"] * n,
        "trading_day": pd.date_range("2021-01-01", periods=n, freq="D").strftime("%Y-%m-%d"),
        "year": [2021] * n,
        "afternoon": [0] * n,
        "slot": [600] * n,
        "decision_time": pd.date_range("2021-01-01 10:00", periods=n, freq="D"),
        "fine_complete": [True] * n,
        "pre5m_range_bp": [1.0] * n,
        "A5": np.linspace(1.0, 2.0, n),
        "partial_price": [100.0] * n,
        "endpoint_age_seconds": [0.0] * n,
    })
    a = attach_m3(base)
    changed = base.copy()
    changed.loc[n-1, "A5"] = 999999.0
    b = attach_m3(changed)
    assert np.allclose(a.M3.iloc[:-1].fillna(0), b.M3.iloc[:-1].fillna(0), rtol=0, atol=0)
    assert pd.isna(a.M3.iloc[M3_MIN_HISTORY-1])
    assert np.isfinite(a.M3.iloc[M3_MIN_HISTORY])


def _design_frame(n=20):
    rng = np.random.default_rng(1)
    q = pd.DataFrame({
        "symbol": np.resize(np.array(["000688.SH", "000852.SH"]), n),
        "slot": np.resize(np.array(SLOTS[:4]), n),
        "previous_state": np.resize(np.array(STATES), n),
        "age_bucket": np.resize(np.array(AGE_BUCKETS), n),
        "rms3": rng.uniform(0.001, 0.002, n),
        "rms6": rng.uniform(0.001, 0.002, n),
        "rms12": rng.uniform(0.001, 0.002, n),
        "rms48": rng.uniform(0.001, 0.002, n),
        "bg48": rng.uniform(0.001, 0.002, n),
        "last_abs": rng.uniform(0.0, 0.002, n),
        "shock_intensity": rng.uniform(0.0, 4.0, n),
        "vol_ratio": rng.uniform(0.5, 2.0, n),
        "M3": rng.normal(size=n),
        "M3_lag": rng.normal(size=n),
    })
    return q


def test_A_and_N_are_complexity_matched_and_add_eight_columns():
    q = _design_frame()
    c, cn = design(q, "C")
    a, an = design(q, "A")
    n, nn = design(q, "N")
    assert an == nn
    assert a.shape == n.shape
    assert a.shape[1] == c.shape[1] + 8
    assert len(an) == len(cn) + 8


def test_design_whitelist_has_no_outcome_or_current_final_fields():
    q = _design_frame()
    for model in ("C", "A", "N"):
        _, names = design(q, model)
        text = " ".join(names).lower()
        assert "future" not in text
        assert "close" not in text
        assert "final" not in text
        assert "return" not in text


def test_state_transition_frozen_thresholds():
    assert transition("NORMAL", 9.0, False) == "NORMAL"
    assert transition("NORMAL", 0.5, True) == "UNSAFE"
    assert transition("UNSAFE", 1.6, False) == "UNSAFE"
    assert transition("UNSAFE", 1.2, False) == "RECOVERING"
    assert transition("UNSAFE", 1.0, False) == "NORMAL"
    assert transition("RECOVERING", 1.6, False) == "UNSAFE"
    assert transition("RECOVERING", 1.2, False) == "RECOVERING"
    assert transition("RECOVERING", 1.0, False) == "NORMAL"
