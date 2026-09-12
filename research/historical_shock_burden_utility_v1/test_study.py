from __future__ import annotations

import numpy as np
import pandas as pd

from research.historical_shock_burden_utility_v1 import run_study as s


def memory_frame(n=16):
    return pd.DataFrame({
        "symbol": ["000688.SH"] * n,
        "final_shock_intensity": np.linspace(1.0, 4.0, n),
        "final_vol_ratio": np.linspace(0.8, 2.0, n),
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
        "shock_count12": [0.0, 1.0, 2.0],
        "shock_excess12": [0.0, 0.5, 1.5],
        "highvol_count12": [1.0, 2.0, 3.0],
        "highvol_excess12": [0.2, 0.8, 1.7],
    })


def test_memory_excludes_current_row_and_updates_only_future_rows():
    a = memory_frame()
    z1 = s.attach_memory(a)
    assert bool(z1.loc[12, "memory_available"])
    before = z1.loc[12, ["shock_count12", "shock_excess12", "highvol_count12", "highvol_excess12"]].to_numpy(float)

    b = a.copy()
    b.loc[12, "final_shock_intensity"] = 100.0
    b.loc[12, "final_vol_ratio"] = 100.0
    z2 = s.attach_memory(b)
    after = z2.loc[12, ["shock_count12", "shock_excess12", "highvol_count12", "highvol_excess12"]].to_numpy(float)
    np.testing.assert_allclose(before, after, rtol=0, atol=0)
    assert z2.loc[13, "shock_excess12"] > z1.loc[13, "shock_excess12"]
    assert z2.loc[13, "highvol_excess12"] > z1.loc[13, "highvol_excess12"]


def test_memory_uses_exact_latest_twelve_valid_completed_bars():
    a = memory_frame(14)
    a.loc[0, ["final_shock_intensity", "final_vol_ratio"]] = np.nan
    z = s.attach_memory(a)
    assert not bool(z.loc[12, "memory_available"])
    assert bool(z.loc[13, "memory_available"])

    prior = a.loc[1:12]
    expected_shock_count = float((prior.final_shock_intensity >= s.SHOCK_SIGMA).sum())
    expected_shock_excess = float(np.maximum(prior.final_shock_intensity.to_numpy() - s.SHOCK_SIGMA, 0).sum())
    expected_highvol_count = float((prior.final_vol_ratio >= s.HIGHVOL_RATIO).sum())
    expected_highvol_excess = float(np.maximum(prior.final_vol_ratio.to_numpy() - s.HIGHVOL_RATIO, 0).sum())
    assert z.loc[13, "shock_count12"] == expected_shock_count
    assert z.loc[13, "shock_excess12"] == expected_shock_excess
    assert z.loc[13, "highvol_count12"] == expected_highvol_count
    assert z.loc[13, "highvol_excess12"] == expected_highvol_excess


def test_shock_and_highvol_memory_are_exact_complexity_matches():
    q = design_frame()
    xc, nc = s.design(q, "C")
    xs, ns = s.design(q, "S")
    xh, nh = s.design(q, "H")
    assert ns == nh
    assert xs.shape == xh.shape
    assert xs.shape[1] == xc.shape[1] + 20
    assert ns[: len(nc)] == nc


def test_design_names_cannot_contain_current_final_or_future_fields():
    q = design_frame()
    for model in s.MODELS:
        _, names = s.design(q, model)
        joined = " ".join(names).lower()
        for forbidden in ("future", "final", "close", "sigma_", "return"):
            assert forbidden not in joined


def test_cohort_uses_same_rows_for_all_models_and_reports_memory_coverage():
    q = pd.DataFrame({
        "year": [2024, 2024, 2025, 2025],
        "base_available": [True, True, True, False],
        "memory_available": [True, False, True, True],
        "label_ok_15": [True, True, True, True],
        "sigma_15": [1.0, 2.0, 3.0, 4.0],
        "log_future_sigma_15": [0.0, 0.1, 0.2, 0.3],
        "future_tail_15": [0.0, 1.0, 0.0, 1.0],
    })
    z, counts = s.cohort(q, (2024, 2025), 15)
    assert len(z) == 2
    assert counts["own_base_and_future_feasible"] == 3
    assert counts["memory_available"] == 2
    assert counts["coverage"] == 2 / 3
