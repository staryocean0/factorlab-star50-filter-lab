"""Audit frozen V2 sample attrition and observable pre-event state. No fitting.

This is a post-V2 measurement audit, NOT a new predictive validation. Thresholds,
source admission and frozen model outputs are not changed. Source reads stay in
2021-2025. Core functions can be tested without pyarrow or original market data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np
import pandas as pd

SYMBOLS = ('000688.SH', '000852.SH')
BASE_REF = '424a6b5a931cf610aa731125aa2081cdf3accbbb'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def consecutive_true(mask):
    """At each physical row, length of the trailing uninterrupted valid run."""
    x = np.asarray(mask, bool)
    if x.ndim != 1:
        raise ValueError('need vector')
    ix = np.arange(len(x))
    return np.where(x, ix - np.maximum.accumulate(np.where(~x, ix, -1)), 0)


def state_from_returns(r, threshold_bp=30.):
    """Five minute returns include SIX prices; zero anchors the starting price.

    Low range is relative to a fixed 30bp criterion, NOT a zero-risk/quiet proof.
    Directional and wide-returning states are descriptive; no new event label.
    """
    r = np.asarray(r, float)
    if len(r) != 5 or not np.isfinite(r).all():
        return {'state': 'unknown', 'net_bp': None, 'range_bp': None}
    x = np.r_[0., np.cumsum(r)]
    net, span = float(x[-1]), float(x.max() - x.min())
    if abs(net) >= threshold_bp:
        kind = 'already_displaced_30bp'
    elif span >= threshold_bp:
        kind = 'wide_returning_30bp'
    else:
        kind = 'low_observed_range_below30bp'
    return {'state': kind, 'net_bp': net, 'range_bp': span}


def snapshot_prefix(t, p, row, end_second):
    """Strict trailing 5m source path at decision, never in the event minute."""
    t, p, row = np.asarray(t,float), np.asarray(p,float), np.asarray(row)
    if len(t)!=len(p) or len(t)!=len(row):
        raise ValueError('source shapes')
    order=np.lexsort((row,t)); t,p,row=t[order],p[order],row[order]
    end=float(end_second); start=end-300
    a=np.searchsorted(t,start,side='right')-1
    b=np.searchsorted(t,end,side='right')-1
    out={'state':'unknown', 'complete_3s':False, 'net_bp':None, 'range_bp':None,
         'max_gap_seconds':None, 'start_age':None, 'end_age':None}
    if a<0 or b<=a or start<0:
        return out
    tt=t[a:b+1]; pp=p[a:b+1]; gaps=np.diff(tt)
    out.update(max_gap_seconds=float(gaps.max()),start_age=float(start-t[a]),end_age=float(end-t[b]))
    good=(out['start_age']<=3 and out['end_age']<=3 and (gaps>0).all()
          and (gaps<=3).all() and np.isfinite(pp).all() and (pp>0).all())
    if not good:
        return out
    logp=np.log(pp/pp[0])*1e4
    net=float(logp[-1]); span=float(logp.max()-logp.min())
    kind=('already_displaced_30bp' if abs(net)>=30 else
          'wide_returning_30bp' if span>=30 else 'low_observed_range_below30bp')
    out.update(state=kind,complete_3s=True,net_bp=net,range_bp=span)
    return out


def eligible_pre_event_rows(minutes, eligible, close_minute):
    m=np.asarray(minutes,int); ok=np.asarray(eligible,bool)
    if m.shape!=ok.shape: raise ValueError('shape mismatch')
    return (m>=close_minute-15)&(m<=close_minute-2)&ok


def first_loss(base_ok, short_ok, long_ok, scale_ok, own_ok, joint_ok):
    """Exclusive waterfall; order declared, not structural causal attribution."""
    masks=[np.asarray(x,bool) for x in (base_ok,short_ok,long_ok,scale_ok,own_ok,joint_ok)]
    if len({x.shape for x in masks})!=1: raise ValueError('shape mismatch')
    result=np.full(masks[0].shape,'retained',dtype=object)
    result[~masks[0]]='base_ineligible'
    active=masks[0].copy()
    for name,condition in zip(('short5m','long15m','scale_windows','other_fine_fields','partner_support'),masks[1:]):
        result[active&~condition]=name
        active&=condition
    return result


def save_json(path,obj):
    def clean(x):
        if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
        if isinstance(x,(tuple,list)):return [clean(v) for v in x]
        if isinstance(x,np.generic):return clean(x.item())
        if isinstance(x,float) and not np.isfinite(x):return None
        return x
    Path(path).write_text(json.dumps(clean(obj),ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(); root=args.root.resolve(); out=args.out.resolve()
    if out.exists() and any(out.iterdir()):raise FileExistsError('do not overwrite evidence')
    out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(root/'docs/research/first_shock_seconds_v2/code'))
    import seconds_v2 as v
    g=v.g
    # Frozen validator hashes all twenty authorized physical Parquet inputs.
    v.validate_inputs(root,out)
    sys.path.insert(0,str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    minute={s:g.minute_panel(load_market_data(s,'1m','2021-01-01','2025-12-31',root=root),s) for s in SYMBOLS}
    common=set(minute[SYMBOLS[0]].session)&set(minute[SYMBOLS[1]].session)
    minute={s:q[q.session.isin(common)].reset_index(drop=True) for s,q in minute.items()}
    if not minute[SYMBOLS[0]][['session','minute']].equals(minute[SYMBOLS[1]][['session','minute']]):raise ValueError('unpaired')
    joint_min=np.isfinite(minute[SYMBOLS[0]].return_bp)&np.isfinite(minute[SYMBOLS[1]].return_bp)
    for q in minute.values():q.loc[~joint_min,'return_bp']=np.nan
    base={s:v.aligned_targets(g.make_features(q)) for s,q in minute.items()}
    fine={}; sessions=[]; gap_records=[]; phase_records=[]; snapshot_states={}
    for s in SYMBOLS:
        parts=[]
        for year in range(2021,2026):
            raw,audit=v.read_seconds(root,s,year)
            groups={key:z for key,z in raw.groupby('session',sort=False)}
            hist={}; phase=np.zeros(60,np.int64)
            for key,z in base[s][base[s].year==year].groupby('session',sort=False):
                src=groups.get(key)
                if src is None:t=np.array([]);p=np.array([]);row=np.array([],int)
                else:
                    t=src.second.to_numpy(float);p=src.price.to_numpy(float);row=src.row_index.to_numpy()
                    order=np.lexsort((row,t));t,p,row=t[order],p[order],row[order]
                if len(t)>1:
                    vals,counts=np.unique(np.diff(t),return_counts=True)
                    for gap,n in zip(vals,counts):hist[float(gap)]=hist.get(float(gap),0)+int(n)
                phase+=np.bincount(t.astype(int)%60,minlength=60)
                sample=v.sample_session(t,p,row,15,15)
                ff=v.fine_features(sample)
                ff['session']=key;parts.append(ff)
                run=consecutive_true(np.isfinite(sample['return_bp']))
                valid=np.isfinite(sample['return_bp'][1:])
                stage5=np.isfinite(ff.fine_log_rv5).to_numpy()
                stage15=np.isfinite(ff.fine_log_rv15).to_numpy()
                stageall=np.isfinite(ff[v.FINE+v.SCALE]).all(axis=1).to_numpy()
                # The no-gap endpoint-only count is an availability counterfactual.
                # Its intermediate path is unknown; it is NOT admitted for features.
                prices=sample['price']; endpoint_pair=np.isfinite(prices[1:])&np.isfinite(prices[:-1])
                phases={f'valid15_end_mod60_{k}':int(valid[(sample['second'][1:]%60)==k].sum()) for k in (0,15,30,45)}
                sessions.append({'symbol':s,'year':year,'session':key,'day':z.day.iloc[0],
                    'source_rows':len(t),'max_gap_seconds':float(np.max(np.diff(t))) if len(t)>1 else None,
                    'valid15_returns':int(valid.sum()),'fresh_endpoint_pairs':int(endpoint_pair.sum()),
                    'crossgap_loss_with_fresh_endpoints':int((endpoint_pair&~valid).sum()),
                    'max_consecutive_valid15':int(run.max()),
                    'valid5m_windows':int(stage5.sum()),'valid15m_windows':int(stage15.sum()),
                    'all_fine_windows':int(stageall.sum()),
                    'base_decisions':int(z.decision_ok.sum()),
                    'retained_own_decisions':int((z.decision_ok.to_numpy()&stageall).sum()),**phases})
                for _,e in z[(z['first']==1)&(z.minute>=33)].iterrows():
                    latest=min(int(e.minute)-2,105)
                    snapshot_states[(s,key,int(e.minute))]=snapshot_prefix(t,p,row,latest*60)
            for gap,count in sorted(hist.items()):gap_records.append({'symbol':s,'year':year,'gap_seconds':gap,'count':count})
            for k,n in enumerate(phase):phase_records.append({'symbol':s,'year':year,'second_mod60':k,'source_rows':int(n)})
            print('AUDITED',s,year,flush=True)
            del raw,groups
        qfine=pd.concat(parts,ignore_index=True)
        if not qfine.session.equals(minute[s].session):raise ValueError('feature order')
        fine[s]=qfine.drop(columns='session')
    own={s:np.isfinite(fine[s][v.FINE+v.SCALE]).all(axis=1).to_numpy() for s in SYMBOLS}
    joint=own[SYMBOLS[0]]&own[SYMBOLS[1]]
    waterfall=[]; support=[]; events=[]
    for s in SYMBOLS:
        q=base[s]; ff=fine[s]; short=np.isfinite(ff.fine_log_rv5).to_numpy();long=np.isfinite(ff.fine_log_rv15).to_numpy()
        scales=np.isfinite(ff[v.SCALE]).all(axis=1).to_numpy()
        labels=first_loss(q.decision_ok,short,long,scales,own[s],joint)
        decision=q.decision_ok.to_numpy()&joint
        metric=decision&np.isfinite(q.target.to_numpy())
        for year,ix in q.groupby('year',sort=True).groups.items():
            ix=np.asarray(ix)
            for reason,n in pd.Series(labels[ix]).value_counts().items():
                waterfall.append({'symbol':s,'year':int(year),'first_failing_stage':reason,'rows':int(n)})
            support.append({'symbol':s,'year':int(year),'rows':len(ix),
                'base_decisions':int(q.loc[ix,'decision_ok'].sum()),'fine_decisions':int(decision[ix].sum()),
                'mature_decisions':int(metric[ix].sum()),
                'actionable_positive_windows':int(q.loc[ix[metric[ix]],'target'].sum()),
                'known_first_events':int(((q.loc[ix,'first']==1)&(q.loc[ix,'minute']>=33)).sum())})
        for key,ix in q.groupby('session',sort=False).groups.items():
            ix=np.asarray(ix); z=q.loc[ix]; mins=z.minute.to_numpy(int)
            r=z.return_bp.to_numpy(float)
            for local in np.flatnonzero((z['first'].to_numpy()==1)&(mins>=33)):
                e=int(mins[local]);latest=min(e-2,105)
                prefix=state_from_returns(r[latest-5:latest])
                eligible=eligible_pre_event_rows(mins,metric[ix],e)
                based=eligible_pre_event_rows(mins,z.metric_ok.to_numpy(bool),e)
                snap=snapshot_states[(s,key,e)]
                events.append({'symbol':s,'year':int(z.year.iloc[0]),'session':key,'day':z.day.iloc[0],
                    'event_close_minute':e,'event_return_bp':float(r[local]),
                    'prefix_decision_minute':latest,'minimum_pre_onset_lead_minutes':e-1-latest,
                    'base_positive_decisions':int(based.sum()),'v2_positive_decisions':int(eligible.sum()),
                    'covered_by_v2':bool(eligible.any()),
                    **{'minute5m_'+k:val for k,val in prefix.items()},
                    **{'snapshot5m_'+k:val for k,val in snap.items()}})
    support=pd.DataFrame(support); events=pd.DataFrame(events);sessions=pd.DataFrame(sessions)
    expected=pd.read_csv(Path(__file__).with_name('expected_support.csv'))
    expected=expected[expected.version=='primary_joint_gap15'].drop(columns='version')
    cols=['symbol','year','rows','base_decisions','fine_decisions','mature_decisions','actionable_positive_windows','known_first_events']
    pd.testing.assert_frame_equal(support[cols].sort_values(['symbol','year']).reset_index(drop=True),
                                  expected[cols].sort_values(['symbol','year']).reset_index(drop=True),check_dtype=False)
    for name,table in [('support_reproduced.csv',support),('waterfall.csv',pd.DataFrame(waterfall)),
                       ('sessions.csv',sessions),('source_gaps.csv',pd.DataFrame(gap_records)),
                       ('source_second_positions.csv',pd.DataFrame(phase_records)),('events_prefix.csv',events)]:
        table.to_csv(out/name,index=False)
    month=sessions.assign(month=sessions.day.str[:7]).groupby(['symbol','year','month']).agg(
        sessions=('session','size'),source_rows=('source_rows','sum'),valid15_returns=('valid15_returns','sum'),
        max_run15=('max_consecutive_valid15','max'),own_decisions=('retained_own_decisions','sum')).reset_index()
    month.to_csv(out/'months.csv',index=False)
    event_counts=events.groupby(['symbol','year']).agg(known_first_events=('covered_by_v2','size'),
                      unique_events_covered=('covered_by_v2','sum'),positive_windows=('v2_positive_decisions','sum')).reset_index()
    # First events cannot overlap within a 15m horizon because quiet interval=30.
    merged=event_counts.merge(support,on=['symbol','year'],suffixes=('_ledger','_support'))
    if not (merged.positive_windows==merged.actionable_positive_windows).all():raise AssertionError('event-window bridge')
    event_counts.to_csv(out/'event_support.csv',index=False)
    for prefix in ['minute5m','snapshot5m']:
        events.groupby(['symbol','year',prefix+'_state']).size().rename('events').reset_index().to_csv(out/f'{prefix}_states.csv',index=False)
    gapframe=pd.DataFrame(gap_records)
    summary={'status':'completed measurement audit; no refit, no new predictive validation',
        'unique_training_events':event_counts[event_counts.year.isin([2021,2022])].to_dict('records'),
        'year2021_gaps_top10':gapframe[gapframe.year==2021].sort_values('count',ascending=False).groupby('symbol').head(10).to_dict('records'),
        'yearly_max_run15':sessions.groupby(['symbol','year']).max_consecutive_valid15.max().reset_index().to_dict('records'),
        'evaluation_prefix_states':events[events.year>=2024].groupby(['symbol','snapshot5m_state']).size().rename('n').reset_index().to_dict('records'),
        'frozen_v2_primary_support_reproduced':'10/10 index-years exact',
        'first_event_positive_window_bridge':'exact all years',
        'requirements_not_changed':True,'models_refitted':False,'fresh_oos':False,'production_authority':False,
        'limits':['prefix categories are descriptive, not newly validated forecasting targets',
                  '30bp low observed range does not prove a stationary or safe environment',
                  'no interpolation, no gap-limit relaxation, no lowering of training-event minimum',
                  'gap schedule identifies archive behaviour, not vendor causal explanation',
                  'derived endpoint-only availability is not complete intraminute information']}
    save_json(out/'summary.json',summary)
    save_json(out/'run_receipt.json',{'run_id':os.getenv('GITHUB_RUN_ID'), 'workflow_commit':os.getenv('GITHUB_SHA'),
        'base_ref':BASE_REF,'execution_location':'GitHub Actions' if os.getenv('GITHUB_RUN_ID') else 'current caller',
        'script_sha256':sha(__file__), 'protocol_sha256':sha(Path(__file__).with_name('protocol.json')),
        'frozen_code_sha256':sha(v.__file__), 'read_post2025':False,'models_refitted':False,'production_authority':False})
    save_json(out/'output_manifest.json',[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.iterdir()) if p.is_file()])
    print('AUDIT_COMPLETE',json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
