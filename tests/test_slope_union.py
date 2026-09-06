"""Independent mathematical and causal oracles for the research prototype."""

import itertools
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.signal import butter, lfilter, sosfilt
from star50_filter.slope_union import (
    SlopeUnionConfig,
    build_signals,
    coefficients,
    slope_covariance,
    threshold_table,
    transition,
)


def bars_from_returns(returns):
    stamps = []
    for day in pd.bdate_range("2021-01-04", periods=int(len(returns) / 240) + 1):
        for start, end in [("09:31", "11:30"), ("13:01", "15:00")]:
            stamps.extend(pd.date_range(f"{day.date()} {start}", f"{day.date()} {end}", freq="min", tz="Asia/Shanghai"))
    return pd.DataFrame(
        {
            "timestamp": stamps[: len(returns)],
            "trading_minute": np.arange(len(returns)),
            "close": 1000 * np.exp(np.cumsum(returns)),
        }
    )


@pytest.fixture
def bars():
    rng = np.random.default_rng(7101)
    return bars_from_returns(rng.normal(0, 0.001, 1440))


def test_filter_matches_independent_scipy_and_endpoints(bars):
    out = build_signals(bars)
    x = np.log(bars.close.to_numpy())
    expected = sosfilt(butter(1, 1 / 120, fs=1, output="sos"), x - x[0])
    np.testing.assert_allclose(out.lowpass_log_relative.iloc[120:], expected[120:], atol=1e-14)
    assert out.lowpass_log_relative.iloc[:120].isna().all()
    for h in range(1, 6):
        np.testing.assert_allclose(out[f"slope_{h}"].iloc[120 + h :], (expected[120 + h :] - expected[120:-h]) / h, atol=1e-14)


@pytest.mark.parametrize("cutoff", [4, 24, 120, 960])
def test_covariance_against_impulse_energy(cutoff):
    cfg = SlopeUnionConfig(cutoff_minutes=cutoff)
    a, b = coefficients(cfg)
    impulse = np.zeros(20000)
    impulse[0] = 1
    response = lfilter([b, b], [1, -a], impulse)
    averaged = [np.convolve(response, np.ones(h) / h)[: len(response)] for h in range(1, 6)]
    expected = np.array([[np.dot(x, y) for y in averaged] for x in averaged])
    np.testing.assert_allclose(slope_covariance(cfg), expected, atol=2e-14, rtol=1e-12)


def test_threshold_curve_and_sigma_units():
    table = threshold_table()
    assert (np.diff(table.entry_per_sigma) < 0).all()
    assert (np.diff(table.exit_per_sigma) < 0).all()
    assert (table.entry_per_sigma > table.exit_per_sigma).all()
    assert table.slope_sd_per_sigma.iloc[-1] / table.slope_sd_per_sigma.iloc[0] > 0.9
    assert np.isclose(table.weight.sum(), 1)


def test_future_prefix_and_repeat_invariance(bars):
    full = build_signals(bars)
    pd.testing.assert_frame_equal(full, build_signals(bars))
    for stop in [121, 241, 800, 1100]:
        pd.testing.assert_frame_equal(full.iloc[:stop], build_signals(bars.iloc[:stop]))
    mutated = bars.copy()
    mutated.loc[900:, "close"] *= 2
    pd.testing.assert_frame_equal(full.iloc[:900], build_signals(mutated).iloc[:900])


def test_current_return_cannot_change_own_sigma(bars):
    out = build_signals(bars)
    altered = bars.copy()
    altered.loc[700, "close"] *= 1.1
    changed = build_signals(altered)
    assert out.sigma_prior.iloc[700] == changed.sigma_prior.iloc[700]
    r = np.log(bars.close).diff()
    assert np.isclose(out.sigma_prior.iloc[700], r.iloc[460:700].std(ddof=1))
    assert not np.isclose(out.sigma_prior.iloc[701], changed.sigma_prior.iloc[701])


def test_full_price_mirror_and_scale_invariance(bars):
    bars = bars.copy()
    bars["close"] *= np.exp(0.04 * np.sin(2 * np.pi * np.arange(len(bars)) / 180))
    original = build_signals(bars)
    inverse = bars.copy()
    inverse["close"] = 1e6 / bars.close
    mirror = build_signals(inverse)
    np.testing.assert_array_equal(original.target_at_close, -mirror.target_at_close)
    assert original.target_at_close.abs().sum() > 0
    scaled = bars.copy()
    scaled["close"] *= 100
    np.testing.assert_array_equal(original.target_at_close, build_signals(scaled).target_at_close)


