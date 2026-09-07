"""Prepare causal decisions and execute one frozen family in reviewed years."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FACTORLAB = Path('/home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab')
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from reproduce_historical_baseline import load_bars, baseline_frame
from star50_filter.three_proposals import (POLICIES, SIDE_FEE, L3_SOURCES, asof_channel,
    causal_features, compose, execution_fields, load_l3_channel, metrics, trade_ledger)

OUT = ROOT / 'artifacts/three_proposals_v1'
DATA = ROOT / 'artifacts/drawdown_material'
SOURCES = ['src/star50_filter/filters.py', 'src/star50_filter/backtest.py',
    'scripts/reproduce_historical_baseline.py', 'src/star50_filter/three_proposals.py',
    'scripts/run_three_proposals_v1.py', 'tests/test_three_proposals.py',
    'docs/research/three_proposals_v1/method.md']
IDENTITY = ['docs/ops/timing_strategy_identity_registry@2.0.json',
    'src/factor_lab/strategy/research/timing/explosive_v3.py',
    'src/factor_lab/market_state/timing_explosive_layer_v2.py']


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def check(prepared=False):
    frozen = json.loads((OUT / 'freeze.json').read_text())
    for name, expected in frozen['sources'].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in frozen['external_sources'].items():
        assert sha(FACTORLAB / name) == expected, name
    for name, expected in frozen['inputs'].items():
        assert sha(ROOT / name) == expected, name
    if prepared:
        receipt = json.loads((OUT / 'prepared.json').read_text())
        assert receipt['freeze_sha256'] == sha(OUT / 'freeze.json')
        assert sha(OUT / 'signals.parquet') == receipt['signals_sha256']
        assert json.loads((OUT / 'science_acceptance.json').read_text())['account_contract_may_open']
    return frozen


def freeze():
    assert not OUT.exists(), 'Existing freezes are immutable'
    receipt = json.loads((DATA / 'receipt.json').read_text())
    source_map = {r['view_id']: r['export_sha256'] for r in receipt['views']}
    inputs = {}
    for view in ['5m_offset_0', '15m_offset_5']:
        path = DATA / (view + '.parquet')
        assert sha(path) == source_map[view]
        inputs[str(path.relative_to(ROOT))] = sha(path)
    accepted = ROOT / 'artifacts/streak_mechanism_v1/5m_offset_0/bars.parquet'
    accepted_manifest = json.loads((ROOT / 'artifacts/streak_mechanism_v1/manifest.json').read_text())['files']
    assert sha(accepted) == accepted_manifest[str(accepted.relative_to(ROOT))]
    inputs[str(accepted.relative_to(ROOT))] = sha(accepted)
    authority = json.loads((ROOT / 'docs/research/streak_mechanism_v1/protocol.json').read_text())
    for name in SOURCES[:3]:
        assert sha(ROOT / name) == authority['source_hashes'][name]
    save(OUT / 'freeze.json', {'sources': {n: sha(ROOT / n) for n in SOURCES},
        'external_sources': {n: sha(FACTORLAB / n) for n in (*L3_SOURCES, *IDENTITY)},
        'inputs': inputs, 'policy_ids': list(POLICIES),
        'roles': {'2020': 'warmup_and_price_only_q75_calibration',
                  '2021-2025': 'consumed_development', '2026': 'excluded'},
        'a_lookback': 12, 'a_calibration_quantile': .75, 'b_prior_sigma_multiple': 1.,
        'channel_periods_native_15m': [48, 96], 'channel_exit': 'opposite_rail',
        'position_when_admitted': 'original full +1/-1; zero only conditional veto/unclaimed component',
        'fee_proxy_per_side': SIDE_FEE, 'fee_proxy_is_actual_etf_or_option_backtest': False,
        'fresh_oos': False, 'production_authority': False})
    print('Frozen 9 identities, original exposure, exact L3 component and native clocks.')


def prepare():
    check()
    assert not (OUT / 'prepared.json').exists()
    base = baseline_frame(load_bars(DATA, '5m_offset_0'))
    dev = base.loc[base.is_development].reset_index(drop=True)
    old = pd.read_parquet(ROOT / 'artifacts/streak_mechanism_v1/5m_offset_0/bars.parquet')
    assert np.array_equal(dev.exec_pos.to_numpy(), old.exec_pos.to_numpy())
    assert np.array_equal(dev.pnl_log.to_numpy(), old.pnl_log.to_numpy())
    f = causal_features(base.open, base.close)
    q = f.loc[base.year == 2020, 'q12'].dropna()
    cutoff = float(q.quantile(.75))
    native = load_bars(DATA, '15m_offset_5')
    build, spec = load_l3_channel(FACTORLAB)
    prices = pd.Series(native.close.to_numpy(), index=pd.DatetimeIndex(native.timestamp))
    channel = build(prices, spec('opposite_rail', (48, 96)))
    channel.insert(0, 'timestamp', prices.index)
    channel = channel.reset_index(drop=True)
    bridge = asof_channel(base.timestamp, channel)
    output = base[['timestamp', 'trading_day', 'year', 'open', 'close', 'signal_pos']].copy()
    output['previous_open'] = base.open.shift(1)
    output['book_return_log'] = np.r_[0., np.log(base.open.to_numpy()[1:] / base.open.to_numpy()[:-1])]
    output = pd.concat([output, f, bridge], axis=1)
    for policy in POLICIES:
        target, owner, veto = compose(base.signal_pos, f, bridge.channel, cutoff, policy)
        output[policy] = target
        output[policy + '_owner'] = owner
        output[policy + '_veto'] = veto
        for n in [300, int((base.year <= 2020).sum()), len(base) // 2]:
            prefix_features = causal_features(base.open.iloc[:n], base.close.iloc[:n])
            pd.testing.assert_frame_equal(f.iloc[:n], prefix_features)
            part = compose(base.signal_pos.iloc[:n], prefix_features, bridge.channel.iloc[:n], cutoff, policy)
            assert all(np.array_equal(a[:n], b) for a, b in zip((target, owner, veto), part))
    prefix_checks = []
    for n in [400, len(native) // 2]:
        prefix = build(prices.iloc[:n], spec('opposite_rail', (48, 96)))
        assert np.array_equal(prefix.decision_position_for_next_bar,
                              channel.decision_position_for_next_bar.iloc[:n])
        prefix_checks.append(n)
    assert output.trading_day.max() <= '2025-12-31'
    output.to_parquet(OUT / 'signals.parquet', index=False)
    channel.to_parquet(OUT / 'native_channel.parquet', index=False)
    save(OUT / 'science_acceptance.json', {'account_contract_may_open': True,
        'status': 'diagnostic_signal_present_account_contract_may_open',
        'original_signal_and_pnl_exact': True, 'all_veto_prefix_checks_passed': True,
        'channel_prefix_checks': prefix_checks, 'asof_reads_future': False,
        'new_signal_economics_success_assumed': False, 'production_authority': False})
    save(OUT / 'prepared.json', {'freeze_sha256': sha(OUT / 'freeze.json'),
        'signals_sha256': sha(OUT / 'signals.parquet'), 'native_channel_sha256': sha(OUT / 'native_channel.parquet'),
        'q75_2020': cutoff, 'calibration_observations': len(q), 'rows': len(output),
        'main_development_rows': len(dev), 'native_channel_rows': len(native),
        'candidate_real_account_results_computed': False})
    print('Prepared causal inputs and exact original signal; account stage admitted.', cutoff)


def year_snapshot(signals, policy, year, dest, previous_state):
    fields = execution_fields(signals[policy], signals[policy + '_owner'])
    x = pd.concat([signals[['timestamp', 'trading_day', 'year', 'open', 'previous_open',
                           'book_return_log']], fields], axis=1)
    x = x.loc[x.year == year].copy().reset_index(drop=True)
    x['gross_log'] = x.exec_pos * x.book_return_log
    x['fee_log'] = x.turnover_sides * np.log1p(-SIDE_FEE)
    x['net_log'] = x.gross_log + x.fee_log
    state = {}
    for name in ['gross', 'net']:
        before = previous_state.get(name + '_log', 0.)
        peak_before = previous_state.get(name + '_peak', 1.)
        x[name + '_nav'] = np.exp(before + x[name + '_log'].cumsum())
        peaks = np.maximum.accumulate(np.r_[peak_before, x[name + '_nav'].to_numpy()])[1:]
        x[name + '_drawdown'] = 1 - x[name + '_nav'] / peaks
        state[name + '_log'] = float(before + x[name + '_log'].sum())
        state[name + '_peak'] = float(peaks[-1])
    x.to_parquet(dest / (policy + '.parquet'), index=False)
    save(dest / (policy + '_state.json'), state)
    return x


def history(policy, year, current):
    prior = [pd.read_parquet(OUT / str(y) / 'accounts' / (policy + '.parquet'))
             for y in range(2021, year)]
    return pd.concat(prior + [current], ignore_index=True)


def annual(year, baseline_only):
    check(prepared=True)
    if year > 2021:
        assert (OUT / str(year - 1) / 'review.json').exists(), 'Previous year not reviewed'
    mode = 'baseline' if baseline_only else 'accounts'
    dest = OUT / str(year) / mode
    assert not dest.exists()
    if not baseline_only:
        assert (OUT / str(year) / 'baseline_review.json').exists()
    dest.mkdir(parents=True)
    signals = pd.read_parquet(OUT / 'signals.parquet')
    policies = ['F'] if baseline_only else list(POLICIES)
    summaries = []
    for policy in policies:
        if not baseline_only and policy == 'F':
            for suffix in ['.parquet', '_state.json']:
                shutil.copyfile(OUT / str(year) / 'baseline' / (policy + suffix), dest / (policy + suffix))
            x = pd.read_parquet(dest / 'F.parquet')
        else:
            state_path = OUT / str(year - 1) / 'accounts' / (policy + '_state.json')
            state = json.loads(state_path.read_text()) if year > 2021 else {}
            x = year_snapshot(signals, policy, year, dest, state)
        full = history(policy, year, x)
        trade_rows, _ = trade_ledger(full)
        finished = trade_rows.loc[trade_rows.complete.astype(bool) & ~trade_rows.left_clipped.astype(bool)
            & trade_rows.exit_label.str.startswith(str(year))]
        for summary in metrics(full, year - 2020):
            kind = 'gross' if summary['basis'] == 'original_zero_cost' else 'net'
            year_nav = np.exp(x[kind + '_log'].cumsum().to_numpy())
            year_peak = np.maximum.accumulate(np.r_[1., year_nav])[1:]
            summaries.append({'policy': policy, 'year': year, **summary,
                'year_return': float(np.expm1(x[kind + '_log'].sum())),
                'year_mdd': float(np.max(1 - year_nav / year_peak)),
                'year_completed_trades': len(finished),
                'year_mean_trade_log_bp': float(finished[kind + '_log'].mean() * 10000) if len(finished) else 0.})
    pd.DataFrame(summaries).to_csv(dest / 'summary.csv', index=False)
    save(dest / 'receipt.json', {'year': year, 'mode': mode,
        'prepared_sha256': sha(OUT / 'prepared.json'), 'policies': policies,
        'previous_review_sha256': sha(OUT / str(year - 1) / 'review.json') if year > 2021 else sha(OUT / 'science_acceptance.json'),
        'files': {p.name: sha(p) for p in sorted(dest.iterdir()) if p.name != 'receipt.json'}})
    if not baseline_only:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 1, figsize=(13, 8), layout='constrained')
        for policy in POLICIES:
            x = pd.read_parquet(dest / (policy + '.parquet'))
            daily = x.groupby('trading_day', sort=True).tail(1)
            for ax, kind in zip(axes, ['gross', 'net']):
                start_nav = float(x[kind + '_nav'].iloc[0] / np.exp(x[kind + '_log'].iloc[0]))
                ax.plot(pd.to_datetime(daily.trading_day), daily[kind + '_nav'] / start_nav,
                        label=policy, lw=1.8 if policy == 'F' else 1.)
                ax.set_title(f'{year} | {kind} | same full-unit account; year-start normalized for display')
                ax.grid(alpha=.2)
        axes[0].legend(ncol=9, fontsize=8)
        fig.savefig(OUT / str(year) / 'accounts.png', dpi=130)
        plt.close(fig)
    show = pd.DataFrame(summaries)
    print(show.loc[show.basis == 'uniform_fee_proxy', ['policy', 'year_return', 'year_mdd',
        'year_completed_trades', 'year_mean_trade_log_bp', 'exposure_fraction']].to_string(index=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['freeze', 'prepare', 'baseline', 'family'])
    p.add_argument('--year', type=int, choices=range(2021, 2026))
    a = p.parse_args()
    if a.action == 'freeze': freeze()
    elif a.action == 'prepare': prepare()
    else:
        assert a.year is not None
        annual(a.year, a.action == 'baseline')
