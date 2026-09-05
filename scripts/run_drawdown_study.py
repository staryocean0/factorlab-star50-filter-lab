"""Reproducible descriptive study and separately reviewed fixed yearly experiments."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from reproduce_historical_baseline import load_bars, baseline_frame
from star50_filter.drawdown_research import causal_states, targets, account, lag, open_component_attribution, exact_gap_attribution
from star50_filter.drawdown_diagnostics import drawdown_summary, permutation_drawdown_reference

OUT=ROOT/'artifacts/drawdown_conditions'

def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def metrics(a, years):
    r=a.net_log_pnl.to_numpy(); d=drawdown_summary(r,top_n=0)
    daily=a.groupby('trading_day',sort=True).net_log_pnl.sum()
    dd=drawdown_summary(daily.to_numpy(),top_n=0)
    return {'cagr':float(np.expm1(r.sum()/years)), 'total_log_return':float(r.sum()),
        'mdd':d['mdd'],'daily_mdd':dd['mdd'],
        'longest_underwater_days':dd['longest_underwater_observations'],
        'mean_exposure':float(a.position.abs().mean()),'turnover':float(a.turnover.sum()),
        'cost_log':float(a.cost_log.sum()),'daily_sharpe':float(daily.mean()/daily.std(ddof=1)*np.sqrt(252))}

def describe(data_dir):
    out=OUT/'descriptive';out.mkdir(parents=True,exist_ok=True)
    df=load_bars(data_dir); f=baseline_frame(df);st=causal_states(df)
    np.testing.assert_array_equal(st.signal,f.signal_pos)
    atr=open_component_attribution(df,f.exec_pos)
    gaps=exact_gap_attribution(df,f.exec_pos)
    v=pd.concat([df[['timestamp','trading_day','open','close','year']],
        f[['signal_pos','exec_pos','pnl_log','nav','drawdown','open_log_return']],atr,gaps],axis=1)
    for c in ['slow_conflict','chop','slow_displacement','slow_stability','work_amplitude','work_efficiency','reversals']:
        v[c]=lag(st[c].to_numpy(),2)
    v=v.loc[f.is_development].reset_index(drop=True)
    summary=drawdown_summary(v.pnl_log.to_numpy())
    events=[]
    for rank,e in enumerate(summary['episodes'],1):
        p,t=e['peak_index'],e['trough_index']; z=v.iloc[p:t]
        rec=e['recovery_index']
        def stamp(n):
            return str(v.timestamp.iloc[n-1]) if n else 'initial_2021_open'
        ev={'rank':rank,'peak':stamp(p),'trough':stamp(t),
            'recovery':stamp(rec) if rec else None,'drawdown':e['drawdown'],
            'decline_trading_days':z.trading_day.nunique(),
            'underwater_trading_days':v.iloc[p:e['end_index']].trading_day.nunique(),
            'index_log_change':float(z.open_log_return.sum()),
            'long_log_pnl':float(z.loc[z.exec_pos>0,'pnl_log'].sum()),
            'short_log_pnl':float(z.loc[z.exec_pos<0,'pnl_log'].sum()),
            'slow_conflict_share':float(z.slow_conflict.mean()),'chop_share':float(z.chop.mean()),
            'slow_conflict_log_pnl':float(z.loc[z.slow_conflict==1,'pnl_log'].sum()),
            'chop_log_pnl':float(z.loc[z.chop==1,'pnl_log'].sum()),
            'flips_per_day':float((z.exec_pos.diff().abs()/2).sum()/z.trading_day.nunique())}
        for c in list(atr)+list(gaps):ev[c]=float(z[c].sum())
        assert abs(sum(ev[c] for c in atr)-z.pnl_log.sum())<1e-10
        assert abs(sum(ev[c] for c in gaps)-z.pnl_log.sum())<1e-10
        events.append(ev)
    pd.DataFrame(events).to_csv(out/'top10_drawdowns.csv',index=False)
    cond=[]
    v['slow_conflict']=v.slow_conflict.astype(bool);v['chop']=v.chop.astype(bool)
    for year,z in [('all',v),*[(str(y),v.loc[v.year==y]) for y in range(2021,2026)]]:
        for (s,c),g in z.groupby(['slow_conflict','chop']):
            cond.append({'year':year,'slow_conflict':bool(s),'chop':bool(c),
                'bars':len(g),'share':len(g)/len(z),'days_present':g.trading_day.nunique(),
                'pnl_log':g.pnl_log.sum(),'mean_pnl_bps':g.pnl_log.mean()*1e4,
                'negative_log_sum':g.pnl_log.clip(upper=0).sum(),
                'slow_log_pnl':g.slow_log_pnl.sum(),'work_log_pnl':g.work_log_pnl.sum(),
                'residual_log_pnl':g.residual_log_pnl.sum(),'overnight_gap_log_pnl':g.overnight_gap_log_pnl.sum()})
    pd.DataFrame(cond).to_csv(out/'joint_condition_cells.csv',index=False)
    daily=v.groupby('trading_day').agg(pnl_log=('pnl_log','sum'),open=('open','last'),
        slow_conflict=('slow_conflict','mean'),chop=('chop','mean'),
        slow_log_pnl=('slow_log_pnl','sum'),work_log_pnl=('work_log_pnl','sum'),
        residual_log_pnl=('residual_log_pnl','sum'),overnight_gap_log_pnl=('overnight_gap_log_pnl','sum'))
    daily.to_csv(out/'daily_baseline.csv')
    perm=permutation_drawdown_reference(daily.pnl_log.to_numpy())
    write_json(out/'permutation_reference.json',perm)
    summary['events']=events;summary['interval']='2021-2025';summary['new_account_start']='descriptive uses exact historical carried position, unlike flat-start candidate accounting'
    write_json(out/'summary.json',summary)
    v.to_csv(out/'bar_attribution.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    print(json.dumps({'mdd':summary['mdd'],'top3':events[:3],
        'permutation_tail':{k:{m:v2['upper_tail_plus_one'] for m,v2 in val.items() if isinstance(v2,dict) and 'upper_tail_plus_one' in v2} for k,val in perm['references'].items()}},indent=2))

def year_experiment(data_dir,year):
    if year not in range(2021,2026):raise ValueError('Only 2021-2025 allowed')
    out=OUT/'sessions'/str(year)
    if (out/'sealed_receipt.json').exists():raise ValueError('Year sealed; do not overwrite')
    if year>2021 and not (OUT/'sessions'/str(year-1)/'sealed_receipt.json').exists():
        raise ValueError('Previous year must be manually reviewed and sealed')
    out.mkdir(parents=True,exist_ok=True); rows=[]; daily_keep=[]; quarter=[]
    for offset in range(5):
        df=load_bars(data_dir,f'5m_offset_{offset}')
        df=df.loc[df.year<=year].reset_index(drop=True)
        st=causal_states(df,48 if offset==0 else 46);ts=targets(st)
        for scope in ['annual','cumulative']:
            mask=(df.year==year).to_numpy() if scope=='annual' else (df.year>=2021).to_numpy()
            n_years=1 if scope=='annual' else year-2020
            active=ts.copy()
            qbase=account(df,ts['baseline']).position.to_numpy()
            for cid in ['slow_conflict_half','chop_half']:
                qc=account(df,ts[cid]).position.to_numpy()
                alpha=float(np.abs(qc[mask]).sum()/np.abs(qbase[mask]).sum())
                active[cid+'_matched_constant']=alpha*ts['baseline']
            for cost in [0,1,3,5]:
                for cid,target in active.items():
                    a=account(df,target,cost,terminal_liquidation=(year==2025))
                    selected=a.loc[mask]
                    rows.append({'year':year,'view':offset,'scope':scope,'cost_bps':cost,
                        'policy':cid,**metrics(selected,n_years)})
                    if offset==0 and scope=='annual':
                        daily=selected.groupby('trading_day').agg(net_log_pnl=('net_log_pnl','sum'),
                            position_abs=('position',lambda x: x.abs().mean()),turnover=('turnover','sum'))
                        daily=daily.reset_index();daily['policy']=cid;daily['cost_bps']=cost
                        daily_keep.append(daily)
                        selected=selected.copy();selected['quarter']=pd.to_datetime(selected.trading_day).dt.to_period('Q').astype(str)
                        for q,g in selected.groupby('quarter'):
                            quarter.append({'quarter':q,'policy':cid,'cost_bps':cost,
                                'total_log_return':float(g.net_log_pnl.sum()),'mdd':drawdown_summary(g.net_log_pnl.to_numpy(),0)['mdd']})
        # One actual-equity sensitivity per original/full-scale and mechanism rule.
        for cid in ['baseline','slow_conflict_half','chop_half']:
            a=account(df,ts[cid],0,mode='simple_equity',terminal_liquidation=(year==2025))
            sel=a.loc[(df.year>=2021).to_numpy()]
            rows.append({'year':year,'view':offset,'scope':'cumulative_simple_equity','cost_bps':0,'policy':cid,**metrics(sel,year-2020)})
    table=pd.DataFrame(rows);table.to_csv(out/'policy_metrics.csv',index=False)
    pd.concat(daily_keep).to_csv(out/'daily_accounts.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame(quarter).to_csv(out/'quarterly_accounts.csv',index=False)
    write_json(out/'evidence_receipt.json',{'year':year,'stage':'fixed complete policy diagnostic counterfactual',
        'risk_protocol_sha256':digest(ROOT/'docs/research/drawdown_conditions/risk_preregistration.json'),
        'prior_receipt_sha256':digest(OUT/'sessions'/str(year-1)/'sealed_receipt.json') if year>2021 else None,
        'source_digests':{str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'src/star50_filter/drawdown_research.py',ROOT/'src/star50_filter/drawdown_diagnostics.py',ROOT/'scripts/reproduce_historical_baseline.py']},
        'evidence_files':{p.name:digest(p) for p in out.iterdir() if p.suffix in ['.csv','.gz']},
        'max_input_year':year,'parameter_updates':0,'fresh_oos':False,'production_authority':False})
    print(table.loc[(table.view==0)&(table.scope=='annual')&(table.cost_bps==0),['policy','cagr','mdd','mean_exposure']].to_string(index=False))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,default=ROOT/'data/development')
    sub=ap.add_subparsers(dest='command',required=True);sub.add_parser('describe');yp=sub.add_parser('year');yp.add_argument('--year',type=int,required=True)
    args=ap.parse_args();describe(args.data_dir) if args.command=='describe' else year_experiment(args.data_dir,args.year)

if __name__=='__main__':main()