def test_every_boolean_transition_is_direction_symmetric():
    for state in [-1, 0, 1]:
        for el, es, xl, xs in itertools.product([False, True], repeat=4):
            result, _ = transition(state, entry_long=el, entry_short=es, exit_long=xl, exit_short=xs)
            inverse, _ = transition(-state, entry_long=es, entry_short=el, exit_long=xs, exit_short=xl)
            assert result == -inverse


def test_exit_reversal_and_conflict():
    def step(state, el=False, es=False, xl=False, xs=False, mode="long_short"):
        return transition(state, entry_long=el, entry_short=es, exit_long=xl, exit_short=xs, direction=mode)

    assert step(0, el=True) == (1, "enter_long")
    assert step(0, el=True, es=True) == (0, "entry_conflict")
    assert step(1, xl=True) == (0, "exit_long")
    assert step(1, es=True, xl=True) == (-1, "reverse_short")
    assert step(1, el=True, es=True, xl=True) == (0, "exit_long")
    assert step(1, es=True, xl=True, mode="long_only") == (0, "exit_long")
    assert step(1, es=True) == (1, "hold_long")


def test_union_masks_and_strict_comparison(bars, monkeypatch):
    from star50_filter import slope_union

    out = build_signals(bars)
    expected = np.zeros(len(out), dtype=int)
    for h in range(1, 6):
        expected |= ((out[f"slope_{h}"] > out[f"entry_threshold_{h}"]) & out.ready).to_numpy(dtype=int) << (h - 1)
    np.testing.assert_array_equal(out.entry_long_mask, expected)

    # A constructed table at equality must not trigger; positive fifth window alone does.
    def fake_filter(*args):
        y = np.zeros(len(bars))
        y[500:] = 1
        return y

    monkeypatch.setattr(slope_union, "lfilter", fake_filter)
    table = threshold_table()
    table["entry_per_sigma"] = 1e20
    table["exit_per_sigma"] = 1e20
    table.loc[4, "entry_per_sigma"] = 0
    monkeypatch.setattr(slope_union, "threshold_table", lambda config: table)
    special = build_signals(bars)
    assert special.entry_long_mask.iloc[500] == 16
    assert special.target_at_close.iloc[500] == 1
    assert special.entry_long_mask.iloc[510] == 0  # slope == threshold == 0


@pytest.mark.parametrize("mode,forbidden", [("long_only", -1), ("short_only", 1)])
def test_single_direction_modes(bars, mode, forbidden):
    out = build_signals(bars, replace(SlopeUnionConfig(), direction=mode))
    assert forbidden not in out.target_at_close.to_numpy()


def test_flat_input_and_not_ready_holds():
    out = build_signals(bars_from_returns(np.zeros(700)))
    assert not out.ready.any()
    assert out.target_at_close.eq(0).all()
    assert out.attrs["fills_computed"] is False


@pytest.mark.parametrize("fault", ["duplicate", "naive", "gap", "ordinal", "negative", "nan", "infinity"])
def test_bad_inputs_fail(bars, fault):
    broken = bars.copy()
    if fault == "duplicate":
        broken.loc[50, "timestamp"] = broken.timestamp.iloc[49]
    elif fault == "naive":
        broken["timestamp"] = broken.timestamp.dt.tz_localize(None)
    elif fault == "gap":
        broken = broken.drop(50).reset_index(drop=True)
        broken["trading_minute"] = np.arange(len(broken))
    elif fault == "ordinal":
        broken.loc[50, "trading_minute"] += 2
    else:
        broken.loc[50, "close"] = {"negative": -1, "nan": np.nan, "infinity": np.inf}[fault]
    with pytest.raises(ValueError):
        build_signals(broken)


@pytest.mark.parametrize(
    "updates",
    [
        {"cutoff_minutes": 2},
        {"entry_alpha": 0},
        {"exit_alpha": 0.001},
        {"weight_power": -1},
        {"volatility_window": 1},
        {"volatility_window": 240.0},
        {"sigma_floor": float("nan")},
        {"direction": "both"},
    ],
)
def test_bad_config_fails(updates):
    with pytest.raises(ValueError):
        SlopeUnionConfig(**updates)
