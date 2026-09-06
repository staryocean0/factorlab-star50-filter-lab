"""Complete registered descriptive controls and figures; no new hypotheses."""
from pathlib import Path
import sys,json,io
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from run_cross_scale_root_cause import OUT,read_daily,read_bar,csv,write_json
from star50_filter.cross_scale_root_cause import cell_labels,FEATURES,trade_fragments
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def savefig(fig,path):
    b=io.BytesIO();fig.savefig(b,format='png',dpi=145);plt.close(fig);Path(path).write_bytes(b.getvalue())


def candlestick_day(f,day,path,title):
    g=f.loc[f.trading_day==day].copy();prev=f.loc[f.index<g.index.min()].tail(1)
    x=np.arange(len(g));o=np.log(g.open)*1e4;c=np.log(g.close)*1e4
    origin=float(o.iloc[0]);o-=origin;c-=origin;hi=np.log(pd.to_numeric(g.high))*1e4-origin;lo=np.log(pd.to_numeric(g.low))*1e4-origin
    # The original filter subtracts the first 2020 log close. Recover exactly
    # that additive origin from the immutable common-root replay artifact.
    source=ROOT/'artifacts/drawdown_conditions/baseline_reproduction/reproduced_baseline_frame.csv.gz'
    initial=float(pd.read_csv(source,nrows=1,usecols=['log_close']).log_close.iloc[0])
    y=(g.lowpass+initial)*1e4-origin
    fig,axs=plt.subplots(3,1,figsize=(12,8),sharex=True,layout='constrained',gridspec_kw={'height_ratios':[2.5,1,1.4]})
    for i in x:
        color='#23856c' if c.iloc[i]>=o.iloc[i] else '#bd4554'
        axs[0].vlines(i,lo.iloc[i],hi.iloc[i],color=color,lw=.9)
        axs[0].add_patch(Rectangle((i-.3,min(o.iloc[i],c.iloc[i])),.6,max(abs(c.iloc[i]-o.iloc[i]),.08),color=color,alpha=.8))
    axs[0].plot(x,y,color='#3158a5',lw=1.4,label='Original causal LP12 (absolute price scale)')
    axs[0].legend(fontsize=8);axs[0].set_ylabel('Log price (bp from day open)')
    axs[1].step(x,g.exec_pos,where='post',label='Booked position',color='#3158a5')
    axs[1].step(x,g.signal_pos,where='post',label='Close signal',color='#dc963e',alpha=.6)
    axs[1].set_ylim(-1.3,1.3);axs[1].legend(ncol=2,fontsize=8);axs[1].set_ylabel('Fixed position')
    axs[2].bar(x,g.pnl_log*1e4,color=np.where(g.pnl_log>=0,'#23856c','#bd4554'),alpha=.5,label='Booked return (bp)')
    cum=axs[2].twinx();cum.plot(x,np.cumsum(g.pnl_log)*100,color='#3158a5',label='Cumulative log PnL (%)');cum.set_ylabel('Cumulative log PnL (%)');axs[2].set_ylabel('Interval PnL (bp)')
    ticks=x[::6];axs[-1].set_xticks(ticks,[str(g.timestamp.iloc[i])[11:16] for i in ticks])
    for ax in axs:ax.grid(alpha=.15)
    fig.suptitle(f'{title} | {day}\nK-line labels are bar ends; PnL at row i ends at open[i], not close[i]',fontsize=12)
    savefig(fig,path)
    csv(Path(path).with_suffix('.csv'),g)


