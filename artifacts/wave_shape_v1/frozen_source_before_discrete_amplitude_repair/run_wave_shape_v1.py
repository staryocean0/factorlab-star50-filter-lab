"""Frozen waveform mechanism study with separate controller-reviewed years."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy import signal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from star50_filter.wave_shape import (FEATURES, TARGETS, adjusted_ranks, cycle_panel,
    fixed_response, matched_shapes, permutation_associations, shape_cycle)

OUT = ROOT / 'artifacts/wave_shape_v1'
INPUT = ROOT / 'artifacts/streak_mechanism_v1/5m_offset_0/bars.parquet'
SOURCES = ['src/star50_filter/filters.py', 'src/star50_filter/backtest.py',
    'src/star50_filter/wave_shape.py', 'scripts/run_wave_shape_v1.py',
    'tests/test_wave_shape.py', 'docs/research/wave_shape_v1/method.md']


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def check():
    frozen = json.loads((OUT / 'freeze.json').read_text())
    assert sha(INPUT) == frozen['input_sha256']
    for name, expected in frozen['sources'].items():
        assert sha(ROOT / name) == expected, name
    return frozen


def freeze():
    assert not OUT.exists(), 'Do not rebind an existing freeze'
    accepted = json.loads((ROOT / 'artifacts/streak_mechanism_v1/manifest.json').read_text())['files']
    assert sha(INPUT) == accepted[str(INPUT.relative_to(ROOT))]
    source_authority = json.loads((ROOT / 'docs/research/streak_mechanism_v1/protocol.json').read_text())
    for name in SOURCES[:2]:
        assert sha(ROOT / name) == source_authority['source_hashes'][name]
    save(OUT / 'freeze.json', {'sources': {n: sha(ROOT / n) for n in SOURCES},
        'input_path': str(INPUT.relative_to(ROOT)), 'input_sha256': sha(INPUT),
        'roles': {'2021-2025': 'consumed_development_material', '2026': 'excluded'},
        'original_signal_or_account_changed': False, 'new_real_account_replays': 0,
        'synthetic_configurations': 90, 'synthetic_phase_replicates': 5,
        'primary_associations': 8, 'annual_review_order': [2021, 2022, 2023, 2024, 2025],
        'fresh_oos': False, 'production_authority': False})
    print('Frozen original sources, consumed data, 90 shapes and 8 primary associations.')


def synthetic():
    check()
    assert not (OUT / 'synthetic.csv').exists()
    menu = []
    for period in [24, 48, 96]:
        menu += [(period, 'triangle', r, 0.) for r in [.125, .25, .5, .75, .875]]
        menu += [(period, 'pulse', w, r) for w in [.25, .5, 1.] for r in [.25, .5, .75]]
        menu += [(period, 'phase', a, b) for a in np.arange(4) * np.pi / 2
                 for b in np.arange(4) * np.pi / 2]
    assert len(menu) == 90
    rows, spectrum_checks = [], []
    for period, family, p1, p2 in menu:
        cycle = shape_cycle(period, family, p1, p2)
        if family == 'phase':
            ref = abs(np.fft.rfft(shape_cycle(period, family, 0., 0.)))
            error = float(np.max(abs(abs(np.fft.rfft(cycle)) - ref)))
            assert error < 1e-12
            spectrum_checks.append(error)
        for phase in range(5):
            x = np.tile(np.roll(cycle, phase), 80)
            _, _, decision, executed, pnl = fixed_response(x)
            start = period * 16
            road = np.abs(np.diff(np.r_[x[0], x[:-1]]))[start - 1:].sum()
            assert len(pnl[start:]) == 64 * period
            rows.append({'period': period, 'family': family, 'p1': p1, 'p2': p2,
                'sample_phase': phase, 'peak_to_peak': float(np.ptp(cycle)),
                'capture': float(pnl[start:].sum() / road),
                'net_log_per_cycle': float(pnl[start:].sum() / 64),
                'long_log_per_cycle': float(pnl[start:][executed[start:] > 0].sum() / 64),
                'short_log_per_cycle': float(pnl[start:][executed[start:] < 0].sum() / 64),
                'reversals_per_cycle': float(np.count_nonzero(np.diff(decision[start:])) / 64)})
    f = pd.DataFrame(rows)
    f.to_csv(OUT / 'synthetic.csv', index=False)
    g = f.groupby(['period', 'family', 'p1', 'p2']).agg(
        capture=('capture', 'mean'), capture_min=('capture', 'min'), capture_max=('capture', 'max'),
        net_log_per_cycle=('net_log_per_cycle', 'mean'),
        long_log_per_cycle=('long_log_per_cycle', 'mean'),
        short_log_per_cycle=('short_log_per_cycle', 'mean')).reset_index()
    g.to_csv(OUT / 'synthetic_summary.csv', index=False)
    periods = np.array([2, 4, 6, 8, 12, 24, 48, 96, 240])
    sos = signal.butter(1, 1 / 12, fs=1., output='sos')
    _, response = signal.sosfreqz(sos, worN=1 / periods, fs=1.)
    freq = pd.DataFrame({'period_bars': periods, 'trading_minutes': periods * 5,
        'amplitude_gain': abs(response), 'phase_radians': np.angle(response),
        'phase_delay_bars': -np.angle(response) * periods / (2 * np.pi)})
    freq.to_csv(OUT / 'filter_response.csv', index=False)
    save(OUT / 'synthetic_validation.json', {'configuration_count': len(g), 'runs': len(f),
        'same_spectrum_max_abs_error': max(spectrum_checks),
        'all_original_sources_unchanged': True})
    print(freq.to_string(index=False))
    print(g.loc[g.family != 'phase'].to_string(index=False))
    print('Same-spectrum phase capture range:')
    print(g.loc[g.family == 'phase'].groupby('period').capture.agg(['min', 'max']).to_string())


def annual(year):
    check()
    if year > 2021:
        prior = OUT / str(year - 1) / 'review.json'
        assert prior.exists(), 'Controller must review preceding year first'
    dest = OUT / str(year)
    assert not dest.exists()
    dest.mkdir()
    frame = pd.read_parquet(INPUT, filters=[('year', '==', year)]).reset_index(drop=True)
    assert set(frame.year) == {year}
    panel, coverage, smooth = cycle_panel(frame)
    panel.to_csv(dest / 'cycles.csv', index=False)
    matched_shapes(panel).to_csv(dest / 'matched.csv', index=False)
    residual = adjusted_ranks(panel)
    corr = np.corrcoef(residual, rowvar=False)[:4, 4:]
    associations = [{'feature': feature, 'target': target, 'adjusted_rank_rho': float(corr[i, j])}
        for i, feature in enumerate(FEATURES) for j, target in enumerate(TARGETS)]
    save(dest / 'associations.json', associations)
    cells = []
    for feature in FEATURES:
        for label, select in [('low', panel[feature] <= panel[feature].quantile(.25)),
                              ('high', panel[feature] >= panel[feature].quantile(.75))]:
            p = panel.loc[select]
            cells.append({'feature': feature, 'bucket': label, 'n': len(p),
                'mean_capture': float(p.capture.mean()), 'mean_net_log': float(p.net_log.mean()),
                'loss_fraction': float((p.net_log < 0).mean())})
    save(dest / 'cells.json', cells)
    save(dest / 'coverage.json', coverage)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    examples = []
    for side, subset in [('concentrated', panel.loc[panel.motion_concentration >= panel.motion_concentration.quantile(.75)]),
                          ('dispersed', panel.loc[panel.motion_concentration <= panel.motion_concentration.quantile(.25)])]:
        for result, index in [('worst', subset.capture.idxmin()), ('best', subset.capture.idxmax())]:
            row = panel.loc[index].to_dict()
            row.update({'selection': side + '_' + result})
            examples.append(row)
    fig, axes = plt.subplots(2, 4, figsize=(16, 6), layout='constrained')
    for k, row in enumerate(examples):
        a, c = int(row['a']), int(row['c'])
        q = frame.iloc[a:c + 1]
        origin = float(frame.log_close.iloc[a])
        axes[0, k].plot(np.arange(len(q)), 10000 * (q.log_close.to_numpy() - origin), label='raw log close')
        causal = q.lowpass.to_numpy() - q.lowpass.iloc[0]
        axes[0, k].plot(np.arange(len(q)), 10000 * causal, label='causal LP12 (start-aligned)')
        axes[0, k].axvline(int(row['b']) - a, color='grey', ls='--')
        axes[0, k].set_title(f"{row['selection']}\n{row['start'][:16]} | capture {row['capture']:.3f}", fontsize=9)
        axes[1, k].plot(np.arange(1, len(q)), np.cumsum(q.pnl_log.to_numpy()[1:]) * 10000)
        ax = axes[1, k].twinx()
        ax.step(np.arange(1, len(q)), q.exec_pos.to_numpy()[1:], color='grey', alpha=.35)
        ax.set_ylim(-1.3, 1.3)
        axes[0, k].legend(fontsize=7)
        axes[1, k].set_xlabel('Original 5m bar index')
    fig.suptitle(f'{year}: post-hoc waveform examples; bottom = original cumulative log PnL bp / position')
    fig.savefig(dest / 'examples.png', dpi=130)
    plt.close(fig)
    save(dest / 'examples.json', examples)
    print(year, json.dumps({k: v for k, v in coverage.items() if k != 'undefined_shapes'}, ensure_ascii=False))
    print(pd.DataFrame(associations).to_string(index=False))
    print(pd.DataFrame(cells).to_string(index=False))


def aggregate():
    check()
    panels = []
    for year in range(2021, 2026):
        assert (OUT / str(year) / 'review.json').exists()
        panels.append(pd.read_csv(OUT / str(year) / 'cycles.csv'))
    results, refs = permutation_associations(panels)
    results.to_csv(OUT / 'associations.csv', index=False)
    for name, values in refs.items():
        np.save(OUT / (name + '.npy'), values)
    matches = pd.concat([pd.read_csv(OUT / str(year) / 'matched.csv') for year in range(2021, 2026)])
    matches.to_csv(OUT / 'matched.csv', index=False)
    summary = matches.groupby('feature').agg(pairs=('delta_capture', 'size'),
        high_minus_low_capture=('delta_capture', 'mean'),
        high_minus_low_net_log=('delta_net_log', 'mean')).reset_index()
    summary.to_csv(OUT / 'matched_summary.csv', index=False)
    print(results.to_string(index=False))
    print(summary.to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'synthetic', 'year', 'aggregate'])
    parser.add_argument('--year', type=int, choices=range(2021, 2026))
    args = parser.parse_args()
    if args.action == 'freeze': freeze()
    elif args.action == 'synthetic': synthetic()
    elif args.action == 'year':
        assert args.year is not None
        annual(args.year)
    else: aggregate()
