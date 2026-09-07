"""Read account snapshots for all reports; do not execute policies here."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from star50_filter.three_proposals import POLICIES, metrics, trade_ledger

OUT = ROOT / 'artifacts/three_proposals_v1'


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def clustering(signals, cutoff):
    rows = []
    for day, group in signals.loc[signals.year >= 2021].groupby('trading_day', sort=True):
        assert len(group) == 48
        for slot in range(4):
            r = group.return_log.to_numpy()[slot * 12:(slot + 1) * 12]
            q = 12 * np.sum(r * r) / np.sum(abs(r)) ** 2
            assert np.isfinite(q)
            rows.append({'day': day, 'year': int(day[:4]), 'slot': slot,
                         'q': float(q), 'high': bool(q > cutoff)})
    blocks = pd.DataFrame(rows)
    pairs = []
    for a, b in zip(rows[:-1], rows[1:]):
        if a['year'] != b['year']:
            continue
        pairs.append({'year': a['year'], 'context': 'within_day' if a['day'] == b['day'] else 'next_trading_day',
            'past_day': a['day'], 'next_day': b['day'], 'past_high': a['high'], 'next_high': b['high']})
    f = pd.DataFrame(pairs)
    contexts = ['within_day', 'next_trading_day']
    observed, arrays, group_indices, summary = [], [], [], []
    for context in contexts:
        sub = f.loc[f.context == context].reset_index(drop=True)
        values = sub[['past_high', 'next_high']].to_numpy(float)
        groups = [np.flatnonzero(sub.year.to_numpy() == y) for y in range(2021, 2026)]
        for ix in groups:
            values[ix] -= values[ix].mean(axis=0)
        values /= np.sqrt(np.sum(values ** 2, axis=0))
        corr = float(values[:, 0] @ values[:, 1])
        observed.append(corr)
        arrays.append(values)
        group_indices.append(groups)
        summary.append({'context': context, 'pairs': len(sub),
            'past_high_count': int(sub.past_high.sum()),
            'p_next_high_given_high': float(sub.loc[sub.past_high, 'next_high'].mean()),
            'p_next_high_given_low': float(sub.loc[~sub.past_high, 'next_high'].mean()),
            'p_next_high_unconditional': float(sub.next_high.mean()),
            'year_centered_phi': corr})
    rng = np.random.default_rng(202609069)
    for method in ['circular20', 'block20']:
        null = np.zeros((1999, 2))
        for k in range(1999):
            for j, (values, groups) in enumerate(zip(arrays, group_indices)):
                order = np.arange(len(values))
                for ix in groups:
                    if method == 'circular20':
                        order[ix] = np.roll(ix, rng.integers(20, len(ix) - 19))
                    else:
                        chunks = [ix[n:n + 20] for n in range(0, len(ix), 20)]
                        order[ix] = np.concatenate([chunks[n] for n in rng.permutation(len(chunks))])
                null[k, j] = values[order, 0] @ values[:, 1]
        maximum = abs(null).max(axis=1)
        for j, row in enumerate(summary):
            row[method + '_maxT_p'] = float((1 + np.sum(maximum >= abs(observed[j]))) / 2000)
        np.save(OUT / ('cluster_' + method + '.npy'), null)
    blocks.to_csv(OUT / 'nonoverlap_blocks.csv', index=False)
    f.to_csv(OUT / 'nonoverlap_pairs.csv', index=False)
    save('clustering.json', summary)
    return summary


def veto_reference(base_trades, accounts):
    complete = base_trades.loc[base_trades.complete.astype(bool) & ~base_trades.left_clipped.astype(bool)].copy()
    values = complete.net_log.to_numpy()
    groups = [np.flatnonzero(complete.entry_label.str[:4].to_numpy() == str(y)) for y in range(2021, 2026)]
    entry_indices = complete.entry_index.to_numpy(int)
    masks = np.column_stack([accounts[p].filled_position.to_numpy()[entry_indices] == 0
                             for p in ['A', 'B', 'AB']])
    observed = -(values[:, None] * masks).sum(axis=0)
    rng = np.random.default_rng(202609070)
    null = np.zeros((999, 3))
    for k in range(999):
        moved = masks.copy()
        for ix in groups:
            moved[ix] = np.roll(masks[ix], rng.integers(1, len(ix)), axis=0)
        assert np.array_equal(moved.sum(axis=0), masks.sum(axis=0))
        null[k] = -(values[:, None] * moved).sum(axis=0)
    mu, std = null.mean(axis=0), np.maximum(null.std(axis=0), 1e-12)
    z = (observed - mu) / std
    reference = ((null - mu) / std).max(axis=1)
    result = []
    for j, policy in enumerate(['A', 'B', 'AB']):
        denied = complete.loc[masks[:, j]]
        result.append({'policy': policy, 'complete_baseline_trade_denominator': len(complete),
            'denied_complete_trades': len(denied),
            'avoided_net_log': float(observed[j]), 'random_location_mean': float(mu[j]),
            'standardized_improvement': float(z[j]),
            'one_sided_three_test_maxT_p': float((1 + np.sum(reference >= z[j])) / 1000),
            'denied_mean_net_log_bp': float(denied.net_log.mean() * 10000) if len(denied) else 0.,
            'denied_profit_count': int((denied.net_log > 0).sum()),
            'denied_loss_count': int((denied.net_log < 0).sum()),
            'forgone_complete_gross_profit_log': float(denied.gross_log.clip(lower=0).sum()),
            'avoided_complete_gross_loss_log': float(-denied.gross_log.clip(upper=0).sum())})
    np.save(OUT / 'veto_location_null.npy', null)
    save('veto_reference.json', result)
    return result


def main():
    for year in range(2021, 2026):
        assert (OUT / str(year) / 'review.json').exists(), 'Annual controller review incomplete'
    accounts, all_rows, quarters = {}, [], []
    for policy in POLICIES:
        bars = pd.concat([pd.read_parquet(OUT / str(y) / 'accounts' / (policy + '.parquet'))
                          for y in range(2021, 2026)], ignore_index=True)
        accounts[policy] = bars
        for row in metrics(bars, 5):
            all_rows.append({'policy': policy, **row})
        trades, orders = trade_ledger(bars)
        target = OUT / 'ledgers' / policy
        target.mkdir(parents=True, exist_ok=True)
        trades.to_parquet(target / 'trades.parquet', index=False)
        orders.to_parquet(target / 'orders.parquet', index=False)
        g = bars.assign(quarter=pd.to_datetime(bars.timestamp).dt.to_period('Q').astype(str))
        summary = g.groupby('quarter')[['gross_log', 'net_log', 'turnover_sides']].sum().reset_index()
        summary['policy'] = policy
        quarters.append(summary)
    table = pd.DataFrame(all_rows)
    baseline = table.loc[table.policy == 'F'].set_index('basis')
    for i, row in table.iterrows():
        base = baseline.loc[row.basis]
        table.loc[i, 'delta_mdd'] = row.mdd - base.mdd
        table.loc[i, 'delta_mean_trade_log_bp'] = row.mean_trade_log_bp - base.mean_trade_log_bp
        table.loc[i, 'trade_reduction'] = 1 - row.completed_trades / base.completed_trades
        table.loc[i, 'cagr_retained'] = row.cagr / base.cagr
        table.loc[i, 'joint_goals'] = bool(row.mdd < base.mdd - 1e-12
            and row.mean_trade_log_bp > base.mean_trade_log_bp + 1e-9
            and row.completed_trades < base.completed_trades)
    table.to_csv(OUT / 'comparison.csv', index=False)
    pd.concat(quarters).to_csv(OUT / 'quarterly.csv', index=False)
    annual = pd.concat([pd.read_csv(OUT / str(y) / 'accounts/summary.csv') for y in range(2021, 2026)])
    annual.to_csv(OUT / 'annual.csv', index=False)
    base_bars = accounts['F']
    decompositions = []
    for policy, bars in accounts.items():
        flat = bars.exec_pos.to_numpy() == 0
        replaced = (bars.exec_pos.to_numpy() != base_bars.exec_pos.to_numpy()) & ~flat
        avoided = float(-base_bars.gross_log.to_numpy()[flat].clip(max=0).sum())
        forgone = float(base_bars.gross_log.to_numpy()[flat].clip(min=0).sum())
        changed = float((bars.gross_log.to_numpy() - base_bars.gross_log.to_numpy())[replaced].sum())
        saved = float(bars.fee_log.sum() - base_bars.fee_log.sum())
        delta = float(bars.net_log.sum() - base_bars.net_log.sum())
        assert abs(delta - (avoided - forgone + changed + saved)) < 1e-10
        decompositions.append({'policy': policy, 'delta_net_log': delta,
            'avoided_negative_interval_log': avoided, 'forgone_positive_interval_log': forgone,
            'direction_replacement_delta_log': changed, 'saved_fee_log': saved,
            'channel_booked_interval_share': float((bars.booked_owner == 2).mean()),
            'filter_booked_interval_share': float((bars.booked_owner == 1).mean())})
    pd.DataFrame(decompositions).to_csv(OUT / 'interval_decomposition.csv', index=False)
    signals = pd.read_parquet(OUT / 'signals.parquet')
    cutoff = json.loads((OUT / 'prepared.json').read_text())['q75_2020']
    cluster = clustering(signals, cutoff)
    base_trades, _ = trade_ledger(base_bars)
    reference = veto_reference(base_trades, accounts)
    print(table[['policy', 'basis', 'cagr', 'mdd', 'completed_trades',
                 'mean_trade_log_bp', 'calmar', 'joint_goals']].to_string(index=False))
    print(json.dumps(cluster, ensure_ascii=False, indent=2))
    print(json.dumps(reference, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
