import numpy as np
import pytest
from star50_filter.resolution_measurement import efficiency, observed_grid
from star50_filter.slope_union_v2 import Policy, features, targets


def test_trend_flat_missing_jump():
    p = np.exp(np.arange(50) * 0.01)
    np.testing.assert_allclose(efficiency(p, 10).er.iloc[10:], 1)
    assert efficiency(np.ones(50), 10).er.isna().all()
    p[20] = np.nan
    assert efficiency(p, 10).er.iloc[20:31].isna().all()
    p = np.ones(50)
    p[25:] = 2
    assert efficiency(p, 10).top1.iloc[25] == 1


def test_asof_age_and_validity_do_not_fill_gaps():
    t = np.array([0, 3, 10]) * 10**9
    p, a = observed_grid(t, [10, 11, 12], np.array([3, 6, 13]) * 10**9, np.arange(15) * 10**9)
    np.testing.assert_array_equal(p[:6], [10, 10, 10, 11, 11, 11])
    assert np.isnan(p[6:10]).all() and np.isnan(p[13:]).all()
    assert np.nanmax(a) <= 3
    with pytest.raises(ValueError):
        observed_grid([0, 0], [1, 2], [1, 2], [0])


def test_random_walk_raw_variance_can_shrink_mechanically():
    r = np.random.default_rng(213).normal(0, 0.001, 90000)
    x = np.cumsum(r)
    fine = efficiency(np.exp(x), 600).er.dropna()
    coarse = efficiency(np.exp(x[::20]), 30).er.dropna()
    assert fine.var() < coarse.var() * 0.2
    # Same random walk, not an improvement in economic opportunity or stationarity.
    assert fine.mean() < coarse.mean()


def test_v2_log_amplitude_scaling_does_not_change_signals():
    t = np.arange(3000)
    x = np.cumsum(np.random.default_rng(5).normal(0, 0.001, len(t))) + 0.04 * np.sin(t / 60)
    p = Policy(entry_alpha=0.001, weight_power=2, volatility_window=480, cooldown=5)
    _, s, v = features(np.exp(x))
    expected = targets(s, v[480], p)
    assert (expected != 0).any()
    for scale in [0.25, 4]:
        _, ss, vv = features(np.exp(x * scale))
        np.testing.assert_array_equal(expected, targets(ss, vv[480], p))