def complete():
    p=read_daily();p=p.loc[p.view=='5m_offset_0'].sort_values('trading_day');valid=p.loc[p.inference_ok].copy()
    valid,med=cell_labels(valid);full,_=cell_labels(p,med)
    f=read_bar();ep=pd.read_csv(OUT/'top10_legs.csv')
    rows=[];native=pd.read_csv(OUT/'native_view_properties.csv.gz');nv=[]
    for _,e in ep.iterrows():
        g=f.iloc[int(e.start_return_index):int(e.end_return_index_exclusive)]
        d=full.set_index('trading_day').reindex(g.trading_day).reset_index(drop=True)
        for table in ('fast_slow','short_long_eff'):
            for cell in ('00','01','10','11'):
                q=g.iloc[np.flatnonzero(d[table].to_numpy()==cell)]
                rows.append({'rank':e['rank'],'leg':e.leg,'table':table,'cell':cell,'bars':len(q),'pnl_log':q.pnl_log.sum(),
                    'positive_log':q.pnl_log.clip(lower=0).sum(),'negative_log':q.pnl_log.clip(upper=0).sum(),
                    'sample_note':'EOD full-day retrospective label applied to each marked interval, including partial event endpoint days'})
        for view,q in native.loc[native.trading_day.isin(g.trading_day)].groupby('view'):
            nv.append({'rank':e['rank'],'leg':e.leg,'view':view,'days':len(q),**{k:q[k].mean() for k in ('eff_1d','eff_5d','eff_20d','wick_1d')}})
    csv(OUT/'event_condition_cells.csv',pd.DataFrame(rows));csv(OUT/'native_event_properties.csv',pd.DataFrame(nv))
    durations=[]
    for table in ('fast_slow','short_long_eff'):
        runs=(valid[table]!=valid[table].shift()).cumsum()
        for _,q in valid.groupby(runs):durations.append({'table':table,'cell':q[table].iloc[0],'start':q.trading_day.iloc[0],'end':q.trading_day.iloc[-1],'days':len(q),'pnl_log':q.pnl_log.sum()})
    csv(OUT/'condition_runs.csv',pd.DataFrame(durations))
    trades=pd.read_csv(OUT/'trades.csv.gz');trades['outcome']=np.where(trades.pnl_log>0,'winner',np.where(trades.pnl_log<0,'loser','flat'))
    csv(OUT/'trade_outcome_summary.csv',trades.groupby('outcome').agg(trades=('trade','size'),bars_mean=('bars','mean'),pnl_sum=('pnl_log','sum'),pnl_mean=('pnl_log','mean'),mfe_mean=('mfe_log','mean'),mae_mean=('mae_log','mean'),giveback_mean=('giveback_log','mean')).reset_index())
    csv(OUT/'native_sampling_summary.csv',native.groupby('view')[['bars_per_day','eff_1d','eff_5d','eff_20d','wick_1d']].mean().reset_index())
    # Explicit point examples supplement all ten full-event charts; they are
    # not extra tests. Worst day in largest drawdown, a ordinary winning
    # control from same year and realized-volatility tercile (median capture).
    e=ep.loc[(ep['rank']==1)&(ep.leg=='decline')].iloc[0];g=f.iloc[int(e.start_return_index):int(e.end_return_index_exclusive)]
    bad=g.groupby('trading_day').pnl_log.sum().idxmin()
    year=int(bad[:4]);v=valid.loc[valid.year==year].copy();v['vol_tercile']=pd.qcut(v.rv_1d,3,labels=False)
    band=int(v.loc[v.trading_day==bad,'vol_tercile'].iloc[0]);w=v.loc[(v.vol_tercile==band)&(v.pnl_log>0)].sort_values('capture')
    good=w.iloc[len(w)//2].trading_day
    candlestick_day(f,bad,OUT/'figures'/'largest_drawdown_worst_day.png','Largest drawdown: worst partial-event PnL day')
    candlestick_day(f,good,OUT/'figures'/'matched_winning_day.png','Winning control: same year / RV tercile, median positive capture')
    write_json(OUT/'point_examples.json',{'worst_day':bad,'winning_day':good,'matching':'same year and full-day realized-volatility tercile; choose median positive daily capture; descriptive only','worst_day_selection':'minimum summed PnL inside the fixed largest drawdown, then show full K-line day','additional_hypothesis_tests':0})
    # Compact result figure: all registered axes retained in CSV, selected
    # display rows follow financial mechanisms, not added statistical tests.
    a=pd.read_csv(OUT/'associations.csv');a=a.loc[a.outcome=='capture'].set_index('feature')
    show=['eff_1d','eff_5d','eff_20d','fast_share_1d','fast_share_5d','fast_share_20d','slow_work_velocity_5d','threshold_work_amplitude_5d']
    labels=['Path efficiency: 1 day','Path efficiency: 5 days','Path efficiency: 20 days','Fast variation: 1 day','Fast variation: 5 days','Fast variation: 20 days','Slow / work velocity: 5 days','Threshold / work amplitude: 5 days']
    fig,ax=plt.subplots(figsize=(11,6),layout='constrained');q=a.loc[show];yy=np.arange(len(q))
    ax.errorbar(q.rho,yy,xerr=np.vstack((q.rho-q.ci_low,q.ci_high-q.rho)),fmt='o',color='#3158a5',capsize=3)
    ax.set_yticks(yy,labels);ax.invert_yaxis();ax.axvline(0,color='#888',lw=.8);ax.grid(axis='x',alpha=.2);ax.set_xlabel('Within-year rank correlation with same-day capture (95% paired block-bootstrap interval)')
    ax.set_title('Fixed original strategy: scale and lookback matter\n1,192 consumed development days; retrospective association, not prediction')
    savefig(fig,OUT/'figures'/'scale_associations.png')
    s=pd.read_csv(OUT/'synthetic_wave_grid.csv');q=s.loc[(s.kind=='wave')&(s.slow_phase==0)]
    fig,ax=plt.subplots(figsize=(10,5.5),layout='constrained')
    for ratio,g in q.groupby('slow_velocity_ratio'):
        ax.plot(g.period_bars,g.capture,marker='o',label=f'Slow / fast maximum velocity = {ratio:g}')
    ax.set_xscale('log');ax.set_xticks([6,8,12,24,48,96,240],[6,8,12,24,48,96,240]);ax.axhline(0,color='#888',lw=.8);ax.grid(alpha=.2);ax.legend(fontsize=9);ax.set_xlabel('Fast wave period (5-minute bars)');ax.set_ylabel('Signed PnL / total absolute price path')
    ax.set_title('Same filter, threshold and full exposure on controlled sine waves\nNo noise, no costs, no gap; slow period = 960 bars; phase = 0')
    savefig(fig,OUT/'figures'/'synthetic_mechanism.png')
    print(json.dumps({'completed_controls':True,'example_days':[bad,good],'policy_candidates':0}))
if __name__=='__main__':complete()
