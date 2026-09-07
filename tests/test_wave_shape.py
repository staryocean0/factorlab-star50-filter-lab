import numpy as np

from star50_filter.wave_shape import fixed_response, shape_cycle, waveform_shape, cycle_panel


def test_triangle_time_peak_and_amplitude():
    for r in [.125, .25, .5, .75, .875]:
        x = shape_cycle(96, 'triangle', r)
        assert np.isclose(np.ptp(x), .002)
        assert np.argmax(x) == 96 * r


def test_same_spectrum_phase_family():
    ref = abs(np.fft.rfft(shape_cycle(48, 'phase', 0, 0)))
    for a in np.arange(4) * np.pi / 2:
        for b in np.arange(4) * np.pi / 2:
            assert np.allclose(abs(np.fft.rfft(shape_cycle(48, 'phase', a, b))), ref, atol=1e-12)


def test_long_short_sign_symmetry():
    x = np.tile(shape_cycle(48, 'pulse', .5, .25), 80)
    a, b = fixed_response(x), fixed_response(-x)
    assert np.array_equal(a[2], -b[2])
    assert np.allclose(a[-1], b[-1], rtol=0, atol=1e-14)


def test_scaling_keeps_signals():
    x = np.tile(shape_cycle(48, 'phase', np.pi / 2, np.pi), 80)
    a, b = fixed_response(x), fixed_response(3 * x)
    assert np.array_equal(a[2][768:], b[2][768:])
    assert np.allclose(a[-1], b[-1] / 3, atol=1e-14)


def test_time_skew_is_not_peak_direction_name():
    x = np.r_[shape_cycle(96, 'triangle', .25), 0.]
    left = waveform_shape(x, 24)
    right = waveform_shape(x[::-1], 72)
    assert left['peak_fraction'] == .25 and right['peak_fraction'] == .75
    assert left['time_mass_skew'] > 0 and right['time_mass_skew'] < 0
    assert np.isclose(left['time_mass_skew'], -right['time_mass_skew'])


def test_constant_shape_invalid():
    assert waveform_shape(np.zeros(20), 10) is None


def test_sampled_pulse_amplitude_is_fixed():
    for period in [24, 48, 96]:
        for width in [.25, .5, 1.]:
            for peak in [.25, .5, .75]:
                assert np.isclose(np.ptp(shape_cycle(period, 'pulse', width, peak)), .002)


def test_cycle_uses_post_close_next_open_intervals():
    import pandas as pd
    x = np.tile(shape_cycle(48, 'triangle', .5), 20)
    _, sigma, _, _, pnl = fixed_response(x)
    opens = np.r_[x[0], x[:-1]]
    f = pd.DataFrame({'log_close': x, 'pnl_log': pnl, 'sigma': sigma,
        'open_log_return': np.r_[0, np.diff(opens)], 'year': 2021,
        'timestamp': pd.date_range('2021-01-01', periods=len(x), freq='5min')})
    panel, _, _ = cycle_panel(f)
    for row in panel.itertuples():
        assert row.pnl_first_index == row.a + 2
        assert row.pnl_last_index == row.c + 1
        assert np.isclose(row.net_log, pnl[row.a + 2:row.c + 2].sum())
