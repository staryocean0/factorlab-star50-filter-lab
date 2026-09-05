"""Prepare exactly one year of frozen-policy execution evidence, then stop."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from reproduce_historical_baseline import _normalise_bars
from star50_filter.drawdown_research import causal_states, targets, account
from star50_filter.drawdown_diagnostics import drawdown_summary
from star50_filter.execution_audit import (SCENARIOS, POLICIES, endpoint_audit,
    schedule_sources, minute_account, reprice, condition_attribution,
    signed_opportunity, wall_close, publication_clock, coarse_open_clock)

OUT = ROOT / 'artifacts/execution_counterexamples'
PROTOCOL = ROOT / 'docs/research/execution_counterexamples/preregistration.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                              default=str, allow_nan=False) + '\n')


def load(data_dir, view, year):
    if year not in range(2021, 2026):
        raise ValueError('Only registered development years')
    p = data_dir / (view + '.parquet')
    receipt = json.loads((ROOT / 'artifacts/drawdown_conditions/input_material_receipt.json').read_text())
    expected = next(v for v in receipt['views'] if v['view_id'] == view)
    h = sha(p)
    if h not in (expected['source_sha256'], expected['export_sha256']):
        raise ValueError('Unregistered data bytes: ' + view)
    d = pd.read_parquet(p, filters=[('trading_day', '<=', f'{year}-12-31')])
    d = _normalise_bars(d)
    assert d.year.max() <= year
    return d, {'view': view, 'sha256': h, 'rows': len(d),
               'last_day': d.trading_day.max(), 'filter_max_day': f'{year}-12-31'}


def metrics(net, days, exposure, turnover, cost, years=1):
    daily = pd.Series(net).groupby(np.asarray(days)).sum()
    ds = drawdown_summary(np.asarray(net), top_n=0)
    dd = drawdown_summary(daily.to_numpy(), top_n=0)
    return {'cagr': float(np.expm1(np.sum(net) / years)),
            'total_log_return': float(np.sum(net)), 'mdd': ds['mdd'],
            'daily_mdd': dd['mdd'],
            'longest_underwater_days': dd['longest_underwater_observations'],
            'mean_exposure': float(np.mean(exposure)),
            'turnover': float(np.sum(turnover)), 'cost_log': float(np.sum(cost)),
            'daily_sharpe': float(daily.mean() / daily.std(ddof=1) * np.sqrt(252))}


def csv(path, data):
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    comp = {'method': 'gzip', 'mtime': 0} if str(path).endswith('.gz') else None
    data.to_csv(path, index=False, compression=comp)


def prepare(data_dir, year):
    out = OUT / 'sessions' / str(year)
    if (out / 'evidence.json').exists():
        raise ValueError('Evidence already written; use a new version, not overwrite')
    prior = OUT / 'sessions' / str(year - 1) / 'seal.json'
    if year > 2021 and not prior.exists():
        raise ValueError('Review and seal prior year before opening next')
    out.mkdir(parents=True, exist_ok=True)
    minute, mr = load(data_dir, '1m_official', year)
    current_minute = minute.loc[minute.year == year]
    syn = current_minute.source_kind.str.contains('causal_flat_missing_minute')
    source_audit = {'year': year, 'minute_rows': len(current_minute),
                    'synthetic_minutes': int(syn.sum()),
                    'synthetic_clock_counts': current_minute.loc[syn, 'timestamp'].dt.strftime('%H:%M').value_counts().to_dict(),
                    'source_kind_counts': current_minute.source_kind.value_counts().to_dict(),
                    'availability_offset_patterns': current_minute.available_at.astype(str).str[-6:].value_counts().to_dict(),
                    'views': []}
    rows, daily_rows, cell_rows, opportunities, order_frames, episode_rows = [], [], [], [], [], []
    input_receipts = [mr]
    snapshot_boundaries, parity = [], []
    minute_mark = pd.DataFrame({'timestamp': wall_close(current_minute) - np.timedelta64(1, 'm'),
                               'trading_day': current_minute.trading_day,
                               'mark_open': current_minute.open,
                               'market_log_return': np.r_[0., np.diff(np.log(minute.open.to_numpy()))][minute.year.to_numpy() == year]})
    csv(out / 'minute_marks.csv.gz', minute_mark)
    for view in range(5):
        bars, br = load(data_dir, f'5m_offset_{view}', year)
        input_receipts.append(br)
        states = causal_states(bars, 48 if view == 0 else 46)
        ts = targets(states)
        ea = endpoint_audit(bars, minute)
        source_audit['views'].append({'view': view, **ea})
        if ea['open_mismatches'] or ea['close_mismatches']:
            raise ValueError('Coarse/minute endpoint mismatch invalidates bridge')
        for scenario in SCENARIOS:
            src = schedule_sources(bars, minute, scenario)
            snapshots = {p: minute_account(bars, minute, ts[p], scenario,
                         terminal_liquidation=(year == 2025), active_sources=src)
                         for p in ('baseline', 'slow_conflict_half')}
            b, s = snapshots['baseline'], snapshots['slow_conflict_half']
            take = b.trading_day.str[:4].astype(int).to_numpy() == year
            annual = b.loc[take]
            alpha = float(s.loc[take, 'q_before'].abs().sum() / annual.q_before.abs().sum())
            cell = condition_attribution(b, states)
            # Sparse positions plus immutable minute marks form a complete
            # cost-independent AccountSnapshot. Reports need no source replay.
            for name, snap in snapshots.items():
                z = snap.loc[take]
                changed = z.turnover > 0
                orders = z.loc[changed, ['timestamp', 'trading_day', 'mark_open',
                                        'q_before', 'q_after', 'turnover',
                                        'source_after', 'synthetic_mark']].copy()
                source_i = orders.source_after.to_numpy(dtype=int)
                orders['source_close'] = wall_close(bars)[np.maximum(source_i, 0)]
                orders['source_available'] = publication_clock(bars)[np.maximum(source_i, 0)]
                orders['view'], orders['scenario'], orders['policy'] = view, scenario, name
                orders['event_type'] = np.where(orders.q_after == 0, 'liquidation',
                    np.where(orders.q_before == 0, 'entry',
                    np.where(orders.q_before * orders.q_after < 0, 'reverse', 'resize')))
                order_frames.append(orders)
                snapshot_boundaries.append({'view': view, 'scenario': scenario, 'policy': name,
                    'start': str(z.timestamp.iloc[0]), 'end': str(z.timestamp.iloc[-1]),
                    'initial_q_before': float(z.q_before.iloc[0]),
                    'final_q_after': float(z.q_after.iloc[-1]),
                    'bars': len(z), 'gross_log_pnl': float(z.gross_log_pnl.sum()),
                    'turnover': float(z.turnover.sum()),
                    'snapshot_array_sha256': hashlib.sha256(z[['q_before','q_after','gross_log_pnl','turnover']].to_numpy('<f8').tobytes()).hexdigest()})
            for cost in [0, 1, 3, 5]:
                bn, bc = reprice(b, cost)
                sn, sc = reprice(s, cost)
                opportunities.append({'year': year, 'view': view, 'scenario': scenario,
                    'cost_bps': cost, 'comparison': 'slow_vs_baseline',
                    **signed_opportunity(b, s, bc, sc, take)})
                # Required same-exposure reference. Its alpha is hindsight only.
                mn, mc = reprice(b, cost, alpha)
                opportunities.append({'year': year, 'view': view, 'scenario': scenario,
                    'cost_bps': cost, 'comparison': 'slow_vs_matched_constant',
                    'alpha': alpha, 'gross_delta_log': float((s.gross_log_pnl.to_numpy()-alpha*b.gross_log_pnl.to_numpy())[take].sum()),
                    'cost_savings_log': float((mc-sc)[take].sum()),
                    'net_delta_log': float((sn-mn)[take].sum())})
                for name, snapshot, scale in [
                    ('baseline', b, 1.), ('slow_conflict_half', s, 1.),
                    ('constant_075', b, .75), ('constant_050', b, .5),
                    ('matched_constant', b, alpha)]:
                    net, fee = reprice(snapshot, cost, scale)
                    rows.append({'year': year, 'view': view, 'scenario': scenario,
                        'cost_bps': cost, 'policy': name, 'alpha': scale,
                        **metrics(net[take], annual.trading_day, scale*snapshot.loc[take, 'q_before'].abs(),
                            scale*snapshot.loc[take, 'turnover'], fee[take])})
                    dayframe = pd.DataFrame({'trading_day': annual.trading_day.to_numpy(),
                        'net_log_pnl': net[take], 'gross_log_pnl': scale*snapshot.loc[take, 'gross_log_pnl'].to_numpy(),
                        'cost_log': fee[take], 'turnover': scale*snapshot.loc[take, 'turnover'].to_numpy()})
                    d = dayframe.groupby('trading_day').sum().reset_index()
                    d['view'], d['scenario'], d['policy'], d['cost_bps'] = view, scenario, name, cost
                    daily_rows.append(d)
                for c in ['neither', 'chop_only', 'slow_only', 'both']:
                    mask = take & (cell == c)
                    cell_rows.append({'year': year, 'view': view, 'scenario': scenario,
                        'cost_bps': cost, 'cell': c, 'minutes': int(mask.sum()),
                        'base_gross_log': float(b.gross_log_pnl[mask].sum()),
                        'base_net_log': float(bn[mask].sum()),
                        'slow_gross_log': float(s.gross_log_pnl[mask].sum()),
                        'slow_net_log': float(sn[mask].sum())})
                # Events are within-year descriptive drawdowns, not isolated
                # annual accounts and not a fresh challenge.
                if view in (0, 4) and cost in (0, 3):
                    dd = drawdown_summary(bn[take], top_n=10)
                    idx = np.flatnonzero(take)
                    for rank, event in enumerate(dd['episodes'], 1):
                        for phase, lo, hi in [('decline', event['peak_index'], event['trough_index']),
                                ('recovery', event['trough_index'], event['end_index'])]:
                            if hi <= lo:
                                continue
                            mask = np.zeros(len(b), dtype=bool)
                            mask[idx[lo:hi]] = True
                            episode_rows.append({'year': year, 'view': view, 'scenario': scenario,
                                'cost_bps': cost, 'rank': rank, 'phase': phase, 'mdd': event['drawdown'],
                                'start': str(annual.timestamp.iloc[max(0,lo-1)]),
                                'end': str(annual.timestamp.iloc[min(hi-1,len(annual)-1)]),
                                'minutes': int(mask.sum()), 'days': b.loc[mask,'trading_day'].nunique(),
                                'baseline_net_log': float(bn[mask].sum()),
                                'slow_net_log': float(sn[mask].sum()),
                                'matched_net_log': float(mn[mask].sum()),
                                'slow_vs_matched_log': float((sn-mn)[mask].sum()),
                                'conflict_share': float(np.isin(cell[mask],['slow_only','both']).mean()),
                                'both_share': float((cell[mask]=='both').mean()),
                                **signed_opportunity(b,s,bc,sc,mask)})
            if scenario == 'legacy_on_minute':
                # Check exact cumulative NAV at original coarse endpoints.
                for name in ('baseline', 'slow_conflict_half'):
                    snap = snapshots[name]
                    original = account(bars, ts[name], 3, terminal_liquidation=(year == 2025))
                    mask = original.is_development.to_numpy()
                    coarse_time = coarse_open_clock(bars, minute)[mask]
                    loc = np.searchsorted(snap.timestamp.to_numpy(), coarse_time)
                    new, _ = reprice(snap,3)
                    old = original.net_log_pnl.to_numpy()[mask]
                    # Nonterminal old runner books an extra last-order change,
                    # which bridge also applies at that same scheduled open.
                    err = float(np.max(abs(np.cumsum(new)[loc]-np.cumsum(old))))
                    if err > 1e-10:
                        raise AssertionError(f'Historical path bridge failed {year}/{view}/{name}: {err}')
                    parity.append({'view':view,'policy':name,'max_nav_log_error':err,
                        'five_minute_mdd':drawdown_summary(old,top_n=0)['mdd']})
    csv(out/'annual_metrics.csv',rows)
    csv(out/'daily_accounts.csv.gz',pd.concat(daily_rows,ignore_index=True))
    csv(out/'condition_cells.csv',cell_rows)
    csv(out/'opportunity_attribution.csv',opportunities)
    csv(out/'top10_events.csv',episode_rows)
    csv(out/'orders.csv.gz',pd.concat(order_frames,ignore_index=True))
    write_json(out/'snapshot_boundaries.json',snapshot_boundaries)
    write_json(out/'source_audit.json',source_audit)
    write_json(out/'bridge_parity.json',parity)
    # Figure is part of the one-year evidence reviewed before sealing.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['svg.hashsalt']='star50-execution-audit-v1'
    d=pd.concat(daily_rows,ignore_index=True)
    fig,ax=plt.subplots(2,2,figsize=(12,6),constrained_layout=True)
    for j,scenario in enumerate(SCENARIOS):
        axis=ax.flat[j]
        for policy in ['baseline','slow_conflict_half','constant_050']:
            z=d[(d.view==0)&(d.scenario==scenario)&(d.policy==policy)&(d.cost_bps==3)].sort_values('trading_day')
            axis.plot(pd.to_datetime(z.trading_day),np.exp(z.net_log_pnl.cumsum()),label=policy,linewidth=1.1)
        axis.set_title(f'{year} | {scenario} | 3bp');axis.grid(alpha=.2)
    ax.flat[0].legend(fontsize=7)
    fig.savefig(out/'annual.svg',metadata={'Date':None})
    fig.savefig(out/'annual.png',dpi=110)
    plt.close(fig)
    files={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='annual.png'}
    source_files=['scripts/run_execution_audit.py','src/star50_filter/execution_audit.py',
        'src/star50_filter/drawdown_research.py','src/star50_filter/filters.py',
        'src/star50_filter/drawdown_diagnostics.py','scripts/reproduce_historical_baseline.py']
    write_json(out/'evidence.json',{'schema':'execution_audit_year@1','year':year,
        'prior_receipt_sha256':sha(prior) if year>2021 else None,
        'frozen_policy_sha256':sha(PROTOCOL),'max_input_year':year,
        'inputs':input_receipts,'files':files,
        'source_digests':{p:sha(ROOT/p) for p in source_files},
        'new_strategy_candidates':0,'fresh_oos':False,'production_authority':False})
    table=pd.DataFrame(rows)
    print(table[(table.view==0)&(table.policy.isin(['baseline','slow_conflict_half','matched_constant']))&(table.cost_bps.isin([0,3]))][
        ['scenario','cost_bps','policy','cagr','mdd','longest_underwater_days']].to_string(index=False))
    print(json.dumps(source_audit,ensure_ascii=False))


def seal(year):
    out=OUT/'sessions'/str(year)
    if (out/'seal.json').exists():raise ValueError('Already sealed')
    evidence=json.loads((out/'evidence.json').read_text())
    analysis=json.loads((out/'analysis.json').read_text())
    assert analysis['year']==year and analysis['main_agent_reviewed']
    for key in ['graphical_evidence','observations','mechanism_verdict','next_step']:
        assert analysis[key]
    for f,h in evidence['files'].items():assert sha(out/f)==h
    write_json(out/'seal.json',{'year':year,'prior_receipt_sha256':evidence['prior_receipt_sha256'],
        'frozen_policy_sha256':sha(PROTOCOL),'evidence_sha256':sha(out/'evidence.json'),
        'analysis_sha256':sha(out/'analysis.json'),'fresh_oos':False,'production_authority':False})
    print(f'Sealed {year}: {sha(out/"seal.json")}')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-dir',type=Path,default=ROOT/'artifacts/drawdown_material')
    parser.add_argument('command',choices=['prepare','seal'])
    parser.add_argument('--year',type=int,required=True,choices=range(2021,2026))
    args=parser.parse_args()
    prepare(args.data_dir,args.year) if args.command=='prepare' else seal(args.year)
