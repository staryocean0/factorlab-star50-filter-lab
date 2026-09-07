"""Report/revalidate frozen waveform diagnostics; no new real-account replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from star50_filter.wave_shape import cycle_panel, fixed_response, permutation_associations, shape_cycle

OUT = ROOT / 'artifacts/wave_shape_v1p2'


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    frozen = json.loads((OUT / 'freeze.json').read_text())
    for name, expected in frozen['sources'].items():
        assert sha(ROOT / name) == expected
    source = ROOT / frozen['input_path']
    assert sha(source) == frozen['input_sha256']
    prior = sha(OUT / 'freeze.json')
    panels = []
    for year in range(2021, 2026):
        dest = OUT / str(year)
        review = json.loads((dest / 'review.json').read_text())
        assert review['prior_receipt_sha256'] == prior
        assert review['cycles_sha256'] == sha(dest / 'cycles.csv')
        prior = sha(dest / 'review.json')
        original = pd.read_parquet(source, filters=[('year', '==', year)]).reset_index(drop=True)
        repeated, coverage, _ = cycle_panel(original)
        assert hashlib.sha256(repeated.to_csv(index=False).encode()).hexdigest() == sha(dest / 'cycles.csv')
        recorded = json.loads((dest / 'coverage.json').read_text())
        assert coverage == recorded
        panels.append(pd.read_csv(dest / 'cycles.csv'))
    associations, refs = permutation_associations(panels)
    stored = pd.read_csv(OUT / 'associations.csv')
    numeric = associations.select_dtypes('number').columns
    assert np.allclose(associations[numeric], stored[numeric], rtol=0, atol=1e-14)
    for name, value in refs.items():
        assert np.array_equal(value, np.load(OUT / (name + '.npy')))
    # v1p1 and v1p2 independently executed all 450 synthetic cases; the only
    # intervening repair was the real-data diagnostic time mapping.
    synthetic_files = ['synthetic.csv', 'synthetic_summary.csv', 'filter_response.csv', 'synthetic_validation.json']
    for name in synthetic_files:
        assert sha(OUT / name) == sha(ROOT / 'artifacts/wave_shape_v1p1' / name)
    all_cycles = pd.concat(panels, ignore_index=True)
    matches = pd.read_csv(OUT / 'matched.csv')
    matched = matches.merge(all_cycles.add_prefix('high_'),
        left_on=['year', 'high_a'], right_on=['high_year', 'high_a'])
    matched = matched.merge(all_cycles.add_prefix('low_'),
        left_on=['year', 'low_a'], right_on=['low_year', 'low_a'])
    assert len(matched) == len(matches)
    assert np.allclose(matched.high_capture - matched.low_capture, matched.delta_capture)
    matched.to_csv(OUT / 'matched_details.csv', index=False)
    contrast = matched.groupby('feature').agg(pairs=('delta_capture', 'size'),
        high_capture=('high_capture', 'mean'), low_capture=('low_capture', 'mean'),
        high_net_log=('high_net_log', 'mean'), low_net_log=('low_net_log', 'mean'),
        high_loss_fraction=('high_net_log', lambda x: float((x < 0).mean())),
        low_loss_fraction=('low_net_log', lambda x: float((x < 0).mean()))).reset_index()
    contrast.to_csv(OUT / 'matched_outcomes.csv', index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    summary = pd.read_csv(OUT / 'synthetic_summary.csv')
    candidates = summary.loc[(summary.family == 'phase') & (summary.period == 24)]
    examples = candidates.loc[[candidates.capture.idxmin(), candidates.capture.idxmax()]]
    traces = []
    fig, axes = plt.subplots(3, 2, figsize=(11, 8), layout='constrained')
    sigma_arrays, spectra = [], []
    for col, row in enumerate(examples.itertuples()):
        cycle = shape_cycle(24, 'phase', row.p1, row.p2)
        x = np.tile(cycle, 80)
        y, sigma, pos, executed, pnl = fixed_response(x)
        i = np.arange(24 * 70, 24 * 72)
        # Price and LP are on one absolute log scale, not separately start-aligned.
        axes[0, col].plot(np.arange(48), x[i] * 10000, label='raw price')
        axes[0, col].plot(np.arange(48), (y[i] + x[0]) * 10000, label='causal LP12')
        axes[0, col].set_title(f'Same spectral powers; capture {row.capture:+.3f}')
        axes[0, col].legend()
        axes[1, col].step(np.arange(48), pos[i], label='close signal')
        axes[1, col].step(np.arange(48), executed[i], label='booked position', alpha=.65)
        axes[1, col].legend()
        axes[2, col].plot(np.arange(48), np.cumsum(pnl[i]) * 10000)
        axes[2, col].set_ylabel('Cumulative log PnL bp')
        axes[2, col].set_xlabel('5-minute bar index (two cycles)')
        spectra.append(abs(np.fft.rfft(cycle)))
        sigma_arrays.append(sigma[i])
        traces.append(pd.DataFrame({'case': col, 'bar': np.arange(48), 'raw_log': x[i],
            'filtered_log': y[i] + x[0], 'sigma': sigma[i], 'signal': pos[i],
            'exec_pos': executed[i], 'pnl_log': pnl[i]}))
    fig.suptitle('Only harmonic phase changes; original filter, threshold and account remain fixed')
    fig.savefig(OUT / 'same_spectrum_phase_examples.png', dpi=150)
    plt.close(fig)
    pd.concat(traces).to_csv(OUT / 'same_spectrum_phase_traces.csv', index=False)
    spectrum_error = float(np.max(abs(spectra[0] - spectra[1])))
    sigma_error = float(np.max(abs(sigma_arrays[0] - sigma_arrays[1])))
    assert spectrum_error < 1e-12 and sigma_error < 1e-12
    tests = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=ROOT, capture_output=True, text=True)
    save('tests.json', {'exit_code': tests.returncode, 'stdout': tests.stdout, 'stderr': tests.stderr})
    assert tests.returncode == 0
    save('validation.json', {'original_sources_and_input_hashes_passed': True,
        'original_account_mutations': 0, 'new_real_account_replays': 0,
        'annual_cycle_tables_replayed_byte_identically': 5,
        'annual_review_chain_passed': True, 'cycles': len(all_cycles),
        'synthetic_executions_each_process': 450, 'synthetic_replayed_identical_files': synthetic_files,
        'both_1999_draw_maxT_arrays_replayed_exactly': True,
        'same_spectrum_example_power_error': spectrum_error,
        'same_spectrum_example_sigma_error': sigma_error,
        'report_source_sha256': sha(Path(__file__)),
        'future_data_used': False, 'new_strategy_promoted': False,
        'limitations': ['hindsight cycles and shapes', 'finite linear controls and matched overlap',
                        'not all drawdown causes identified', 'no real-time veto tested']})
    print(contrast.to_string(index=False))
    print('PASS: original account unchanged; cycles, review chain, synthetic and permutation replay.')
    print(tests.stdout.strip())


if __name__ == '__main__':
    main()
