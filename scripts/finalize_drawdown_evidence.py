"""Derive closeout tables from frozen evidence, without model/account replay."""
import hashlib,json
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/drawdown_conditions'
out=OUT/'closeout';out.mkdir(exist_ok=True)
v=pd.read_csv(OUT/'descriptive/bar_attribution.csv.gz')
summary=json.loads((OUT/'descriptive/summary.json').read_text())
rows=[]
for rank,e in enumerate(summary['episodes'],1):
    for phase,start,end in [('decline',e['peak_index'],e['trough_index']),
                            ('recovery',e['trough_index'],e['end_index'])]:
        z=v.iloc[start:end]
        if z.empty:continue
        # Both state flags are lagged to the actual PnL interval in the source.
        s=z.slow_conflict.astype(bool);c=z.chop.astype(bool)
        d={'rank':rank,'phase':phase,'bars':len(z),'trading_days':z.trading_day.nunique(),
           'pnl_log':z.pnl_log.sum(),'mean_pnl_bps':z.pnl_log.mean()*1e4,
           'long_log_pnl':z.loc[z.exec_pos>0,'pnl_log'].sum(),
           'short_log_pnl':z.loc[z.exec_pos<0,'pnl_log'].sum(),
           'negative_log_sum':z.pnl_log.clip(upper=0).sum(),
           'positive_log_sum':z.pnl_log.clip(lower=0).sum(),
           'joint_share':(s&c).mean(),'joint_log_pnl':z.loc[s&c,'pnl_log'].sum(),
           'slow_only_share':(s&~c).mean(),'slow_only_log_pnl':z.loc[s&~c,'pnl_log'].sum(),
           'chop_only_share':(~s&c).mean(),'chop_only_log_pnl':z.loc[~s&c,'pnl_log'].sum(),
           'neither_share':(~s&~c).mean(),'neither_log_pnl':z.loc[~s&~c,'pnl_log'].sum(),
           'overnight_gap_log_pnl':z.overnight_gap_log_pnl.sum()}
        assert abs(sum(d[k] for k in ['joint_log_pnl','slow_only_log_pnl','chop_only_log_pnl','neither_log_pnl'])-d['pnl_log'])<1e-10
        rows.append(d)
pd.DataFrame(rows).to_csv(out/'top10_decline_recovery_condition_cells.csv',index=False)
tables=[pd.read_csv(OUT/'sessions'/str(y)/'policy_metrics.csv') for y in range(2021,2026)]
all_metrics=pd.concat(tables,ignore_index=True)
all_metrics.to_csv(out/'all_policy_metrics.csv',index=False)
tables[-1].loc[tables[-1].scope=='cumulative'].to_csv(out/'five_year_metrics.csv',index=False)
qs=pd.concat([pd.read_csv(OUT/'sessions'/str(y)/'quarterly_accounts.csv') for y in range(2021,2026)])
qs.to_csv(out/'quarterly_accounts.csv',index=False)
disp=[]
for cid in ['slow_conflict_half','chop_half']:
    for cost in [0,1,3,5]:
        a=all_metrics[(all_metrics.view==0)&(all_metrics.scope=='annual')&(all_metrics.cost_bps==cost)].pivot(index='year',columns='policy')
        mdd_improvement=a['mdd'][cid+'_matched_constant']-a['mdd'][cid]
        ret_delta=a['total_log_return'][cid]-a['total_log_return'][cid+'_matched_constant']
        q=qs[qs.cost_bps==cost].pivot(index='quarter',columns='policy',values='total_log_return')
        # Annual matched controls vary by year: this is a matched descriptive comparison.
        qd=q[cid]-q[cid+'_matched_constant']
        disp.append({'policy':cid,'cost_bps':cost,'annual_mdd_better_count':int((mdd_improvement>1e-10).sum()),
            'annual_mdd_worse_count':int((mdd_improvement<-1e-10).sum()),
            'annual_log_return_better_count':int((ret_delta>1e-10).sum()),
            'annual_mdd_improvement_median':float(mdd_improvement.median()),
            'positive_quarter_log_delta_count':int((qd>1e-10).sum()),
            'negative_quarter_log_delta_count':int((qd<-1e-10).sum()),
            'quarter_log_delta_median':float(qd.median()),
            'note':'diagnostic distribution only; no promotion gate relaxed or fresh OOS claimed'})
pd.DataFrame(disp).to_csv(out/'dispersion.csv',index=False)
print(pd.DataFrame(rows).head(6).to_string(index=False))
print(pd.DataFrame(disp).to_string(index=False))
