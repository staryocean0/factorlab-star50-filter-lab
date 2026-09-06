"""Execute one frozen retrospective attribution round; never change positions.

prepare builds fixed evidence; year opens one annual pack; seal requires a human
review JSON; analyze runs the registered global references after all five seals.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from reproduce_historical_baseline import load_bars,baseline_frame,fingerprint,HISTORICAL
from star50_filter.cross_scale_root_cause import (FEATURES,components,properties,native_properties,
    association,simple_associations,cell_labels,cell_table,trade_fragments)
from star50_filter.drawdown_diagnostics import drawdown_summary
from star50_filter.filters import butter_lowpass,hysteresis_positions
from star50_filter.backtest import execute_next_open

OUT=ROOT/'artifacts/cross_scale_root_cause'
PROTOCOL=ROOT/'docs/research/cross_scale_root_cause/preregistration.json'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n')
def csv(p,f):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    f.to_csv(p,index=False,compression={'method':'gzip','mtime':0} if str(p).endswith('.gz') else None)
def read_daily(): return pd.read_csv(OUT/'daily_panel.csv.gz',dtype={'trading_day':str})
def read_bar(): return pd.read_parquet(OUT/'primary_bars.parquet')

def episode_table(f,daily):
    summary=drawdown_summary(f.pnl_log,top_n=10000)
    rows=[]
    for rank,e in enumerate(summary['episodes'][:10],1):
        for leg,a,b in [('decline',e['peak_index'],e['trough_index']),('recovery',e['trough_index'],e['end_index'])]:
            g=f.iloc[a:b]
            if g.empty: continue
            days=g.trading_day.unique()
            q=daily.set_index('trading_day').reindex(days)
            trades=trade_fragments(g.reset_index(drop=True))
            negative=g.pnl_log.clip(upper=0).sum();positive=g.pnl_log.clip(lower=0).sum()
            rows.append({'rank':rank,'leg':leg,'start_return_index':a,'end_return_index_exclusive':b,
                'peak':str(f.timestamp.iloc[max(e['peak_index']-1,0)]),'trough':str(f.timestamp.iloc[e['trough_index']-1]),
                'recovery':str(f.timestamp.iloc[e['end_index']-1]),'mdd_pct':100*e['drawdown'],
                'first_booking':str(g.timestamp.iloc[0]),'last_booking':str(g.timestamp.iloc[-1]),
                'trading_days':len(days),'bars':len(g),'pnl_log':g.pnl_log.sum(),'mean_daily_pnl_bp':g.pnl_log.sum()/len(days)*1e4,
                'long_log':g.loc[g.exec_pos>0,'pnl_log'].sum(),'short_log':g.loc[g.exec_pos<0,'pnl_log'].sum(),
                'positive_bar_log':positive,'negative_bar_log':negative,'cancellation':-negative/positive if positive>0 else np.nan,
                'fragment_count':len(trades),'fragment_win_rate':(trades.pnl_log>0).mean(),
                'mfe_sum':trades.mfe_log.sum(),'giveback_sum':trades.giveback_log.sum(),
                'loss_never_favorable_log':trades.loc[trades.losing_never_favorable,'pnl_log'].sum(),
                'loss_after_favorable_log':trades.loc[trades.losing_after_favorable,'pnl_log'].sum(),
                'price_path_abs':g.open_log_return.abs().sum(),'capture':g.pnl_log.sum()/g.open_log_return.abs().sum(),
                'attribute_edge_days':int((~q.inference_ok.fillna(False)).sum()),
                **{f: q[f].mean() for f in FEATURES}})
    return pd.DataFrame(rows),summary

def prepare(data_dir):
    OUT.mkdir(parents=True,exist_ok=True)
    protocol=json.loads(PROTOCOL.read_text())
    for p,h in protocol['source_hashes'].items():
        assert sha(ROOT/p)==h,('sealed baseline source changed',p)
    views=[];panels=[];causal=[];inputs=[];native=[]
    all_days=None
    for source in sorted(data_dir.glob('*.parquet')):
        view=source.stem
        raw=load_bars(data_dir,view)
        assert raw.trading_day.max()<='2025-12-31'
        inputs.append({'view':view,'sha256':sha(source),'rows':len(raw),'first':raw.trading_day.min(),'last':raw.trading_day.max()})
        npanel,nbar=native_properties(raw)
        npanel=npanel.reset_index();npanel['view']=view;npanel['bars_per_day']=nbar
        native.append(npanel.loc[npanel.trading_day>='2021-01-01'])
        if not view.startswith('5m_offset_'): continue
        f=baseline_frame(raw)
        dp,lps,bands,a=properties(f)
        cp,_,_,_=properties(f,causal=True)
        # Shift attributes calculated only from history by one full day. This
        # does not assert an intraday executable proxy; no policy is evaluated.
        cp=cp.shift(1)
        day=f.groupby('trading_day').agg(pnl_log=('pnl_log','sum'),abs_path=('open_log_return',lambda z:z.abs().sum()),
            negative_log=('pnl_log',lambda z:z.clip(upper=0).sum()),positive_log=('pnl_log',lambda z:z.clip(lower=0).sum()),
            flips=('exec_pos',lambda z:int((z.diff().fillna(0)!=0).sum())),nav=('nav','last'),drawdown=('drawdown','last'),year=('year','last'))
        day['capture']=day.pnl_log/np.maximum(day.abs_path,1e-15)
        days=list(day.index);allowed=set(days[20:-20]);day['inference_ok']=day.index.isin(allowed)
        d=dp.join(day).reset_index();d['view']=view
        c=cp.join(day).reset_index();c['view']=view
        panels.append(d.loc[d.year>=2021]);causal.append(c.loc[c.year>=2021])
        fp=fingerprint(f);views.append({'view':view,**fp})
        if view=='5m_offset_0':
            for key,value in HISTORICAL.items(): assert np.isclose(fp[key],value,atol=1e-8),key
            primary=f.loc[f.is_development].copy().reset_index(drop=True)
            dev=f.is_development.to_numpy()
            for p in (12,48,240,960): primary[f'lp{p}']=lps[p][dev]
            for k,name in enumerate(('fast','work','swing','macro','trend')): primary[name]=bands[dev,k]
            for name in ('fast_share_5d','slow_work_velocity_5d','eff_1d','eff_20d'): primary[name]=a.loc[dev,name].to_numpy()
            keep=['timestamp','trading_day','year','open','close','high','low','log_close','lowpass','sigma','signal_pos','exec_pos','pnl_log','open_log_return','nav','drawdown','lp12','lp48','lp240','lp960','fast','work','swing','macro','trend','fast_share_5d','slow_work_velocity_5d','eff_1d','eff_20d']
            primary[keep].to_parquet(OUT/'primary_bars.parquet',index=False,compression='zstd')
            csv(OUT/'trades.csv.gz',trade_fragments(primary))
    csv(OUT/'daily_panel.csv.gz',pd.concat(panels,ignore_index=True))
    csv(OUT/'causal_previous_day_panel.csv.gz',pd.concat(causal,ignore_index=True))
    csv(OUT/'native_view_properties.csv.gz',pd.concat(native,ignore_index=True))
    csv(OUT/'baseline_fingerprints.csv',pd.DataFrame(views))
    dp=read_daily();d=dp.loc[dp.view=='5m_offset_0']
    episodes,summary=episode_table(read_bar(),d)
    csv(OUT/'top10_legs.csv',episodes)
    write_json(OUT/'account_summary.json',summary)
    write_json(OUT/'input_receipt.json',{'protocol_sha256':sha(PROTOCOL),'inputs':inputs,'excluded_2026':True,'available_at':'historical retrieval only; realtime realtime','policy_candidates':0,'production_authority':False})
    print(json.dumps({'prepared_views':len(inputs),'original_baseline':views[0],'primary_days':len(d),'inferential_days':int(d.inference_ok.sum())}))

def event_plot(rank,path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    f=read_bar();legs=pd.read_csv(OUT/'top10_legs.csv');e=legs.loc[legs['rank']==rank]
    a=int(e.start_return_index.min());b=int(e.end_return_index_exclusive.max())
    q=f.iloc[max(0,a-48):min(len(f),b+48)].copy();xx=np.arange(len(q));split=int(e.loc[e.leg=='decline','end_return_index_exclusive'].iloc[0])-max(0,a-48)
    fig,axs=plt.subplots(5,1,figsize=(13,12),sharex=True,gridspec_kw={'height_ratios':[2,1.3,1.2,1,1.5]},layout='constrained')
    axs[0].plot(xx,np.log(q.close),lw=.65,color='#34495e',label='Log close')
    axs[0].plot(xx,q.lp12,lw=.8,label='Two-sided LP 1h')
    axs[0].plot(xx,q.lp240,lw=1.5,label='Two-sided LP 5d')
    axs[0].legend(ncol=3,fontsize=8);axs[0].set_ylabel('Price / slow drift')
    axs[1].plot(xx,q.work*1e4,lw=.8,label='1h-1d work band')
    axs[1].plot(xx,q.fast*1e4,lw=.5,alpha=.7,label='<1h fast component');axs[1].set_ylabel('Component (bp)');axs[1].legend(fontsize=8,ncol=2)
    axs[2].plot(xx,q.fast_share_5d,label='Fast variation share, 5d')
    axs[2].plot(xx,q.slow_work_velocity_5d,label='Slow/work velocity, 5d');axs[2].set_ylabel('Attributes');axs[2].legend(fontsize=8,ncol=2)
    axs[3].step(xx,q.exec_pos,where='post',lw=.65,label='Original booked position')
    axs[3].step(xx,q.signal_pos,where='post',lw=.5,alpha=.45,label='Close signal');axs[3].set_ylabel('Fixed position');axs[3].legend(fontsize=8,ncol=2)
    axs[4].plot(xx,np.cumsum(q.pnl_log)*100,color='#b34450',label='Cumulative log PnL')
    gross_ax=axs[4].twinx()
    gross_ax.plot(xx,np.cumsum(q.pnl_log.clip(lower=0))*100,color='#36886e',ls='--',alpha=.6,label='Positive booked returns')
    gross_ax.plot(xx,np.cumsum(q.pnl_log.clip(upper=0))*100,color='#636e72',ls='--',alpha=.6,label='Negative booked returns');axs[4].set_ylabel('Net log PnL (%)');gross_ax.set_ylabel('Gross +/- log PnL (%)');axs[4].legend(fontsize=8,loc='upper left');gross_ax.legend(fontsize=8,loc='lower left')
    for ax in axs:
        ax.axvline(split,color='#b34450',ls=':',lw=1);ax.grid(alpha=.16)
    ticks=np.unique(np.linspace(0,len(q)-1,8).astype(int));axs[-1].set_xticks(ticks,[str(q.timestamp.iloc[i])[:16] for i in ticks],rotation=20,ha='right')
    fig.suptitle(f'Original drawdown #{rank}: {e.mdd_pct.iloc[0]:.2f}% | dotted line = trough\nHindsight components use future; original signals and positions remain unchanged',fontsize=13)
    path.parent.mkdir(parents=True,exist_ok=True)
    import io
    buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=135);plt.close(fig)
    path.write_bytes(buffer.getvalue())

def year_pack(year):
    session=OUT/'sessions'/str(year)
    if year>2021 and not (OUT/'sessions'/str(year-1)/'receipt.json').exists(): raise ValueError('Prior annual review is not sealed')
    if (session/'receipt.json').exists(): raise ValueError('Sealed session cannot be overwritten')
    p=read_daily();p=p.loc[p.view=='5m_offset_0'];valid=p.loc[p.inference_ok].copy();valid,medians=cell_labels(valid)
    q=valid.loc[valid.year==year]
    f=read_bar();fy=f.loc[f.year==year];ep=pd.read_csv(OUT/'top10_legs.csv')
    selected=ep.loc[(ep.leg=='decline') & ep.peak.str.startswith(str(year))].sort_values('mdd_pct',ascending=False)
    rank=int(selected['rank'].iloc[0]) if len(selected) else 1
    csv(session/'cells.csv',cell_table(q));csv(session/'associations.csv',simple_associations(q,['year']))
    csv(session/'event_legs.csv',ep.loc[ep['rank'].isin(selected['rank'])])
    csv(session/'trades.csv',trade_fragments(fy.reset_index(drop=True)))
    event_plot(rank,session/'event.png')
    receipt={'year':year,'baseline_annual_pct':100*np.expm1(fy.pnl_log.sum()),'inference_days':len(q),'figure_event_rank':rank,
        'attribute_means':{z:float(q[z].mean()) for z in FEATURES},'daily_losing_share':float((q.pnl_log<0).mean()),
        'consumed_material':True,'blind':False,'policy_change':False,'protocol_sha256':sha(PROTOCOL),'thresholds':medians}
    write_json(session/'evidence.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False))

def seal(year,review):
    p=OUT/'sessions'/str(year);target=p/'receipt.json'
    if target.exists(): raise ValueError('Immutable annual receipt already exists')
    text=json.loads(review.read_text());assert text['year']==year
    for key in ('observations','counterexamples','mechanism_status','next_year_fixed_protocol'): assert text.get(key),key
    write_json(p/'review.json',text)
    previous=sha(PROTOCOL) if year==2021 else sha(OUT/'sessions'/str(year-1)/'receipt.json')
    write_json(target,{'year':year,'prior_receipt_sha256':previous,'baseline_formula_hashes':json.loads(PROTOCOL.read_text())['source_hashes'],
        'files':{str(x.relative_to(ROOT)):sha(x) for x in sorted(p.iterdir()) if x.is_file()},'policy_change':False,'production_authority':False})
    print(json.dumps({'sealed':year,'receipt_sha256':sha(target)}))

def synthetic():
    rows=[];A=.002;T=9600;warm=1920;t=np.arange(T)
    for period in (6,8,12,24,48,96,240):
        cases=[('wave',ratio,phase,0) for ratio in (0,.5,2) for phase in (0,np.pi/2,np.pi)]
        cases += [('drift',0,0,drift) for drift in (-.5,0,.5)]
        for kind,ratio,phase,drift in cases:
            x=A*np.sin(2*np.pi*t/period)+ratio*A*960/period*np.sin(2*np.pi*t/960+phase)+drift*A*2*np.pi/period*t
            op=np.exp(np.r_[x[0],x[:-1]])
            low=butter_lowpass(x,12,1);sig=pd.Series(x).diff().rolling(48).std(ddof=0).to_numpy()
            s=hysteresis_positions(low,sig);p,pnl=execute_next_open(s,op)
            ret=np.r_[0,np.diff(np.log(op))]
            rows.append({'kind':kind,'period_bars':period,'slow_velocity_ratio':ratio,'slow_phase':phase,'drift_velocity_ratio':drift,
                'capture':pnl[warm:].sum()/np.abs(ret[warm:]).sum(),'pnl_log_per_1000bars':pnl[warm:].mean()*1000,
                'flips_per_1000bars':(np.diff(p[warm:])!=0).mean()*1000,'long_share':(p[warm:]>0).mean()})
    csv(OUT/'synthetic_wave_grid.csv',pd.DataFrame(rows))

def ablations(data_dir):
    raw=load_bars(data_dir);x=np.log(raw.close.to_numpy());o=np.log(raw.open.to_numpy())
    lpc,_=components(x);lpo,_=components(o)
    cb=[x-lpc[12],lpc[12]-lpc[240],lpc[240]];ob=[o-lpo[12],lpo[12]-lpo[240],lpo[240]]
    original=baseline_frame(raw);dev=raw.year>=2021;ep=pd.read_csv(OUT/'top10_legs.csv')
    rows=[];events=[];paths=[];decomp=[]
    originalp=original.exec_pos.to_numpy()
    for j,name in enumerate(('fast','medium','slow')):
        pnl=originalp*np.r_[0,np.diff(ob[j])]
        gd=pnl[dev]
        for _,e in ep.iterrows():
            a,b=int(e.start_return_index),int(e.end_return_index_exclusive)
            decomp.append({'rank':e['rank'],'leg':e.leg,'component':name,'fixed_position_log_pnl':float(gd[a:b].sum())})
    for mask in itertools.product((0,1),repeat=3):
        if not any(mask):continue
        close=sum(b*k for b,k in zip(cb,mask));op=sum(b*k for b,k in zip(ob,mask))
        # Common recentering does not alter close/open returns or the filter.
        anchor=x[0]-close[0]
        q=raw.copy();q['close']=np.exp(close+anchor);q['open']=np.exp(op+anchor)
        g=baseline_frame(q);gdev=g.loc[dev].reset_index(drop=True)
        name='+'.join(n for n,k in zip(('fast','medium','slow'),mask) if k)
        if all(mask):
            assert np.allclose(g.pnl_log,original.pnl_log,rtol=0,atol=2e-14)
            assert np.array_equal(g.exec_pos,original.exec_pos)
        valid=gdev.iloc[:-20*48];ds=drawdown_summary(valid.pnl_log)
        rows.append({'components':name,'full_cagr_pct':100*np.expm1(gdev.pnl_log.sum()/5),'full_mdd_pct':100*drawdown_summary(gdev.pnl_log)['mdd'],
            'edge_trimmed_pnl_log':valid.pnl_log.sum(),'edge_trimmed_mdd_pct':100*ds['mdd'],
            'position_disagreement_original':(gdev.exec_pos.to_numpy()!=original.loc[dev,'exec_pos'].to_numpy()).mean()})
        daily=gdev.groupby('trading_day').pnl_log.sum().reset_index();daily['components']=name;paths.append(daily)
        for _,e in ep.iterrows():
            a,b=int(e.start_return_index),int(e.end_return_index_exclusive)
            events.append({'components':name,'rank':e['rank'],'leg':e.leg,'pnl_log':float(gdev.pnl_log.iloc[a:b].sum())})
    csv(OUT/'ablation_paths.csv',pd.DataFrame(rows));csv(OUT/'ablation_event_legs.csv',pd.DataFrame(events))
    csv(OUT/'ablation_daily.csv.gz',pd.concat(paths));csv(OUT/'fixed_position_component_legs.csv',pd.DataFrame(decomp))

def matched(panel):
    p=panel.copy();p['vol_tercile']=p.groupby('year').rv_1d.transform(lambda z:pd.qcut(z,3,labels=False,duplicates='drop'))
    rows=[]
    for name in ('fast_slow','short_long_eff'):
        for cell in ('00','01','10','11'):
            for (year,vol),q in p.groupby(['year','vol_tercile']):
                a=q.loc[q[name]==cell];b=q.loc[q[name]!=cell]
                if len(a) and len(b): rows.append({'table':name,'cell':cell,'year':year,'vol_tercile':vol,'target_days':len(a),'control_days':len(b),'pnl_bp_difference':1e4*(a.pnl_log.mean()-b.pnl_log.mean()),'capture_difference':a.capture.mean()-b.capture.mean()})
    return pd.DataFrame(rows)

def analyze(data_dir):
    for y in range(2021,2026): assert (OUT/'sessions'/str(y)/'receipt.json').exists(),y
    p=read_daily();valid=p.loc[p.inference_ok].copy();primary=valid.loc[valid.view=='5m_offset_0'].copy()
    primary,medians=cell_labels(primary);valid,_=cell_labels(valid,medians)
    csv(OUT/'associations.csv',association(primary))
    cp=pd.read_csv(OUT/'causal_previous_day_panel.csv.gz');cp=cp.loc[(cp.view=='5m_offset_0') & cp.inference_ok]
    csv(OUT/'causal_proxy_associations.csv',association(cp,seed=20260907))
    csv(OUT/'annual_offset_associations.csv',simple_associations(valid,['view','year']))
    csv(OUT/'offset_associations.csv',simple_associations(valid,['view']))
    csv(OUT/'cells.csv',cell_table(primary));csv(OUT/'cells_by_year.csv',cell_table(primary,['year']));csv(OUT/'cells_by_offset.csv',cell_table(valid,['view']))
    csv(OUT/'matched_controls.csv',matched(primary))
    write_json(OUT/'cell_thresholds.json',medians)
    primary=primary.sort_values('trading_day');primary['block']=primary.groupby('year').cumcount()//5
    blocks=primary.groupby(['year','block']).agg({**{f:'mean' for f in FEATURES},'pnl_log':'sum','abs_path':'sum','trading_day':'size'}).reset_index()
    blocks=blocks.loc[blocks.trading_day==5];blocks['capture']=blocks.pnl_log/blocks.abs_path
    csv(OUT/'nonoverlap5day_blocks.csv',blocks)
    csv(OUT/'nonoverlap5day_associations.csv',simple_associations(blocks,['year']))
    # All other periods provide winning and ordinary-underwater controls.
    f=read_bar();f['slice']='other_underwater';f.loc[f.drawdown>=-1e-12,'slice']='at_highwater'
    ep=pd.read_csv(OUT/'top10_legs.csv')
    for _,e in ep.iterrows():f.loc[int(e.start_return_index):int(e.end_return_index_exclusive)-1,'slice']='top10_'+e.leg
    rows=[]
    for name,g in f.groupby('slice'):
        t=trade_fragments(g.reset_index(drop=True)) if name in () else None
        rows.append({'slice':name,'bars':len(g),'pnl_log':g.pnl_log.sum(),'positive_log':g.pnl_log.clip(lower=0).sum(),'negative_log':g.pnl_log.clip(upper=0).sum(),'mean_bp':g.pnl_log.mean()*1e4,'long_log':g.loc[g.exec_pos>0,'pnl_log'].sum(),'short_log':g.loc[g.exec_pos<0,'pnl_log'].sum()})
    csv(OUT/'all_period_controls.csv',pd.DataFrame(rows))
    synthetic();ablations(data_dir)
    for rank in (1,2,3,4,5,6,7,8,9,10):event_plot(rank,OUT/'figures'/f'event_{rank:02d}.png')
    print(json.dumps({'analysis_complete':True,'primary_tests':40,'causal_companion_tests':40,'policy_candidates':0}))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['prepare','year','seal','analyze']);ap.add_argument('--data-dir',type=Path);ap.add_argument('--year',type=int);ap.add_argument('--review',type=Path)
    a=ap.parse_args()
    if a.command=='prepare':prepare(a.data_dir)
    elif a.command=='year':year_pack(a.year)
    elif a.command=='seal':seal(a.year,a.review)
    else:analyze(a.data_dir)
if __name__=='__main__':main()
