"""Derive validation and comparisons solely from frozen account snapshots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/conditional_bucket_accounts_v1p3'


def save(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')


def audit_accounts(mode):
    folder=OUT/mode;summary=pd.read_csv(folder/'summary.csv');results=[]
    for s in summary.itertuples():
        p=folder/f'{s.underlying}_{s.carrier}_{s.policy}'
        trades=pd.read_parquet(p/'trades.parquet');orders=pd.read_parquet(p/'orders.parquet');marks=pd.read_parquet(p/'marks.parquet');segments=pd.read_parquet(p/'drawdown_segments.parquet')
        qmult=10000 if s.carrier=='option' else 1
        cash=100000.;max_cash_error=0.;dividend_paid=False
        for o in orders.itertuples():
            day=pd.Timestamp(o.time_ns,tz='UTC').tz_convert('Asia/Shanghai').strftime('%Y-%m-%d')
            if str(s.underlying)=='588080' and day>='2025-10-22' and not dividend_paid:
                cash+=float(trades.dividend.fillna(0).sum()) if len(trades) else 0
                dividend_paid=True
            if o.side=='buy':cash-=o.quantity*qmult*o.price+o.fee
            elif o.side=='sell':cash+=o.quantity*qmult*o.price-o.fee
            else:assert o.side=='expiry' and o.price==0 and o.fee==0
            max_cash_error=max(max_cash_error,abs(cash-o.cash_after))
            if o.side in ['buy','sell']:
                expected=o.quantity*4.5 if s.carrier=='option' else o.quantity*o.price*.0002
                assert abs(expected-o.fee)<1e-9
                assert o.price>0
        nav_error=float(np.max(abs(marks.cash+marks.receivable+marks.quantity*marks.multiplier*marks.bid-marks.nav)))
        assert nav_error<1e-8 and max_cash_error<1e-6
        assert abs(float(orders.fee.sum())-s.fees)<1e-7
        assert abs(float(marks.nav.iloc[-1])-s.terminal_nav)<1e-7
        assert abs(float(marks.running_mdd.max())-s.max_drawdown)<1e-12
        if len(trades):
            assert (trades.exit_ns>=trades.entry_ns).all()
            assert (trades.entry_ns>trades.entry_signal_ns).all()
            calc=(trades.exit_price-trades.entry_price)*trades.quantity*trades.multiplier-trades.entry_fee-trades.exit_fee+trades.dividend.fillna(0)
            assert np.allclose(calc,trades.net_pnl,rtol=0,atol=1e-8)
            if s.carrier=='spot':
                first=pd.to_datetime(trades.entry_ns,utc=True).dt.tz_convert('Asia/Shanghai').dt.date
                last=pd.to_datetime(trades.exit_ns,utc=True).dt.tz_convert('Asia/Shanghai').dt.date
                assert (last>first).all()
        end=marks.iloc[-1];open_pnl=0.
        if end.quantity:
            last_buy=orders.loc[orders.side=='buy'].iloc[-1]
            open_pnl=end.quantity*end.multiplier*(end.bid-last_buy.price)-last_buy.fee
            if str(s.underlying)=='588080' and pd.Timestamp(last_buy.time_ns,tz='UTC').tz_convert('Asia/Shanghai').strftime('%Y-%m-%d')<='2025-10-16':open_pnl+=end.quantity*.014
        total=float(trades.net_pnl.sum())+open_pnl if len(trades) else open_pnl
        assert abs(total-s.net_pnl)<1e-6,(s.policy,s.carrier,total,s.net_pnl)
        daily=marks.sort_values('time_ns').groupby('day',sort=True).tail(1).copy()
        daily['net_change']=daily.nav.diff().fillna(daily.nav.iloc[0]-100000)
        daily['month']=daily.day.str[:7]
        monthly=daily.groupby('month').net_change.sum().reset_index()
        monthly.to_csv(p/'monthly_pnl.csv',index=False)
        results.append({'policy':s.policy,'carrier':s.carrier,'underlying':str(s.underlying),
            'accounting_passed':True,'cash_reconstruction_max_error':max_cash_error,
            'nav_identity_max_error':nav_error,'open_marked_pnl':float(open_pnl),
            'closed_net_pnl':float(trades.net_pnl.sum()) if len(trades) else 0.,
            'economic_valid':s.coverage_incidents==0,'coverage_incidents':int(s.coverage_incidents),
            'quote_points_scanned':int(segments.quote_count.sum()) if len(segments) else 0})
    save(folder/'account_validation.json',results)
    return summary,results


def report():
    base,_=audit_accounts('baseline');family,checks=audit_accounts('family')
    f=pd.read_parquet(OUT/'frozen_signals.parquet');m={p:dict(zip(f.time.astype('int64'),f[p])) for p in family.policy.unique()}
    rows=[];monthly=[]
    for s in family.itertuples():
        b=base.loc[(base.carrier==s.carrier)&(base.underlying==s.underlying)].iloc[0]
        p=OUT/'family'/f'{s.underlying}_{s.carrier}_{s.policy}'
        bp=OUT/'baseline'/f'{s.underlying}_{s.carrier}_baseline'
        bt=pd.read_parquet(bp/'trades.parquet')
        denied=bt.loc[bt.entry_signal_ns.map(m[s.policy]).fillna(0)==0] if len(bt) else bt
        gross=denied.net_pnl+denied.entry_fee+denied.exit_fee if len(denied) else pd.Series(dtype=float)
        avoided=float(-gross.clip(upper=0).sum());foregone=float(gross.clip(lower=0).sum())
        delta=float(s.net_pnl-b.net_pnl);fee_saved=float(b.fees-s.fees)
        valid=s.coverage_incidents==0
        rows.append({'underlying':s.underlying,'carrier':s.carrier,'policy':s.policy,
            'net_pnl':s.net_pnl,'cagr':s.cagr_2025,'mdd':s.max_drawdown,'mean_net_trade':s.mean_net_trade,
            'trades':s.completed_trades,'fees':s.fees,'calmar':s.calmar,
            'delta_net_pnl':delta,'delta_mdd':s.max_drawdown-b.max_drawdown,
            'delta_mean_trade':s.mean_net_trade-b.mean_net_trade,
            'trade_reduction':1-s.completed_trades/b.completed_trades,
            'avoided_baseline_gross_loss':avoided,'foregone_baseline_gross_profit':foregone,
            'saved_fees':fee_saved,'path_and_terminal_residual':delta-(avoided-foregone+fee_saved),
            'hard_valid':valid,'joint_goals':bool(valid and s.max_drawdown<b.max_drawdown-1e-12 and s.mean_net_trade>b.mean_net_trade+1e-9),
            'positive_net_account':s.net_pnl>0,'open_inventory':s.terminal_quantity})
        a=pd.read_csv(p/'monthly_pnl.csv');z=pd.read_csv(bp/'monthly_pnl.csv');a=a.merge(z,on='month',suffixes=('','_baseline'))
        a['delta']=a.net_change-a.net_change_baseline;a['policy']=s.policy;a['carrier']=s.carrier;a['underlying']=s.underlying;monthly.append(a)
    r=pd.DataFrame(rows);r.to_csv(OUT/'comparison.csv',index=False)
    pd.concat(monthly,ignore_index=True).to_csv(OUT/'monthly_comparison.csv',index=False)
    for key,g in r.groupby(['underlying','carrier']):
        baseline=g.loc[g.policy=='baseline'].iloc[0]
        assert abs(baseline.delta_net_pnl)<1e-7 and abs(baseline.delta_mdd)<1e-12 and abs(baseline.delta_mean_trade)<1e-7,key
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,1,figsize=(13,10),layout='constrained')
    for ax,(u,c) in zip(axes,[('588000','spot'),('588000','option'),('588080','spot')]):
        for name in family.policy.unique():
            p=OUT/'family'/f'{u}_{c}_{name}'
            a=pd.read_parquet(p/'marks.parquet').groupby('day',sort=True).tail(1)
            ax.plot(pd.to_datetime(a.day),a.nav-100000,label=name,lw=1)
        ax.set_title(f'{u} {c}: net PnL (CNY), fixed units, 2025 consumed history')
        ax.grid(alpha=.2);ax.legend(ncol=3,fontsize=7)
    fig.savefig(OUT/'account_comparison.png',dpi=140);plt.close(fig)
    print(r[['underlying','carrier','policy','net_pnl','mdd','mean_net_trade','trades','joint_goals']].to_string(index=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['baseline','family','report'],required=True);a=p.parse_args()
    if a.mode=='report':report()
    else:
        s,r=audit_accounts(a.mode);print(s.to_string(index=False));print(json.dumps(r,ensure_ascii=False))
