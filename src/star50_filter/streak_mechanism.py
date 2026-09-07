"""Bounded retrospective diagnostics. No position or strategy changes."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

FEATURES = ['eff_1d', 'fast_share_1d', 'slow_work_velocity_5d',
            'threshold_work_amplitude_5d']
WINDOWS = (20, 50, 100)
METHODS = ('trade_shuffle', 'day_shuffle', 'block5_shuffle')
STATISTICS = ('longest_loss', 'longest_win', 'scan_low', 'scan_high')


def sequence_stats(values, p):
    x = np.atleast_2d(np.asarray(values, dtype=np.int8))
    probability = np.broadcast_to(np.asarray(p, float), (x.shape[1],))
    assert np.isin(x, [-1, 0, 1]).all()
    result = np.zeros((len(x), 4))
    for j, sign in enumerate((-1, 1)):
        run = np.zeros(len(x), dtype=int)
        for column in x.T:
            run = (run + 1) * (column == sign)
            result[:, j] = np.maximum(result[:, j], run)
    wins = np.pad(np.cumsum(x == 1, axis=1), ((0, 0), (1, 0)))
    expected = np.r_[0., np.cumsum(probability)]
    variance = np.r_[0., np.cumsum(probability * (1 - probability))]
    for w in WINDOWS:
        if w > x.shape[1]:
            continue
        z = ((wins[:, w:] - wins[:, :-w]) - (expected[w:] - expected[:-w]))
        z = z / np.maximum(np.sqrt(variance[w:] - variance[:-w]), 1e-12)
        result[:, 2] = np.maximum(result[:, 2], (-z).max(axis=1))
        result[:, 3] = np.maximum(result[:, 3], z.max(axis=1))
    return result


def permuted_sequences(values, cluster_ids, draws, seed):
    x = np.asarray(values, dtype=np.int8)
    ids = np.asarray(cluster_ids)
    assert len(ids) == len(x)
    groups = [np.flatnonzero(ids == k) for k in pd.unique(ids)]
    rng = np.random.default_rng(seed)
    return np.asarray([x[np.concatenate([groups[k] for k in rng.permutation(len(groups))])]
                       for _ in range(draws)], dtype=np.int8)


def holm(pvalues):
    p = np.asarray(pvalues, float)
    order = np.argsort(p, kind='stable')
    adjusted = np.minimum(1., np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    result = np.empty(len(p))
    result[order] = adjusted
    return result


def runs(values):
    x = np.asarray(values)
    splits = np.r_[0, np.flatnonzero(x[1:] != x[:-1]) + 1, len(x)]
    return pd.DataFrame([{'start': int(a), 'end': int(b), 'length': int(b-a),
                          'sign': int(x[a])} for a, b in zip(splits[:-1], splits[1:])])


def conditional_wins(values):
    rows = []
    loss_streak = 0
    for i, value in enumerate(values):
        bucket = str(loss_streak) if loss_streak <= 2 else '3-4' if loss_streak < 5 else '5+'
        if i:
            rows.append({'prior_losses': bucket, 'win': value == 1, 'loss': value == -1})
        loss_streak = loss_streak + 1 if value == -1 else 0
    f = pd.DataFrame(rows)
    return f.groupby('prior_losses', sort=False).agg(n=('win', 'size'), wins=('win', 'sum'),
                                                   win_rate=('win', 'mean')).reset_index()


def centered_ranks(frame, columns):
    values = frame[columns].to_numpy(float)
    years = frame.year.to_numpy()
    out = np.zeros_like(values)
    for year in np.unique(years):
        ix = np.flatnonzero(years == year)
        r = rankdata(values[ix], axis=0)
        out[ix] = r - r.mean(axis=0)
    return out / np.maximum(np.sqrt(np.sum(out**2, axis=0)), 1e-15)


def stage_associations(frame, draws=1999, seed=202609065):
    targets = ['win_rate', 'mean_trade_log']
    f = frame.dropna(subset=FEATURES + targets).reset_index(drop=True)
    xx, yy = centered_ranks(f, FEATURES), centered_ranks(f, targets)
    observed = xx.T @ yy
    groups = [np.flatnonzero(f.year.to_numpy() == y) for y in sorted(f.year.unique())]
    assert min(map(len, groups)) >= 10
    rng = np.random.default_rng(seed)
    nulls = {}
    for method in ('circular4', 'block4'):
        values = np.empty((draws, len(FEATURES), len(targets)))
        for k in range(draws):
            order = np.arange(len(f))
            for ix in groups:
                if method == 'circular4':
                    order[ix] = np.roll(ix, rng.integers(4, len(ix)-3))
                else:
                    blocks = [ix[a:a+4] for a in range(0, len(ix), 4)]
                    order[ix] = np.concatenate([blocks[j] for j in rng.permutation(len(blocks))])
            values[k] = xx[order].T @ yy
        nulls[method] = values
    rows = []
    for i, feature in enumerate(FEATURES):
        for j, target in enumerate(targets):
            row = {'feature': feature, 'outcome': target, 'rho': observed[i, j], 'stages': len(f)}
            for method, values in nulls.items():
                row[method + '_p'] = (1 + np.sum(abs(values[:, i, j]) >= abs(observed[i, j]))) / (draws+1)
                row[method + '_maxT_p'] = (1 + np.sum(np.max(abs(values), axis=(1, 2)) >= abs(observed[i, j]))) / (draws+1)
            rows.append(row)
    return pd.DataFrame(rows)


def synthetic_cases():
    from star50_filter.filters import butter_lowpass, hysteresis_positions
    from star50_filter.backtest import execute_next_open
    n, warm, amplitude = 9600, 1920, .002
    time = np.arange(n)
    rows = []
    for period in (6, 8, 12, 24, 48, 96, 240):
        cases = [('wave', ratio, phase, 0) for ratio in (0, .5, 2)
                 for phase in (0, np.pi/2, np.pi)]
        cases += [('drift', 0, 0, drift) for drift in (-.5, 0, .5)]
        for kind, ratio, phase, drift in cases:
            x = (amplitude*np.sin(2*np.pi*time/period)
                 + ratio*amplitude*960/period*np.sin(2*np.pi*time/960+phase)
                 + drift*amplitude*2*np.pi/period*time)
            opens = np.exp(np.r_[x[0], x[:-1]])
            sigma = pd.Series(x).diff().rolling(48).std(ddof=0).to_numpy()
            signal = hysteresis_positions(butter_lowpass(x, 12, 1), sigma)
            pos, pnl = execute_next_open(signal, opens)
            p, ret = pos[warm:], pnl[warm:]
            edges = np.r_[0, np.flatnonzero(p[1:] != p[:-1])+1, len(p)]
            trades = np.asarray([ret[a:b].sum() for a, b in zip(edges[1:-2], edges[2:-1])])
            signs = np.sign(trades).astype(np.int8)
            win_rate = float(np.mean(signs == 1)) if len(signs) else None
            rows.append({'kind': kind, 'period_bars': period, 'slow_velocity_ratio': ratio,
                         'slow_phase': phase, 'drift_velocity_ratio': drift,
                         'trades': len(trades), 'win_rate': win_rate,
                         'longest_loss': int(sequence_stats(signs, win_rate)[0, 0]) if len(signs) else 0,
                         'capture': ret.sum()/np.abs(np.diff(np.log(opens))[warm-1:]).sum()})
    return pd.DataFrame(rows)
