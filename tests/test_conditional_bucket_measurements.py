import numpy as np
import pandas as pd
import pytest

from star50_filter.conditional_bucket_measurements import FEATURES, causal_measurements


def test_future_prices_and_signal_do_not_change_past_measurements():
    rng = np.random.default_rng(815)
    price = 100*np.exp(np.cumsum(rng.normal(0, .002, 1600)))
    signal = np.where(np.arange(1600)%41 < 20, 1., -1.)
    a = causal_measurements(price, signal)
    future_price, future_signal = price.copy(), signal.copy()
    future_price[1000:] *= np.exp(np.linspace(0, 1, 600))
    future_signal[1000:] *= -1
    b = causal_measurements(future_price, future_signal)
    pd.testing.assert_frame_equal(a.iloc[:1000], b.iloc[:1000])
    pd.testing.assert_frame_equal(a.iloc[:1000], causal_measurements(price[:1000], signal[:1000]))
    assert list(a.columns) == list(FEATURES)


def test_price_units_do_not_create_artificial_condition_strength():
    price = np.exp(np.linspace(4., 4.1, 1000)+.01*np.sin(np.arange(1000)/13))
    side = np.ones(1000)
    a, b = causal_measurements(price, side), causal_measurements(price*100, side)
    assert np.allclose(a, b, atol=1e-8, rtol=1e-8, equal_nan=True)


def test_missing_warmup_and_zero_wave_are_not_pass_conditions():
    f = causal_measurements(np.ones(600)*100, np.ones(600))
    assert f.threshold_work_amplitude_48.isna().all()
    assert f.work_efficiency_48.isna().all()
    assert f.slow_directional_efficiency_48.isna().all()
    assert not np.isinf(f.to_numpy()).any()


def test_invalid_price_or_signal_rejected():
    with pytest.raises(ValueError):
        causal_measurements([1., 0.], [1., 1.])
    with pytest.raises(ValueError):
        causal_measurements([1., 2.], [1., 2.])
