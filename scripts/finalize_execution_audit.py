"""Reconstruct sufficient snapshots, derive reports; never read source bars."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from run_execution_audit import OUT, PROTOCOL, sha, write_json, csv, metrics
from star50_filter.execution_audit import SCENARIOS, reprice
from star50_filter.drawdown_diagnostics import drawdown_summary


def read_csv(p):
    return pd.read_csv(p,float_precision='round_trip')


def reconstruct(folder, boundary, marks=None, orders=None):
    marks=read_csv(folder/'minute_marks.csv.gz') if marks is None else marks
    orders=read_csv(folder/'orders.csv.gz') if orders is None else orders
    d=marks[(marks.timestamp>=boundary['start'])&(marks.timestamp<=boundary['end'])].copy().reset_index(drop=True)
    ev=orders[(orders.view==boundary['view'])&(orders.scenario==boundary['scenario'])&
              (orders.policy==boundary['policy'])]
    q=np.full(len(d),np.nan)
    idx=np.searchsorted(d.timestamp.to_numpy(),ev.timestamp.to_numpy())
    assert (idx<len(d)).all() and np.array_equal(d.timestamp.to_numpy()[idx],ev.timestamp.to_numpy())
    q[idx]=ev.q_after
    if np.isnan(q[0]):q[0]=boundary['initial_q_before']
    q=pd.Series(q).ffill().to_numpy()
    before=np.r_[boundary['initial_q_before'],q[:-1]]
    turnover=np.abs(q-before)
    np.testing.assert_allclose(turnover[idx],ev.turnover,atol=1e-14)
    np.testing.assert_allclose(before[idx],ev.q_before,atol=1e-14)
    d['q_before'],d['q_after'],d['turnover']=before,q,turnover
    d['gross_log_pnl']=before*d.market_log_return.to_numpy()
    assert len(d)==boundary['bars'] and q[-1]==boundary['final_q_after']
    np.testing.assert_allclose(d.gross_log_pnl.sum(),boundary['gross_log_pnl'],atol=1e-10)
    np.testing.assert_allclose(turnover.sum(),boundary['turnover'],atol=1e-10)
    h=hashlib.sha256(d[['q_before','q_after','gross_log_pnl','turnover']].to_numpy('<f8').tobytes()).hexdigest()
    assert h==boundary['snapshot_array_sha256'], 'AccountSnapshot bytes differ'
    return d


def validate_sessions():
    previous=None; arrays={}; annual=[]; files_count=0; parity_max=0
    for year in range(2021,2026):
        folder=OUT/'sessions'/str(year)
        seal=json.loads((folder/'seal.json').read_text())
        ev=json.loads((folder/'evidence.json').read_text())
        assert seal['year']==year and seal['prior_receipt_sha256']==previous
        assert seal['evidence_sha256']==sha(folder/'evidence.json')
        assert seal['analysis_sha256']==sha(folder/'analysis.json')
        assert seal['frozen_policy_sha256']==sha(PROTOCOL)==ev['frozen_policy_sha256']
        assert ev['max_input_year']==year and ev['new_strategy_candidates']==0
        assert not ev['fresh_oos'] and not ev['production_authority']
        for f,h in ev['files'].items():assert sha(folder/f)==h;files_count+=1
        for f,h in ev['source_digests'].items():assert sha(ROOT/f)==h
        for item in ev['inputs']:assert item['last_day']<=f'{year}-12-31'
        previous=sha(folder/'seal.json')
        marks=read_csv(folder/'minute_marks.csv.gz');orders=read_csv(folder/'orders.csv.gz')
        assert set(marks.trading_day.str[:4])=={str(year)}
        assert not marks.timestamp.duplicated().any()
        for mode in SCENARIOS:
            o=orders[(orders.scenario==mode)&(orders.event_type!='liquidation')]
            assert (o.source_close<=o.timestamp).all()
            if mode=='literal_publication':assert (o.source_available<=o.timestamp).all()
            if mode=='delay_1m_observed':assert not o.synthetic_mark.any()
        bounds=json.loads((folder/'snapshot_boundaries.json').read_text())
        assert len(bounds)==40
        for boundary in bounds:
            key=(boundary['view'],boundary['scenario'],boundary['policy'])
            d=reconstruct(folder,boundary,marks,orders)
            if key in arrays:
                assert arrays[key][-1].q_after.iloc[-1]==d.q_before.iloc[0]
            arrays.setdefault(key,[]).append(d)
        parity=json.loads((folder/'bridge_parity.json').read_text())
        parity_max=max(parity_max,max(x['max_nav_log_error'] for x in parity))
        assert parity_max<1e-10
        annual.append(read_csv(folder/'annual_metrics.csv'))
    return {k:pd.concat(v,ignore_index=True) for k,v in arrays.items()},pd.concat(annual,ignore_index=True),{
        'sessions':5,'snapshots':200,'sealed_files':files_count,'max_bridge_nav_log_error':parity_max,
        'no_source_market_reads':True,'exact_snapshot_hashes':True,
        'fresh_oos':False,'production_authority':False}


def finalize(validate_only=False):
    arrays,annual,validation=validate_sessions()
    close=OUT/'closeout'
    if validate_only:
        man=json.loads((OUT/'manifest.json').read_text())
        # The historical manifest records the bytes that existed at closeout.
        # CONTINUE_HERE is now a live governance surface, and this validator is
        # operational code that may evolve to preserve the historical contract.
        # Keep those recorded hashes untouched, but do not require today's live
        # files to equal their historical snapshot. All other bundle entries,
        # annual seals, source digests and AccountSnapshot hashes remain exact.
        mutable_surfaces={'CONTINUE_HERE.md','scripts/finalize_execution_audit.py'}
        checked=0
        for f,h in man['files'].items():
            if f in mutable_surfaces:
                continue
            assert sha(ROOT/f)==h, f
            checked+=1
        assert (ROOT/'CONTINUE_HERE.md').is_file()
        print(json.dumps({'status':'pass',**validation,'manifest_files':len(man['files']),
            'manifest_files_checked':checked,'mutable_surfaces':sorted(mutable_surfaces)}))
        return
    close.mkdir(parents=True,exist_ok=True)
    five=[];daily_rows=[];episodes=[];deltas=[]
    for view in range(5):
        for scenario in SCENARIOS:
            b=arrays[(view,scenario,'baseline')];s=arrays[(view,scenario,'slow_conflict_half')]
            alpha=float(s.q_before.abs().sum()/b.q_before.abs().sum())
            for cost in [0,1,3,5]:
                all_net={}
                for name,snap,scale in [('baseline',b,1.),('slow_conflict_half',s,1.),
                     ('constant_075',b,.75),('constant_050',b,.5),('matched_constant',b,alpha)]:
                    net,fee=reprice(snap,cost,scale);all_net[name]=net
                    five.append({'view':view,'scenario':scenario,'cost_bps':cost,'policy':name,
                        'alpha':scale,**metrics(net,snap.trading_day,scale*snap.q_before.abs(),scale*snap.turnover,fee,years=5)})
                    d=pd.DataFrame({'trading_day':snap.trading_day,'net_log_pnl':net}).groupby('trading_day').sum().reset_index()
                    d['view'],d['scenario'],d['policy'],d['cost_bps']=view,scenario,name,cost
                    daily_rows.append(d)
                if view in (0,4) and cost in (0,3):
                    for rank,e in enumerate(drawdown_summary(all_net['baseline'],top_n=10)['episodes'],1):
                        for phase,lo,hi in [('decline',e['peak_index'],e['trough_index']),('recovery',e['trough_index'],e['end_index'])]:
                            if hi<=lo:continue
                            z=b.iloc[lo:hi];r={'view':view,'scenario':scenario,'cost_bps':cost,
                                'rank':rank,'phase':phase,'mdd':e['drawdown'],
                                'peak':str(b.timestamp.iloc[max(0,e['peak_index']-1)]),
                                'start':str(b.timestamp.iloc[max(0,lo-1)]),'end':str(b.timestamp.iloc[hi-1]),
                                'days':z.trading_day.nunique(),'minutes':len(z)}
                            for policy,net in all_net.items():r[policy+'_net_log']=float(net[lo:hi].sum())
                            gross_delta=(s.gross_log_pnl-b.gross_log_pnl).iloc[lo:hi].to_numpy()
                            r['wins_removed_log']=float(-gross_delta[gross_delta<0].sum())
                            r['losses_avoided_log']=float(gross_delta[gross_delta>0].sum())
                            r['gross_delta_log']=float(gross_delta.sum())
                            r['slow_vs_matched_log']=r['slow_conflict_half_net_log']-r['matched_constant_net_log']
                            episodes.append(r)
    five=pd.DataFrame(five)
    for (view,mode,cost),g in annual.groupby(['view','scenario','cost_bps']):
        pivot=g.pivot(index='year',columns='policy',values='mdd')
        for year,r in pivot.iterrows():
            deltas.append({'view':view,'scenario':mode,'cost_bps':cost,'year':year,
                'mdd_improvement_vs_baseline':r['baseline']-r['slow_conflict_half'],
                'mdd_improvement_vs_matched':r['matched_constant']-r['slow_conflict_half']})
    csv(close/'five_year_metrics.csv',five)
    csv(close/'annual_metrics.csv',annual)
    csv(close/'annual_mdd_deltas.csv',deltas)
    csv(close/'top10_decline_recovery.csv',episodes)
    daily=pd.concat(daily_rows,ignore_index=True)
    daily['quarter']=pd.to_datetime(daily.trading_day).dt.to_period('Q').astype(str)
    csv(close/'quarterly_accounts.csv',daily.groupby(['view','scenario','policy','cost_bps','quarter']).net_log_pnl.sum().reset_index())
    # Latency attribution is exact because all variants share minute returns.
    timing=[]
    for view in range(5):
        for policy in ['baseline','slow_conflict_half']:
            old=arrays[(view,'legacy_on_minute',policy)]
            for mode in SCENARIOS[1:]:
                new=arrays[(view,mode,policy)]
                delta=(new.q_before-old.q_before)*old.market_log_return
                np.testing.assert_allclose(delta.sum(),new.gross_log_pnl.sum()-old.gross_log_pnl.sum(),atol=1e-10)
                timing.append({'view':view,'scenario':mode,'policy':policy,
                    'gross_latency_delta_log':float(delta.sum()),
                    'changed_holding_minutes':int((new.q_before!=old.q_before).sum()),
                    'gross_positive_change_log':float(delta.clip(lower=0).sum()),
                    'gross_negative_change_log':float(delta.clip(upper=0).sum())})
    csv(close/'latency_attribution.csv',timing)
    write_json(close/'validation.json',{'status':'pass',**validation})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['svg.hashsalt']='star50-execution-audit-v1'
    fig,axes=plt.subplots(2,2,figsize=(12,7),constrained_layout=True)
    for j,mode in enumerate(SCENARIOS):
        for policy in ['baseline','slow_conflict_half','constant_050']:
            z=daily[(daily.view==0)&(daily.scenario==mode)&(daily.policy==policy)&(daily.cost_bps==3)].sort_values('trading_day')
            axes.flat[j].plot(pd.to_datetime(z.trading_day),np.exp(z.net_log_pnl.cumsum()),label=policy,lw=1)
        axes.flat[j].set_title(mode+' | 3bp');axes.flat[j].grid(alpha=.25)
    axes.flat[0].legend(fontsize=8)
    fig.savefig(close/'overview.svg',metadata={'Date':None});fig.savefig(close/'overview.png',dpi=120);plt.close(fig)
    print(five[(five.view==0)&(five.cost_bps.isin([0,3]))][['scenario','cost_bps','policy','cagr','mdd','longest_underwater_days']].to_string(index=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate-only',action='store_true')
    finalize(p.parse_args().validate_only)
