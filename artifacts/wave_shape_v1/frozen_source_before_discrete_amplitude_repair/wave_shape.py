"""Bounded post-hoc waveform diagnostics, never an entry/exit policy."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import rankdata

from star50_filter.filters import butter_lowpass, hysteresis_positions
from star50_filter.backtest import execute_next_open

FEATURES = ['peak_fraction', 'time_mass_skew', 'motion_concentration', 'half_height_width']
TARGETS = ['net_log', 'capture']
CONTROLS = ['bars', 'amplitude', 'sigma', 'net_trend_normalized']


def fixed_response(x):
    x = np.asarray(x, float)
    y = butter_lowpass(x, 12, 1)
    sigma = pd.Series(x).diff().rolling(48, min_periods=48).std(ddof=0).to_numpy()
    pos = hysteresis_positions(y, sigma)
    opens = np.exp(np.r_[x[0], x[:-1]])
    executed, pnl = execute_next_open(pos, opens)
    return y, sigma, pos, executed, pnl


def shape_cycle(period, family, p1, p2=0.):
    t = np.arange(period) / period
    if family == 'triangle':
        return .002 * np.where(t <= p1, t / p1, (1 - t) / (1 - p1))
    if family == 'pulse':
        width, peak = p1, p2
        local = (t - (1 - width) / 2) / width
        return .002 * np.maximum(0, np.minimum(local / peak, (1 - local) / (1 - peak)))
    if family == 'phase':
        return .002 * sum(a * np.cos(2 * np.pi * k * t + phase)
                         for k, a, phase in [(1, 1, 0), (2, .5, p1),
                                              (3, .25, p2), (4, .125, 0)])
    raise ValueError(family)


def waveform_shape(raw, peak):
    raw = np.asarray(raw, float)
    n = len(raw) - 1
    detrended = raw - np.linspace(raw[0], raw[-1], len(raw))
    positive = np.maximum(detrended, 0)
    amplitude = float(np.ptp(raw))
    if detrended[peak] <= 1e-12 or positive.sum() <= 1e-12 or amplitude <= 1e-12:
        return None
    t = np.arange(len(raw)) / n
    weights = positive / positive.sum()
    mean = float(weights @ t)
    variance = float(weights @ ((t - mean) ** 2))
    skew = float(weights @ ((t - mean) ** 3) / max(variance, 1e-15) ** 1.5)
    motion = np.abs(np.diff(raw))
    return {'peak_fraction': peak / n, 'time_mass_skew': skew,
        'motion_concentration': float(n * np.sum((motion / motion.sum()) ** 2)),
        'half_height_width': float(np.mean(positive >= .5 * positive.max())),
        'negative_area_share': float(np.maximum(-detrended, 0).sum() / np.abs(detrended).sum()),
        'amplitude': amplitude, 'net_trend_normalized': float((raw[-1] - raw[0]) / amplitude)}


def cycle_panel(frame):
    x = frame.log_close.to_numpy(float)
    smooth = signal.sosfiltfilt(signal.butter(1, 1 / 12, fs=1, output='sos'), x)
    lows = signal.find_peaks(-smooth)[0]
    rows, rejected = [], []
    covered = np.zeros(len(frame), bool)
    for a, c in zip(lows[:-1], lows[1:]):
        if a < 48 or c >= len(frame) - 48 or c - a < 4:
            continue
        b = int(a + np.argmax(smooth[a:c + 1]))
        shape = waveform_shape(x[a:c + 1], b - a)
        if shape is None:
            rejected.append({'a': int(a), 'c': int(c), 'net_log': float(frame.pnl_log.iloc[a + 1:c + 1].sum())})
            continue
        assert not covered[a + 1:c + 1].any()
        covered[a + 1:c + 1] = True
        net = float(frame.pnl_log.iloc[a + 1:c + 1].sum())
        road = float(np.abs(frame.open_log_return.iloc[a + 1:c + 1]).sum())
        if road <= 0:
            raise ValueError('zero-price-path cycle')
        rows.append({'a': int(a), 'b': int(b), 'c': int(c),
            'year': int(frame.year.iloc[a]), 'start': str(frame.timestamp.iloc[a]),
            'peak': str(frame.timestamp.iloc[b]), 'end': str(frame.timestamp.iloc[c]),
            'bars': int(c - a), 'sigma': float(frame.sigma.iloc[a:c + 1].median()),
            'net_log': net, 'capture': net / road, **shape})
    panel = pd.DataFrame(rows)
    assert abs(panel.net_log.sum() - frame.pnl_log.to_numpy()[covered].sum()) < 1e-12
    coverage = {'rows': len(frame), 'cycles': len(panel), 'covered_intervals': int(covered.sum()),
        'coverage_fraction': float(covered.mean()),
        'covered_net_log': float(frame.pnl_log.to_numpy()[covered].sum()),
        'uncovered_net_log': float(frame.pnl_log.to_numpy()[~covered].sum()),
        'full_net_log': float(frame.pnl_log.sum()), 'undefined_shapes': rejected}
    return panel, coverage, smooth


def adjusted_ranks(panel):
    z = rankdata(panel[CONTROLS].to_numpy(float), axis=0)
    z = (z - z.mean(axis=0)) / np.maximum(z.std(axis=0), 1e-12)
    design = np.c_[np.ones(len(z)), z]
    matrix = rankdata(panel[FEATURES + TARGETS].to_numpy(float), axis=0)
    residual = matrix - design @ np.linalg.lstsq(design, matrix, rcond=None)[0]
    return residual


def matched_shapes(panel):
    out = []
    n = len(panel)
    for feature in FEATURES:
        low = np.flatnonzero(panel[feature] <= panel[feature].quantile(.25))
        high = np.flatnonzero(panel[feature] >= panel[feature].quantile(.75))
        used = set()
        for i in high:
            a = panel.iloc[i]
            candidates = []
            for j in low:
                if int(j) in used:
                    continue
                b = panel.iloc[j]
                differences = np.abs(np.log([a.bars / b.bars, a.amplitude / b.amplitude,
                                             a.sigma / b.sigma]))
                trend_gap = abs(a.net_trend_normalized - b.net_trend_normalized)
                limits = np.log([1.25, 1.25, 1.5])
                if np.all(differences <= limits) and trend_gap <= .25:
                    distance = float((differences / limits).sum() + trend_gap / .25)
                    candidates.append((distance, int(j)))
            if candidates:
                _, j = min(candidates)
                used.add(j)
                b = panel.iloc[j]
                out.append({'year': int(a.year), 'feature': feature,
                    'high_a': int(a.a), 'low_a': int(b.a), 'year_cycles': n,
                    'high_feature': float(a[feature]), 'low_feature': float(b[feature]),
                    'high_bars': int(a.bars), 'low_bars': int(b.bars),
                    'high_amplitude': float(a.amplitude), 'low_amplitude': float(b.amplitude),
                    'delta_net_log': float(a.net_log - b.net_log),
                    'delta_capture': float(a.capture - b.capture)})
    return pd.DataFrame(out)


def permutation_associations(panels, draws=1999, seed=202609067):
    residuals = [adjusted_ranks(p) for p in panels]
    joined = np.concatenate(residuals)
    denom = np.maximum(np.sqrt((joined ** 2).sum(axis=0)), 1e-15)
    matrices = [r / denom for r in residuals]
    observed = (joined / denom)[:, :4].T @ (joined / denom)[:, 4:]
    rng = np.random.default_rng(seed)
    refs = {}
    for method in ['circular20', 'block20']:
        stats = np.zeros((draws, 4, 2))
        for draw in range(draws):
            for m in matrices:
                n = len(m)
                assert n > 40
                if method == 'circular20':
                    ix = np.roll(np.arange(n), rng.integers(20, n - 19))
                else:
                    blocks = [np.arange(i, min(i + 20, n)) for i in range(0, n, 20)]
                    ix = np.concatenate([blocks[i] for i in rng.permutation(len(blocks))])
                stats[draw] += m[ix, :4].T @ m[:, 4:]
        refs[method] = stats
    rows = []
    for i, f in enumerate(FEATURES):
        for j, target in enumerate(TARGETS):
            item = {'feature': f, 'target': target, 'adjusted_rank_rho': float(observed[i, j])}
            for name, values in refs.items():
                maximum = np.max(np.abs(values), axis=(1, 2))
                item[name + '_maxT_p'] = float((1 + np.sum(maximum >= abs(observed[i, j]))) / (draws + 1))
            rows.append(item)
    return pd.DataFrame(rows), refs
