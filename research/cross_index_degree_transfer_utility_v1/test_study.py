from __future__ import annotations

import numpy as np
import pandas as pd

from research.cross_index_degree_transfer_utility_v1.run_study import (
    MODELS, SYMBOLS, design, other_symbol, pair_other, select_snapshot,
)


def _frame(n=24):
    rng = np.random.default_rng(7)
    q = pd.DataFrame({
        "symbol": np.resize(np.array(SYMBOLS), n),
        "slot": np.resize(np.array([575, 580, 585, 590]), n),
        "previous_state": np.resize(np.array(["NORMAL", "UNSAFE", "RECOVERING"]), n),
        "age_bucket": np.resize(np.array(["NONE", "LT15", "M15_25", "M30_40", "GE45"]), n),
        "rms3": rng.uniform(.001, .003, n),
        "rms6": rng.uniform(.001, .003, n),
        "rms12": rng.uniform(.001, .003, n),
        "rms48": rng.uniform(.001, .003, n),
        "bg48": rng.uniform(.001, .003, n),
        "last_abs": rng.uniform(0, .003, n),
        "shock_intensity": rng.uniform(0, 4, n),
        "vol_ratio": rng.uniform(.5, 2, n),
        "other_shock_intensity": rng.uniform(0, 4, n),
        "other_vol_ratio": rng.uniform(.5, 2, n),
        "other_lag_intensity": rng.uniform(0, 4, n),
        "other_lag_ratio": rng.uniform(.5, 2, n),
    })
    return q


def test_counterpart_mapping_is_bidirectional():
    assert other_symbol("000688.SH") == "000852.SH"
    assert other_symbol("000852.SH") == "000688.SH"


def test_snapshot_uses_latest_stable_row_inside_bar():
    obs = pd.DataFrame({
        "obs_dt": pd.to_datetime(["2023-01-03 10:00:00", "2023-01-03 10:04:42", "2023-01-03 10:04:45", "2023-01-03 10:04:45"]),
        "price": [99.0, 100.0, 101.0, 102.0],
        "row_index": [1, 2, 3, 4],
    })
    # Caller data are stable-sorted by obs_dt,row_index; search-right chooses last same-second row.
    got = select_snapshot(obs, pd.Timestamp("2023-01-03 10:00:00"), pd.Timestamp("2023-01-03 10:04:45"))
    assert got is not None
    assert got[0] == 102.0 and got[2] == 4.0
    assert select_snapshot(obs.iloc[:1], pd.Timestamp("2023-01-03 10:00:01"), pd.Timestamp("2023-01-03 10:04:45")) is None


def test_X_and_L_are_complexity_matched_with_15_extra_columns():
    q = _frame()
    c, cn = design(q, "C")
    x, xn = design(q, "X")
    l, ln = design(q, "L")
    assert xn == ln
    assert x.shape == l.shape
    assert x.shape[1] == c.shape[1] + 15
    assert len(xn) == len(cn) + 15


def test_other_current_perturbation_changes_X_not_C_or_L():
    q = _frame()
    c0, _ = design(q, "C")
    x0, _ = design(q, "X")
    l0, _ = design(q, "L")
    changed = q.copy()
    changed.loc[:, "other_shock_intensity"] *= 1.7
    changed.loc[:, "other_vol_ratio"] *= 1.2
    c1, _ = design(changed, "C")
    x1, _ = design(changed, "X")
    l1, _ = design(changed, "L")
    assert np.array_equal(c0, c1)
    assert np.array_equal(l0, l1)
    assert not np.array_equal(x0, x1)


def test_other_lag_perturbation_changes_L_not_C_or_X():
    q = _frame()
    c0, _ = design(q, "C")
    x0, _ = design(q, "X")
    l0, _ = design(q, "L")
    changed = q.copy()
    changed.loc[:, "other_lag_intensity"] *= 1.7
    changed.loc[:, "other_lag_ratio"] *= 1.2
    c1, _ = design(changed, "C")
    x1, _ = design(changed, "X")
    l1, _ = design(changed, "L")
    assert np.array_equal(c0, c1)
    assert np.array_equal(x0, x1)
    assert not np.array_equal(l0, l1)


def test_pair_other_requires_exact_same_bar_and_decision():
    t = pd.Timestamp("2023-01-03 10:05:00")
    d = t - pd.Timedelta(seconds=15)
    frame = pd.DataFrame({
        "symbol": list(SYMBOLS), "trading_day": ["2023-01-03"] * 2,
        "bar_end": [t, t], "decision_time": [d, d],
        "shock_intensity": [1.0, 2.0], "vol_ratio": [1.1, 1.2],
        "lag_intensity": [.8, .9], "lag_ratio": [1.0, 1.05],
        "base_available": [True, True], "lag_available": [True, True],
        "observation_time": [d, d], "observation_age_seconds": [0.0, 0.0],
    })
    paired = pair_other(frame)
    a = paired[paired.symbol.eq("000688.SH")].iloc[0]
    assert a.other_shock_intensity == 2.0
    assert bool(a.paired_available)


def test_design_names_contain_no_outcome_or_final_current_close():
    q = _frame()
    for model in MODELS:
        _, names = design(q, model)
        text = " ".join(names).lower()
        assert "future" not in text
        assert "close" not in text
        assert "final" not in text
