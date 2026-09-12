from __future__ import annotations

import numpy as np
import pandas as pd

from research.degree_trajectory_utility_v1 import run_study as s


def lag_frame(n=20):
    r = np.linspace(-0.02, 0.03, n)
    return pd.DataFrame({
        "symbol": ["000688.SH"] * n,
        "r": r,
        "bg48": np.full(n, 0.01),
    })


def design_frame():
    return pd.DataFrame({
        "symbol": ["000688.SH", "000852.SH", "000688.SH"],
        "slot": [600, 600, 605],
        "previous_state": ["NORMAL", "UNSAFE", "RECOVERING"],
        "age_bucket": ["NONE", "LT15", "M15_25"],
        "rms3": [0.01, 0.012, 0.011],
        "rms6": [0.011, 0.013, 0.012],
        "rms12": [0.012, 0.014, 0.013],
        "rms48": [0.013, 0.015, 0.014],
        "bg48": [0.01, 0.011, 0.012],
        "last_abs": [0.005, 0.007, 0.006],
        "shock_intensity": [0.5, 1.5, 2.0],
        "vol_ratio": [0.9, 1.4, 1.2],
        "lag_intensity": [0.4, 1.1, 1.7],
        "lag_ratio": [0.8, 1.2, 1.1],
        "lag2_intensity": [0.3, 0.9, 1.4],
        "lag2_ratio": [0.7, 1.0, 1.0],
    })


def test_lag2_excludes_current_and_previous_valid_return():
    a = lag_frame()
    z1 = s.attach_lag2(a)
    i = 15
    expected_abs = abs(a.loc[i - 2, "r"])
    expected_std = a.loc[1:i - 2, "r"].tail(12).std(ddof=0)
    assert np.isclose(z1.loc[i, "lag2_abs"], expected_abs)
    assert np.isclose(z1.loc[i, "lag2_std12"], expected_std)

    b = a.copy()
    b.loc[i, "r"] = 100.0
    z2 = s.attach_lag2(b)
    assert z2.loc[i, "lag2_abs"] == z1.loc[i, "lag2_abs"]
    assert z2.loc[i, "lag2_std12"] == z1.loc[i, "lag2_std12"]


def test_delta_raw_identity_is_exact_to_roundoff():
    q = design_frame()
    z = s.attach_deltas(q)
    np.testing.assert_allclose(z.shock_intensity - z.delta1_intensity, z.lag_intensity, rtol=0, atol=1e-15)
    np.testing.assert_allclose(z.vol_ratio - z.delta1_ratio, z.lag_ratio, rtol=0, atol=1e-15)
    np.testing.assert_allclose(z.shock_intensity - z.delta2_intensity, z.lag2_intensity, rtol=0, atol=1e-15)
    np.testing.assert_allclose(z.vol_ratio - z.delta2_ratio, z.lag2_ratio, rtol=0, atol=1e-15)


def test_T_and_O_are_exact_complexity_matches():
    q = design_frame()
    xc, nc = s.design(q, "C")
    xt, nt = s.design(q, "T")
    xo, no = s.design(q, "O")
    assert nt == no
    assert xt.shape == xo.shape
    assert xt.shape[1] == xc.shape[1] + 20
    assert nt[: len(nc)] == nc
    assert xc.shape[1] == 84
    assert xt.shape[1] == 104


def test_design_names_exclude_current_final_and_future_fields():
    q = design_frame()
    for model in s.MODELS:
        _, names = s.design(q, model)
        joined = " ".join(names).lower()
        for forbidden in ("future", "close", "final", "return", "sigma_"):
            assert forbidden not in joined


def test_cohort_uses_common_trajectory_rows_and_reports_coverage():
    q = pd.DataFrame({
        "year": [2024, 2024, 2025, 2025],
        "base_available": [True, True, True, False],
        "lag_available": [True, True, False, True],
        "lag2_available": [True, False, True, True],
        "label_ok_15": [True, True, True, True],
        "sigma_15": [1.0, 2.0, 3.0, 4.0],
        "log_future_sigma_15": [0.0, 0.1, 0.2, 0.3],
        "future_tail_15": [0.0, 1.0, 0.0, 1.0],
    })
    z, counts = s.cohort(q, (2024, 2025), 15)
    assert len(z) == 1
    assert counts["own_base_and_future_feasible"] == 3
    assert counts["lag1_available"] == 2
    assert counts["lag2_available"] == 2
    assert counts["coverage"] == 1 / 3
