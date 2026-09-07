"""V3.1 older-history support audit. No model fitting and no evaluation-year reuse."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
RESEARCH = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(RESEARCH / 'first_shock_seconds_v2/code'))
sys.path.insert(0, str(RESEARCH / 'first_shock_gate_v1/code'))
import morphology_v3 as m3
import seconds_v2 as v2
import first_shock_gate as g

RANGES = {
    '000688.SH': ('2020-07-23', '2023-12-31'),
    '000852.SH': ('2015-01-05', '2023-12-31'),
}


def generalized_minute_panel(native: pd.DataFrame, symbol: str) -> pd.DataFrame:
    required = {'symbol','timestamp','trading_day','close','causal_flat_fill','high_frequency_analysis_eligible'}
    if not required <= set(native): raise ValueError(f'missing {required-set(native)}')
    x=native.copy()
    if set(x.symbol)!={symbol}: raise ValueError('unexpected symbol')
    x['ts']=pd.to_datetime(x.timestamp.str[:19])
    if not (x.ts.dt.strftime('%Y-%m-%d')==x.trading_day).all(): raise ValueError('calendar-clock mismatch')
    if x.ts.duplicated().any(): raise ValueError('duplicate minute timestamp')
    close=pd.to_numeric(x.close,errors='coerce')
    ok=x.high_frequency_analysis_eligible.eq(True)&x.causal_flat_fill.eq(False)&(close>0)
    x['analysis_close']=close.where(ok)
    parts=[]
    for day,group in x.groupby('trading_day',sort=True):
        by=group.set_index('ts').analysis_close
        for afternoon,opening in enumerate(('09:30:00','13:00:00')):
            grid=pd.date_range(f'{day} {opening}',periods=121,freq='min')[1:]
            p=by.reindex(grid).to_numpy(float)
            r=np.r_[np.nan,np.diff(np.log(p))]*1e4
            parts.append(pd.DataFrame({'session':f'{day}/{afternoon}','day':day,'year':int(day[:4]),
                'minute':np.arange(1,121),'afternoon':afternoon,'return_bp':r,'source_valid':np.isfinite(p)}))
    return pd.concat(parts,ignore_index=True)


def generalized_first_features(panel: pd.DataFrame) -> pd.DataFrame:
    f=panel.reset_index(drop=True).copy()
    for col in ('sigma_pre','event','first'): f[col]=np.nan
    for _,idx in f.groupby('session',sort=False).groups.items():
        idx=np.asarray(idx);r=f.loc[idx,'return_bp'].to_numpy(float)
        rv30=g.roll_mean(r*r,30);sigma=np.sqrt(np.r_[np.nan,rv30[:-1]])
        ev=g.event_flags(r,sigma);lab=g.event_labels(ev)
        f.loc[idx,'sigma_pre']=sigma;f.loc[idx,'event']=ev;f.loc[idx,'first']=lab['first']
    return f


def read_seconds_year(root: Path, symbol: str, year: int):
    sys.path.insert(0,str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    start=f'{year}-01-01';end=f'{year}-12-31'
    if symbol=='000688.SH' and year==2020: start='2020-07-23'
    if symbol=='000852.SH' and year==2015: start='2015-01-05'
    frame=load_market_data(symbol,'3s',start,end,root=root)
    need={'observation_datetime','price','row_index','trading_day','symbol'}
    if not need <= set(frame): raise ValueError(f'missing {need-set(frame)}')
    if frame.duplicated(['symbol','observation_datetime','row_index']).any(): raise ValueError('bad source key')
    ts=frame.market_time_shanghai.dt.tz_localize(None)
    q=frame[['trading_day','row_index','price']].copy()
    q['second_day']=(ts.dt.hour*3600+ts.dt.minute*60+ts.dt.second).to_numpy()
    q['afternoon']=(q.second_day>=13*3600).astype(int)
    q['session']=q.trading_day+'/'+q.afternoon.astype(str)
    q['second']=q.second_day-np.where(q.afternoon==1,13*3600,9*3600+30*60)
    audit={'symbol':symbol,'year':year,'source_rows':len(frame),
           'in_session_rows':int(q.second.between(0,7200).sum()),
           'same_second_extra':int(frame.duplicated(['symbol','observation_datetime']).sum())}
    return q[q.second.between(0,7200)].copy(),audit


def classify(root: Path, symbol: str, gap_limit: int):
    sys.path.insert(0,str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    start,end=RANGES[symbol]
    native=load_market_data(symbol,'1m',start,end,root=root)
    feat=generalized_first_features(generalized_minute_panel(native,symbol))
    years=sorted(feat.year.unique())
    records=[];audits=[]
    for year in years:
        seconds,audit=read_seconds_year(root,symbol,int(year));groups={s:z for s,z in seconds.groupby('session',sort=False)}
        yr=feat[feat.year==year]
        for session,ix in yr.groupby('session',sort=False).groups.items():
            ix=np.asarray(ix);raw=groups.get(session)
            if raw is None: t=np.array([]);p=np.array([]);rr=np.array([],dtype=int)
            else: t=raw.second.to_numpy(float);p=raw.price.to_numpy(float);rr=raw.row_index.to_numpy()
            sample=v2.sample_session(t,p,rr,15,gap_limit)
            morph=[m3.minute_morphology(sample,j) for j in range(1,121)]
            rf=m3.first_roundtrip([x.get('roundtrip') if x.get('minute_support') else None for x in morph])
            for local,row_ix in enumerate(ix):
                row=feat.loc[row_ix];mm=morph[local]
                tail=bool(row['first']==1) if np.isfinite(row['first']) else False
                if tail:
                    if mm.get('quiet_pre') is True: tc='quiet_first_tail'
                    elif mm.get('active_pre') is True: tc='active_continuation_tail'
                    elif mm.get('pre_support') is True: tc='intermediate_tail'
                    else: tc='unknown_tail'
                else: tc=None
                round_first=bool(rf[local]==1) if np.isfinite(rf[local]) else False
                if round_first:
                    if mm.get('quiet_pre') is True: rc='quiet_roundtrip'
                    elif mm.get('active_pre') is True: rc='active_roundtrip'
                    elif mm.get('pre_support') is True: rc='intermediate_roundtrip'
                    else: rc='unknown_roundtrip'
                else: rc=None
                if tail or round_first:
                    records.append({'symbol':symbol,'year':int(year),'day':row.day,'session':row.session,
                        'minute':int(row.minute),'tail_first':tail,'tail_class':tc,
                        'roundtrip_first':round_first,'roundtrip_class':rc,
                        'official_minute_return_bp':float(row.return_bp) if np.isfinite(row.return_bp) else None,
                        **mm})
        audit['gap_limit_seconds']=gap_limit;audits.append(audit)
        print('HISTORY_MEASURED',symbol,year,'gap',gap_limit)
    return pd.DataFrame(records),audits


def counts(events: pd.DataFrame):
    out=[]
    for symbol in RANGES:
        s=events[events.symbol==symbol]
        for year in sorted(s.year.unique()):
            y=s[s.year==year];tail=y[y.tail_first.astype(bool)];rnd=y[y.roundtrip_first.astype(bool)]
            out.append({'symbol':symbol,'year':int(year),'tail_events':len(tail),
                'quiet_first_tail':int((tail.tail_class=='quiet_first_tail').sum()),
                'active_continuation_tail':int((tail.tail_class=='active_continuation_tail').sum()),
                'intermediate_tail':int((tail.tail_class=='intermediate_tail').sum()),
                'unknown_tail':int((tail.tail_class=='unknown_tail').sum()),
                'roundtrip_first':len(rnd),'quiet_roundtrip':int((rnd.roundtrip_class=='quiet_roundtrip').sum()),
                'active_roundtrip':int((rnd.roundtrip_class=='active_roundtrip').sum()),
                'intermediate_roundtrip':int((rnd.roundtrip_class=='intermediate_roundtrip').sum()),
                'unknown_roundtrip':int((rnd.roundtrip_class=='unknown_roundtrip').sum())})
    return pd.DataFrame(out)


def readiness(table: pd.DataFrame):
    rows=[]
    for symbol in RANGES:
        s=table[table.symbol==symbol].sort_values('year')
        for cls in ('quiet_first_tail','roundtrip_first','quiet_roundtrip'):
            cum=0
            for _,r in s.iterrows():
                cum+=int(r[cls]);rows.append({'symbol':symbol,'event_family':cls,'through_year':int(r.year),
                    'cumulative_independent_anchors':cum,'minimum':20,'ready':cum>=20})
    return pd.DataFrame(rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();root=args.repo_root.resolve();out=args.out.resolve()
    if out.exists() and any(out.iterdir()): raise FileExistsError('immutable outputs')
    out.mkdir(parents=True,exist_ok=True)
    prim=[];strict=[];audit={}
    for symbol in RANGES:
        p,a=classify(root,symbol,15);p['support_mode']='gap15';prim.append(p);audit[symbol]=a
        s,_=classify(root,symbol,3);s['support_mode']='gap3';strict.append(s)
    primary=pd.concat(prim,ignore_index=True);strict=pd.concat(strict,ignore_index=True)
    ct=counts(primary);rd=readiness(ct)
    primary.to_csv(out/'historical_taxonomy_gap15.csv',index=False)
    strict.to_csv(out/'historical_taxonomy_gap3.csv',index=False)
    ct.to_csv(out/'historical_counts.csv',index=False);rd.to_csv(out/'historical_readiness.csv',index=False)
    g.write_json(out/'historical_source_audit.json',audit)
    g.write_json(out/'summary.json',{'status':'completed support audit; no model fit','counts':ct.to_dict('records'),
        'readiness':rd.to_dict('records'),'fresh_oos':False,'production_authority':False})
    print(ct.to_string(index=False));print(rd.groupby(['symbol','event_family']).tail(1).to_string(index=False))

if __name__=='__main__': main()
