"""One-year, no-price order feasibility audit of immutable research orders."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from star50_filter.market_admission import CashT1Inventory, inspect_bundle

OUT = ROOT / 'artifacts/market_admission'
DOC = ROOT / 'docs/research/market_admission'
OLD = ROOT / 'artifacts/execution_counterexamples/sessions'
POLICIES = ('baseline', 'slow_conflict_half')
SOURCES = ['src/star50_filter/market_admission.py',
           'scripts/audit_market_admission.py',
           'docs/research/market_admission/preregistration.json']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def csv(p, df):
    df.to_csv(p, index=False, compression={'method': 'gzip', 'mtime': 0})


def prepare(year):
    if year not in range(2021, 2026):
        raise ValueError('Only consumed 2021-2025 order snapshots')
    folder = OUT / 'sessions' / str(year)
    if folder.exists():
        raise ValueError('Do not overwrite an evidence pack')
    prior = OUT / 'sessions' / str(year - 1)
    previous = None
    initial = {p: CashT1Inventory().snapshot() for p in POLICIES}
    if year > 2021:
        if not (prior / 'seal.json').exists():
            raise ValueError('Review and seal prior year first')
        previous = sha(prior / 'seal.json')
        initial = json.loads((prior / 'summary.json').read_text())['final_inventory']
    old = OLD / str(year)
    evidence = json.loads((old / 'evidence.json').read_text())
    input_hashes = {}
    for name in ('orders.csv.gz', 'minute_marks.csv.gz', 'snapshot_boundaries.json'):
        h = sha(old / name)
        if h != evidence['files'][name]:
            raise ValueError('Sealed input changed')
        input_hashes[str((old / name).relative_to(ROOT))] = h
    # No source prices, returns, or new signals are loaded.
    marks = pd.read_csv(old / 'minute_marks.csv.gz', usecols=['timestamp', 'trading_day'])
    orders = pd.read_csv(old / 'orders.csv.gz', usecols=[
        'timestamp', 'trading_day', 'q_after', 'view', 'scenario', 'policy'])
    orders = orders[(orders.view == 0) & (orders.scenario == 'delay_1m_observed')]
    bounds = json.loads((old / 'snapshot_boundaries.json').read_text())
    summaries, final, timelines, events = [], {}, [], []
    for policy in POLICIES:
        b = next(x for x in bounds if x['view'] == 0 and
                 x['scenario'] == 'delay_1m_observed' and x['policy'] == policy)
        m = marks[(marks.timestamp >= b['start']) & (marks.timestamp <= b['end'])]
        o = orders[orders.policy == policy]
        assert not o.timestamp.duplicated().any()
        event_map = dict(zip(o.timestamp, o.q_after))
        assert set(event_map) <= set(m.timestamp)
        state = CashT1Inventory(**initial[policy])
        signed = int(round(2 * b['initial_q_before']))
        rows, ev = [], []
        for timestamp, day in m.itertuples(index=False, name=None):
            new_day = state.advance(day)
            has_order = timestamp in event_map
            if has_order:
                raw_target = 2 * event_map[timestamp]
                if raw_target != round(raw_target):
                    raise ValueError('Noninteger frozen diagnostic target')
                signed = int(raw_target)
            if has_order or (new_day and state.total != max(signed, 0)):
                result = state.request(signed)
                ev.append({'policy': policy, 'timestamp': timestamp, 'trading_day': day,
                           'trigger': 'frozen_order' if has_order else 'next_day_pending', **result})
            rows.append({'policy': policy, 'timestamp': timestamp, 'trading_day': day,
                         'signed_target': signed, 'cash_target': max(signed, 0),
                         'inventory': state.total, 'settled': state.settled, 'locked': state.locked})
        d, e = pd.DataFrame(rows), pd.DataFrame(ev)
        blocked = e[e.blocked_sell > 0]
        summaries.append({'policy': policy, 'minute_observations': len(d),
            'negative_target_minutes': int((d.signed_target < 0).sum()),
            'negative_target_share': float((d.signed_target < 0).mean()),
            'cash_mismatch_minutes': int((d.inventory != d.cash_target).sum()),
            'cash_mismatch_share': float((d.inventory != d.cash_target).mean()),
            'frozen_order_events': int((e.trigger == 'frozen_order').sum()),
            'next_day_pending_events': int((e.trigger == 'next_day_pending').sum()),
            'blocked_sell_events': len(blocked),
            'blocked_sell_units_requested': int(blocked.blocked_sell.sum()),
            'first_blocked_sale': blocked.iloc[0].to_dict() if len(blocked) else None})
        final[policy] = state.snapshot()
        timelines.append(d)
        events.append(e)
    folder.mkdir(parents=True)
    timeline, event = pd.concat(timelines), pd.concat(events)
    csv(folder / 'inventory_minutes.csv.gz', timeline)
    csv(folder / 'requests.csv.gz', event)
    summary = {'year': year, 'metrics': summaries, 'initial_inventory': initial,
               'final_inventory': final, 'prior_receipt_sha256': previous,
               'no_prices_or_returns_loaded': True, 'tradable_pnl_computed': False,
               'input_hashes': input_hashes,
               'source_hashes': {name: sha(ROOT / name) for name in SOURCES}}
    write_json(folder / 'summary.json', summary)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['svg.hashsalt'] = 'star50-cash-feasibility-v1'
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), constrained_layout=True)
    for ax, policy, metric in zip(axes, POLICIES, summaries):
        day = metric['first_blocked_sale']['trading_day'] if metric['first_blocked_sale'] else timeline.trading_day.iloc[0]
        d = timeline[(timeline.policy == policy) & (timeline.trading_day == day)]
        ax.step(pd.to_datetime(d.timestamp), d.signed_target, where='post', label='signed index target', alpha=.6)
        ax.step(pd.to_datetime(d.timestamp), d.cash_target, where='post', label='clipped cash target')
        ax.step(pd.to_datetime(d.timestamp), d.inventory, where='post', label='T+1 eligible inventory')
        ax.set_title(f'{policy}: first blocked-sale day {day}')
        ax.set_ylabel('Abstract units; no PnL')
        ax.grid(alpha=.2)
        ax.legend(fontsize=8, loc='best')
    fig.savefig(folder / 'first_counterexample.svg', metadata={'Date': None})
    fig.savefig(folder / 'first_counterexample.png', dpi=110)
    plt.close(fig)
    print(json.dumps(summary, ensure_ascii=False))


def seal(year):
    folder = OUT / 'sessions' / str(year)
    if (folder / 'seal.json').exists():
        raise ValueError('Already sealed')
    analysis = json.loads((folder / 'analysis.json').read_text())
    assert analysis['year'] == year and analysis['figure_reviewed']
    assert analysis['event_interpretation'] and analysis['limitation']
    summary = json.loads((folder / 'summary.json').read_text())
    write_json(folder / 'seal.json', {'year': year,
        'prior_receipt_sha256': summary['prior_receipt_sha256'],
        'protocol_sha256': sha(DOC / 'preregistration.json'),
        'files': {p.name: sha(p) for p in sorted(folder.iterdir()) if p.suffix != '.png'}})


def validate():
    previous, final, count = None, None, 0
    for year in range(2021, 2026):
        folder = OUT / 'sessions' / str(year)
        seal_doc = json.loads((folder / 'seal.json').read_text())
        summary = json.loads((folder / 'summary.json').read_text())
        assert seal_doc['year'] == year
        assert seal_doc['prior_receipt_sha256'] == previous == summary['prior_receipt_sha256']
        assert seal_doc['protocol_sha256'] == sha(DOC / 'preregistration.json')
        for name, h in seal_doc['files'].items():
            assert sha(folder / name) == h
            count += 1
        for name, h in (summary['input_hashes'] | summary['source_hashes']).items():
            assert sha(ROOT / name) == h
        assert final is None or final == summary['initial_inventory']
        requests = pd.read_csv(folder / 'requests.csv.gz')
        for policy in POLICIES:
            state = CashT1Inventory(**summary['initial_inventory'][policy])
            for r in requests[requests.policy == policy].to_dict('records'):
                state.advance(r['trading_day'])
                expected = state.request(r['signed_target'])
                assert all(expected[k] == r[k] for k in expected)
            # Settlement can occur on days with no order request.
            state.advance(summary['final_inventory'][policy]['trading_day'])
            assert state.snapshot() == summary['final_inventory'][policy]
        final = summary['final_inventory']
        previous = sha(folder / 'seal.json')
    manifest = OUT / 'manifest.json'
    if manifest.exists():
        for name, h in json.loads(manifest.read_text())['files'].items():
            assert sha(ROOT / name) == h
    print(json.dumps({'status': 'pass', 'annual_sessions': 5, 'sealed_files': count,
                      'inventory_event_replay': True, 'tradable_pnl_computed': False}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--year', type=int)
    group.add_argument('--seal', type=int)
    group.add_argument('--validate', action='store_true')
    group.add_argument('--inspect-bundle', type=Path)
    args = ap.parse_args()
    if args.year is not None:
        prepare(args.year)
    elif args.seal is not None:
        seal(args.seal)
    elif args.inspect_bundle:
        print(json.dumps(inspect_bundle(args.inspect_bundle), ensure_ascii=False))
    else:
        validate()
