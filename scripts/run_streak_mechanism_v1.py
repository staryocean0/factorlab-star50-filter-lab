"""Freeze, materialize, review separately, and audit one fixed-policy study."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from reproduce_historical_baseline import baseline_frame, load_bars, fingerprint
from star50_filter.cross_scale_root_cause import properties, trade_fragments
from star50_filter.streak_mechanism import (
    FEATURES, METHODS, STATISTICS, WINDOWS, conditional_wins, holm,
    permuted_sequences, runs, sequence_stats, stage_associations, synthetic_cases,
)

DOC = ROOT/'docs/research/streak_mechanism_v1'
OUT = ROOT/'artifacts/streak_mechanism_v1'
DATA = ROOT/'artifacts/drawdown_material'
YEARS = (2021, 2022, 2023, 2024, 2025)
DRAWS = 1999
VIEWS = [f'5m_offset_{i}' for i in range(5)]
SOURCES = ['src/star50_filter/filters.py', 'src/star50_filter/backtest.py',
           'src/star50_filter/cross_scale_root_cause.py',
           'scripts/reproduce_historical_baseline.py',
           'src/star50_filter/streak_mechanism.py',
           'scripts/run_streak_mechanism_v1.py', 'tests/test_streak_mechanism.py',
           'docs/research/streak_mechanism_v1/method.md']


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def csv(p, frame):
    p.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(p, index=False, float_format='%.17g')


def check_sources():
    contract = json.loads((DOC/'protocol.json').read_text())
    for p, h in contract['source_hashes'].items():
        assert sha(ROOT/p) == h, p
    for item in contract['inputs']:
        assert sha(ROOT/item['path']) == item['sha256']
    return contract


def freeze():
    assert not (DOC/'protocol.json').exists()
    old = json.loads((ROOT/'data/manifest.json').read_text())
    originals = {v['view_id']: v for v in old['views']}
    inputs = []
    for view in VIEWS:
        item = originals[view]
        assert sha(ROOT/item['file']) == item['sha256']
        p = DATA/(view+'.parquet')
        inputs.append({'view': view, 'path': str(p.relative_to(ROOT)), 'sha256': sha(p),
                       'original_path': item['file'], 'original_sha256': item['sha256']})
    original_bindings = {}
    for p in SOURCES[:2]:
        data = subprocess.check_output(['git', 'show', 'bdbcf7dc:'+p], cwd=ROOT)
        h = hashlib.sha256(data).hexdigest()
        assert h == sha(ROOT/p)
        original_bindings[p] = h
    write(DOC/'protocol.json', {
        'schema': 'star50_streak_mechanism@1', 'issue': 'fl-wisxs',
        'roles': {'2020': 'warmup_only', '2021-2025': 'development_material_already_consumed',
                  '2026': 'excluded_no_price_or_return_reads'},
        'parent_research_commit': '4f9f01c69353e8e9ea15db341e39c967e5873359',
        'prior_round4_source_incident_preserved': True,
        'new_round_source_identity': 'original_Git_bytes_verified_and_new_dependencies_frozen',
        'original_root_bindings': original_bindings,
        'source_hashes': {p: sha(ROOT/p) for p in SOURCES}, 'inputs': inputs,
        'draws': DRAWS, 'sequence_metrics': STATISTICS, 'sequence_nulls': METHODS,
        'rolling_windows_trades': WINDOWS, 'global_sequence_tests': 12,
        'features': FEATURES, 'stage_days': 5, 'stage_tests': 8,
        'synthetic_cases': 84, 'policy_candidates': 0, 'year_review_order': YEARS,
        'fresh_oos': False, 'production_authority': False,
        'runtime': {n: importlib.import_module(n).__version__
                    for n in ['numpy', 'pandas', 'scipy', 'pyarrow', 'matplotlib']}})
    print('Protocol frozen', sha(DOC/'protocol.json'))


def compute_view(view):
    raw = load_bars(DATA, view)
    assert raw.trading_day.max() <= '2025-12-31'
    f = baseline_frame(raw)
    attributes, lps, bands, _ = properties(f)
    daily = f.groupby('trading_day').agg(pnl_log=('pnl_log', 'sum'), year=('year', 'last'))
    days = list(daily.index)
    daily['eligible'] = daily.index.isin(days[20:-20])
    daily = attributes[FEATURES].join(daily).reset_index()
    daily = daily.loc[daily.year >= 2021].copy()
    daily['day_index'] = daily.groupby('year').cumcount()
    daily['stage'] = daily.day_index//5
    dev = f.loc[f.is_development].copy().reset_index(drop=True)
    for n in (12, 240):
        dev['lp'+str(n)] = lps[n][f.is_development.to_numpy()]
    dev['fast'] = bands[f.is_development.to_numpy(), 0]
    dev['work'] = bands[f.is_development.to_numpy(), 1]
    trades = trade_fragments(dev)
    assert np.isclose(trades.pnl_log.sum(), dev.pnl_log.sum(), atol=1e-12)
    trades['exit_day'] = trades.last_booking.str[:10]
    trades['year'] = trades.exit_day.str[:4].astype(int)
    trades['outcome'] = np.sign(trades.pnl_log).astype(np.int8)
    trades = trades.merge(daily[['trading_day', 'day_index', 'stage']],
                          left_on='exit_day', right_on='trading_day', validate='many_to_one')
    closed = trades.loc[~trades.boundary_clipped].copy()
    rows = []
    for (year, stage), day in daily.groupby(['year', 'stage']):
        t = closed.loc[(closed.year == year) & (closed.stage == stage)]
        rows.append({'year': int(year), 'stage': int(stage), 'first': day.trading_day.iloc[0],
                     'last': day.trading_day.iloc[-1], 'days': len(day), 'n_trades': len(t),
                     'eligible': bool(day.eligible.all() and len(day) == 5 and len(t) > 0),
                     'win_rate': float((t.outcome == 1).mean()) if len(t) else np.nan,
                     'mean_trade_log': float(t.pnl_log.mean()) if len(t) else np.nan,
                     'marked_log_pnl': day.pnl_log.sum(),
                     **{name: day[name].mean() for name in FEATURES}})
    return dev, trades, daily, pd.DataFrame(rows), fingerprint(f)


def prepare():
    check_sources()
    assert not OUT.exists(), 'Preserve prior study output'
    OUT.mkdir()
    bindings = []
    for view in VIEWS:
        f, t, d, stages, metrics = compute_view(view)
        folder = OUT/view
        folder.mkdir()
        f.to_parquet(folder/'bars.parquet', index=False)
        csv(folder/'trades.csv', t)
        csv(folder/'daily.csv', d)
        csv(folder/'stages.csv', stages)
        write(folder/'metrics.json', metrics)
        bindings.append({'view': view, 'bars': len(f), 'fragments': len(t),
                         'closed_trades': int((~t.boundary_clipped).sum()),
                         'last_day': f.trading_day.max()})
    write(OUT/'materialization.json', {'protocol_sha256': sha(DOC/'protocol.json'),
                                     'inputs': bindings, 'new_policies': 0, 'data_2026': False})
    print('Five views materialized from newly bound original source; no annual reviews yet')


def read_trades(view=VIEWS[0]):
    t = pd.read_csv(OUT/view/'trades.csv', float_precision='round_trip')
    return t.loc[~t.boundary_clipped].reset_index(drop=True)


def year_plot(year, t, folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x = np.arange(len(t))
    values = t.outcome.to_numpy()
    losing = runs(values).query('sign == -1').sort_values(['length', 'start'], ascending=[False, True]).iloc[0]
    rolling = pd.Series(values == 1).rolling(50).mean()
    best_end = int(rolling.idxmax())+1
    f = pd.read_parquet(OUT/VIEWS[0]/'bars.parquet')
    fig, axes = plt.subplots(3, 1, figsize=(13, 8), sharex=True, layout='constrained')
    end_indices = t.last_interval_index.astype(int).to_numpy()
    q = f.iloc[end_indices]
    axes[0].plot(x, np.log(q.close), label='Log close at trade end', lw=.8)
    axes[0].plot(x, q.lp240, label='Hindsight slow >5d', lw=1)
    for w in WINDOWS:
        axes[1].plot(x, pd.Series(values == 1).rolling(w).mean(), label=f'{w} trades', lw=.9)
    axes[1].axhline((values == 1).mean(), color='black', ls=':', label='Annual mean')
    axes[2].plot(x, t.pnl_log.cumsum()*100, label='Cumulative closed-trade log PnL (%)')
    for ax in axes:
        ax.axvspan(int(losing.start), int(losing.end)-1, color='red', alpha=.13)
        ax.axvspan(best_end-50, best_end-1, color='green', alpha=.10)
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    ticks = np.linspace(0, len(t)-1, 8).astype(int)
    axes[-1].set_xticks(ticks, t.exit_day.iloc[ticks], rotation=20)
    axes[-1].set_xlabel('Completed-trade order; red=longest loss run, green=best 50-trade window')
    fig.suptitle(f'{year}: fixed original exposure; hindsight components are not live signals')
    fig.savefig(folder/'annual.png', dpi=130)
    plt.close(fig)
    return {'longest_loss_first': t.iloc[int(losing.start)].first_booking,
            'longest_loss_last': t.iloc[int(losing.end)-1].last_booking,
            'longest_loss_trades': int(losing.length),
            'longest_loss_log_pnl': float(t.iloc[int(losing.start):int(losing.end)].pnl_log.sum()),
            'best50_first': t.iloc[best_end-50].first_booking,
            'best50_last': t.iloc[best_end-1].last_booking,
            'best50_win_rate': float(rolling.max())}


def year_pack(year):
    check_sources()
    if year != YEARS[0]:
        assert (OUT/'sessions'/str(year-1)/'receipt.json').exists(), 'Review prior year first'
    folder = OUT/'sessions'/str(year)
    assert not folder.exists(), 'Do not overwrite annual evidence'
    folder.mkdir(parents=True)
    t = read_trades().query('year == @year').reset_index(drop=True)
    values = t.outcome.to_numpy(np.int8)
    p = float((values == 1).mean())
    observed = sequence_stats(values, p)[0]
    for j, method in enumerate(METHODS):
        ids = np.arange(len(t)) if j == 0 else t.day_index.to_numpy() if j == 1 else (t.day_index//5).to_numpy()
        sims = permuted_sequences(values, ids, DRAWS, year*100+j+20260906)
        assert np.all((sims == 1).sum(axis=1) == np.count_nonzero(values == 1))
        assert np.all((sims == -1).sum(axis=1) == np.count_nonzero(values == -1))
        np.save(folder/(method+'.npy'), sims, allow_pickle=False)
    csv(folder/'conditional_win_rate.csv', conditional_wins(values))
    stages = pd.read_csv(OUT/VIEWS[0]/'stages.csv').query('year == @year and eligible')
    associations = []
    for feature in FEATURES:
        for target in ('win_rate', 'mean_trade_log'):
            associations.append({'feature': feature, 'outcome': target,
                                 'rho': float(spearmanr(stages[feature], stages[target]).statistic)})
    csv(folder/'stage_associations.csv', pd.DataFrame(associations))
    summary = {'year': year, 'trades': len(t), 'wins': int((values == 1).sum()),
               'losses': int((values == -1).sum()), 'flats': int((values == 0).sum()), 'win_rate': p,
               'mean_win_log': float(t.loc[t.outcome == 1, 'pnl_log'].mean()),
               'mean_loss_log': float(t.loc[t.outcome == -1, 'pnl_log'].mean()),
               'sequence_statistics': dict(zip(STATISTICS, observed.tolist())),
               'stage_associations': associations, **year_plot(year, t, folder)}
    write(folder/'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False))


def seal(year, review):
    check_sources()
    folder = OUT/'sessions'/str(year)
    assert not (folder/'receipt.json').exists()
    text = json.loads(review.read_text())
    assert text['year'] == year
    assert all(text.get(k) for k in ['observations', 'counterexamples', 'interpretation', 'next_step'])
    write(folder/'review.json', text)
    prior = DOC/'protocol.json' if year == YEARS[0] else OUT/'sessions'/str(year-1)/'receipt.json'
    write(folder/'receipt.json', {'year': year, 'prior_sha256': sha(prior),
                                 'files': {str(p.relative_to(ROOT)): sha(p) for p in sorted(folder.iterdir()) if p.is_file()},
                                 'new_policy': False, 'production_authority': False})
    print('Sealed', year)


def sequence_results():
    t = read_trades()
    values = t.outcome.to_numpy(np.int8)
    rates = t.assign(win=t.outcome == 1).groupby('year').win.mean()
    p = t.year.map(rates).to_numpy()
    observed = sequence_stats(values, p)[0]
    rows = []
    for method in METHODS:
        sims = np.concatenate([np.load(OUT/'sessions'/str(y)/(method+'.npy')) for y in YEARS], axis=1)
        null = sequence_stats(sims, p)
        for j, name in enumerate(STATISTICS):
            rows.append({'null': method, 'statistic': name, 'observed': observed[j],
                         'p': (1+np.sum(null[:, j] >= observed[j]))/(DRAWS+1),
                         'null_median': float(np.median(null[:, j])),
                         'null_q95': float(np.quantile(null[:, j], .95)),
                         'null_q99': float(np.quantile(null[:, j], .99))})
    table = pd.DataFrame(rows)
    table['holm_12_p'] = holm(table.p)
    return table


def analyze():
    check_sources()
    assert all((OUT/'sessions'/str(y)/'receipt.json').exists() for y in YEARS)
    assert not (OUT/'sequence_tests.csv').exists()
    table = sequence_results()
    csv(OUT/'sequence_tests.csv', table)
    print(table.to_string(index=False), flush=True)
    t = read_trades()
    csv(OUT/'conditional_win_rate.csv', conditional_wins(t.outcome.to_numpy()))
    all_runs = runs(t.outcome.to_numpy())
    all_runs['first'] = [t.iloc[a].first_booking for a in all_runs.start]
    all_runs['last'] = [t.iloc[b-1].last_booking for b in all_runs.end]
    csv(OUT/'all_runs.csv', all_runs)
    rolling = []
    for w in WINDOWS:
        rate = pd.Series(t.outcome.to_numpy() == 1).rolling(w).mean()
        for kind, ix in [('worst', int(rate.idxmin())), ('best', int(rate.idxmax()))]:
            rolling.append({'window': w, 'kind': kind, 'win_rate': float(rate.iloc[ix]),
                            'first': t.iloc[ix-w+1].first_booking, 'last': t.iloc[ix].last_booking})
    csv(OUT/'rolling_extremes.csv', pd.DataFrame(rolling))
    associations = []
    for view in VIEWS:
        stages = pd.read_csv(OUT/view/'stages.csv', float_precision='round_trip').query('eligible')
        result = stage_associations(stages)
        result['view'] = view
        csv(OUT/view/'stage_tests.csv', result)
        associations.append(result)
    csv(OUT/'all_stage_tests.csv', pd.concat(associations, ignore_index=True))
    stage = pd.read_csv(OUT/VIEWS[0]/'stages.csv', float_precision='round_trip').query('eligible').copy()
    cells = []
    for name, a, b in [('eff_fast', FEATURES[0], FEATURES[1]), ('slow_threshold', FEATURES[2], FEATURES[3])]:
        labels = (stage[a] > stage[a].median()).astype(int).astype(str)+(stage[b] > stage[b].median()).astype(int).astype(str)
        for label, g in stage.groupby(labels):
            cells.append({'table': name, 'cell': label, 'stages': len(g),
                          'first_threshold': stage[a].median(), 'second_threshold': stage[b].median(),
                          'mean_stage_win_rate': g.win_rate.mean(),
                          'trade_weighted_win_rate': np.average(g.win_rate, weights=g.n_trades),
                          'mean_trade_log': np.average(g.mean_trade_log, weights=g.n_trades),
                          'positive_trade_pnl_stages': int((g.mean_trade_log > 0).sum()),
                          'negative_trade_pnl_stages': int((g.mean_trade_log < 0).sum())})
    csv(OUT/'condition_cells.csv', pd.DataFrame(cells))
    csv(OUT/'synthetic_cases.csv', synthetic_cases())
    write(OUT/'summary.json', {'trades': len(t), 'wins': int((t.outcome == 1).sum()),
                             'losses': int((t.outcome == -1).sum()), 'flats': int((t.outcome == 0).sum()),
                             'win_rate': float((t.outcome == 1).mean()),
                             'mean_win_log': float(t.loc[t.outcome == 1, 'pnl_log'].mean()),
                             'mean_loss_log': float(t.loc[t.outcome == -1, 'pnl_log'].mean()),
                             'stage_count': len(stage), 'new_policy': False, 'fresh_oos': False})


def validate():
    contract = check_sources()
    prior = sha(DOC/'protocol.json')
    for year in YEARS:
        folder = OUT/'sessions'/str(year)
        r = json.loads((folder/'receipt.json').read_text())
        assert r['year'] == year and r['prior_sha256'] == prior
        for path, h in r['files'].items():
            assert sha(ROOT/path) == h
        prior = sha(folder/'receipt.json')
        t = read_trades().query('year == @year')
        for j, method in enumerate(METHODS):
            ids = np.arange(len(t)) if j == 0 else t.day_index.to_numpy() if j == 1 else (t.day_index//5).to_numpy()
            expected = permuted_sequences(t.outcome.to_numpy(), ids, DRAWS, year*100+j+20260906)
            assert np.array_equal(expected, np.load(folder/(method+'.npy')))
    max_error = 0.
    for view in VIEWS:
        f, trades, d, stages, _ = compute_view(view)
        saved = pd.read_parquet(OUT/view/'bars.parquet')
        assert np.array_equal(saved.exec_pos, f.exec_pos)
        assert np.array_equal(saved.pnl_log, f.pnl_log)
        saved_stages = pd.read_csv(OUT/view/'stages.csv', float_precision='round_trip')
        numeric = stages.select_dtypes(include='number').columns
        assert np.allclose(stages[numeric], saved_stages[numeric], equal_nan=True, atol=1e-12)
        expected = stage_associations(stages.query('eligible'))
        actual = pd.read_csv(OUT/view/'stage_tests.csv', float_precision='round_trip')
        numeric = expected.select_dtypes(include='number').columns
        max_error = max(max_error, float(np.max(abs(expected[numeric].to_numpy()-actual[numeric].to_numpy()))))
    expected = sequence_results()
    actual = pd.read_csv(OUT/'sequence_tests.csv', float_precision='round_trip')
    numeric = expected.select_dtypes(include='number').columns
    assert np.allclose(expected[numeric], actual[numeric], atol=1e-12, rtol=0)
    from PIL import Image
    for p in OUT.rglob('*.png'):
        with Image.open(p) as im:
            im.verify()
    assert max_error < 1e-12
    assert len(pd.read_csv(OUT/'synthetic_cases.csv')) == contract['synthetic_cases'] == 84
    result = {'valid': True, 'new_source_closure_passed': True,
              'old_round4_source_failure_not_rewritten': True, 'years_reviewed_in_order': 5,
              'all_five_view_positions_and_pnl_rebuild_exact': True,
              'all_15_null_matrices_rebuild_exact': True, 'stage_statistics_max_abs_error': max_error,
              'sequence_tests': 12, 'stage_tests_primary': 8, 'synthetic_cases': 84,
              'data_2026_used': False, 'new_policies': 0, 'fresh_oos': False, 'production_authority': False}
    write(OUT/'validation.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['freeze', 'prepare', 'year', 'seal', 'analyze', 'validate'])
    ap.add_argument('--year', type=int, choices=YEARS)
    ap.add_argument('--review', type=Path)
    args = ap.parse_args()
    if args.action == 'year':
        year_pack(args.year)
    elif args.action == 'seal':
        seal(args.year, args.review)
    else:
        globals()[args.action]()
