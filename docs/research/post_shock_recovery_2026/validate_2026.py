from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss

SYMBOLS=('000688.SH','000852.SH')
CHECKPOINTS=(5,10,15,20)

def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def jsafe(x):
    if isinstance(x,dict): return {str(k):jsafe(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [jsafe(v) for v in x]
    if isinstance(x,np.generic): return jsafe(x.item())
    if isinstance(x,float) and not np.isfinite(x): return None
    return x

def write_json(p,obj): p.write_text(json.dumps(jsafe(obj),ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def roll_mean(x,n):
    return pd.Series(np.asarray(x,float)).rolling(n,min_periods=n).mean().to_numpy()

def minute_panel(native,symbol):
    required={'symbol','timestamp','trading_day','close','causal_flat_fill','high_frequency_analysis_eligible'}
    if not required<=set(native): raise ValueError(f'{symbol}: missing minute fields {required-set(native)}')
    x=native.copy(); x=x[x.symbol.eq(symbol)].copy()
    x['ts']=pd.to_datetime(x.timestamp.astype(str).str[:19])
    if not (x.ts.dt.strftime('%Y-%m-%d')==x.trading_day.astype(str)).all(): raise ValueError('wall-clock/day mismatch')
    good=x.high_frequency_analysis_eligible.eq(True)&x.causal_flat_fill.eq(False)
    x['px']=pd.to_numeric(x.close,errors='coerce').where(good)
    parts=[]
    for day,g in x.groupby('trading_day',sort=True):
        by=g.set_index('ts').px
        for aft,open_ in enumerate(('09:30:00','13:00:00')):
            grid=pd.date_range(f'{day} {open_}',periods=121,freq='min')[1:]
            p=by.reindex(grid).to_numpy(float)
            r=np.r_[np.nan,np.diff(np.log(p))]*1e4
            parts.append(pd.DataFrame({'session':f'{day}/{aft}','day':str(day),'minute':np.arange(1,121),'afternoon':aft,'return_bp':r,'source_valid':np.isfinite(p)}))
    return pd.concat(parts,ignore_index=True)

def event_enrich(panel):
    q=panel.copy(); q['sigma_pre']=np.nan; q['event']=np.nan; q['first']=np.nan
    for _,ix in q.groupby('session',sort=False).groups.items():
        ix=np.asarray(ix); r=q.loc[ix,'return_bp'].to_numpy(float)
        rv30=roll_mean(r*r,30); sigma=np.sqrt(np.r_[np.nan,rv30[:-1]])
        ev=np.full(len(r),np.nan); finite=np.isfinite(r); ev[finite&(np.abs(r)<=30)]=0
        known=finite&np.isfinite(sigma); ev[known]=((np.abs(r[known])>30)&(np.abs(r[known])>4*np.maximum(sigma[known],1))).astype(float)
        first=np.full(len(r),np.nan)
        for j in range(30,len(r)):
            before=ev[j-30:j]
            if np.isfinite(before).all() and np.isfinite(ev[j]): first[j]=float(ev[j]==1 and not before.any())
        q.loc[ix,'sigma_pre']=sigma; q.loc[ix,'event']=ev; q.loc[ix,'first']=first
    return q

def seconds_sessions(native,symbol):
    required={'symbol','observation_datetime','trading_day','price','row_index'}
    if not required<=set(native): raise ValueError(f'{symbol}: missing 3s fields {required-set(native)}')
    x=native[native.symbol.eq(symbol)].copy()
    ts=pd.to_datetime(x.observation_datetime.astype(str).str[:19])
    x['sec_day']=ts.dt.hour*3600+ts.dt.minute*60+ts.dt.second
    x['afternoon']=(x.sec_day>=13*3600).astype(int)
    x['session']=x.trading_day.astype(str)+'/'+x.afternoon.astype(str)
    x['second']=x.sec_day-np.where(x.afternoon.eq(1),13*3600,9*3600+30*60)
    x['price']=pd.to_numeric(x.price,errors='coerce')
    x['row_index']=pd.to_numeric(x.row_index,errors='raise').astype(np.int64)
    return {s:g.sort_values(['second','row_index'],kind='stable') for s,g in x[x.second.between(0,7200)].groupby('session',sort=False)}

def latest_at(t,second):
    j=np.searchsorted(t,second,side='right')-1
    if j<0 or second-t[j]>3:return None
    return j

def complete_desc(t,p,row,start,end,sigma):
    a=latest_at(t,start); b=latest_at(t,end)
    if a is None or b is None or b<=a:return None
    tt=t[a:b+1]; pp=p[a:b+1]
    dt=np.diff(tt)
    if np.any(dt==0) or np.any(dt>3) or not np.isfinite(pp).all() or np.any(pp<=0):return None
    inc=np.diff(np.log(pp))*1e4; total=float(np.abs(inc).sum())
    signs=np.sign(inc[np.abs(inc)>1e-12]); signchg=float(np.mean(signs[1:]!=signs[:-1])) if len(signs)>1 else 0.0
    return {'rms':float(np.sqrt(np.mean(inc**2))/sigma),'max':float(np.max(np.abs(inc))/sigma),'net':float(np.log(pp[-1]/pp[0])*1e4/sigma),
            'range':float(np.log(pp.max()/pp.min())*1e4/sigma),'eff':float(abs(np.log(pp[-1]/pp[0])*1e4)/total) if total else 0.0,
            'top3':float(np.sort(np.abs(inc))[-3:].sum()/total) if total else 0.0,'signchg':signchg}

def event_path_info(group,minute,sigma):
    if group is None or group.empty:return {}
    t=group.second.to_numpy(float); p=group.price.to_numpy(float); row=group.row_index.to_numpy(np.int64)
    e=minute*60; start=e-60
    lo=max(0,start-300); sel=(t>=lo)&(t<=start)
    pre_range=np.nan; pre_net=np.nan
    if sel.sum()>=2 and np.isfinite(p[sel]).all() and np.all(p[sel]>0):
        pp=p[sel]; pre_range=float(np.log(pp.max()/pp.min())*1e4); pre_net=float(np.log(pp[-1]/pp[0])*1e4)
    ed=complete_desc(t,p,row,start,e,sigma); d2=complete_desc(t,p,row,e,e+120,sigma); d5=complete_desc(t,p,row,e,e+300,sigma)
    out={'pre5m_range_bp':pre_range,'pre5m_net_bp':pre_net,'event_complete':ed is not None,'post2_complete':d2 is not None,'post5_complete':d5 is not None}
    if ed:
        out['event_top3']=ed['top3'];out['event_eff']=ed['eff']
    if d2:
        for k,v in d2.items():out['p2_'+k]=v
    if d5:
        for k,v in d5.items():out['p5_'+k]=v
    return out

def lin_score(row,params,logistic=False):
    fs=params['features']; x=np.asarray([row.get(f,np.nan) for f in fs],float)
    if not np.isfinite(x).all(): return None
    z=(x-np.asarray(params['scaler_mean']))/np.asarray(params['scaler_scale'])
    v=float(params['intercept']+z@np.asarray(params['coef']))
    if logistic:return float(1/(1+np.exp(-np.clip(v,-40,40))))
    return v

def stable_next10(r,j,d,sigma):
    if d is None:return None
    s=j+d+1;e=s+10
    if e>len(r):return None
    x=r[s:e]
    if not np.isfinite(x).all():return None
    return bool(np.sqrt(np.mean(x[:5]**2))/sigma<1 and np.sqrt(np.mean(x[5:]**2))/sigma<1)

def release_rule(r,j,sigma,rule):
    for d in range(5,min(46,len(r)-j)):
        x=r[j+d-4:j+d+1]
        if len(x)<5 or not np.isfinite(x).all():continue
        trail5=np.sqrt(np.mean(x**2))/sigma; max5=np.max(np.abs(x))/sigma; trail2=np.sqrt(np.mean(x[-2:]**2))/sigma
        ok=trail5<1
        if rule in ('R2','R3'):ok &= max5<1.5
        if rule=='R3':ok &= trail2<.8
        if ok:return d
    return None

def km(rows):
    arr=[]
    for r in rows:
        rel=r.get('release_start_lag')
        if rel is not None and np.isfinite(rel):arr.append((float(rel),1))
        else:arr.append((float(max(r.get('max_release_start_observable',0),0)),0))
    if not arr:return {}
    a=pd.DataFrame(arr,columns=['t','e']).sort_values('t');surv=1.;curve=[]
    for t in sorted(a.t.unique()):
        risk=int((a.t>=t).sum());d=int(((a.t==t)&(a.e==1)).sum());c=int(((a.t==t)&(a.e==0)).sum())
        if d:surv*=1-d/risk
        curve.append({'time':float(t),'at_risk':risk,'released':d,'censored':c,'survival':float(surv),'release_cdf':float(1-surv)})
    med=next((z['time'] for z in curve if z['survival']<=.5),None)
    def cdf(t):
        z=[r for r in curve if r['time']<=t];return z[-1]['release_cdf'] if z else 0.
    return {'n':len(a),'censor_share':float(1-a.e.mean()),'km_median_release_start':med,'km_release_by_5':cdf(5),'km_release_by_10':cdf(10),'km_release_by_15':cdf(15),'km_release_by_30':cdf(30),'curve':curve}

def corr(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    return float(np.corrcoef(a,b)[0,1]) if len(a)>2 and np.std(a)>0 and np.std(b)>0 else None

def spearman(a,b): return corr(pd.Series(a).rank().to_numpy(),pd.Series(b).rank().to_numpy())

def model_metrics(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float)
    return {'n':len(y),'rmse_log':float(np.sqrt(np.mean((np.log(y)-np.log(p))**2))),'pearson':corr(np.log(y),np.log(p)),'spearman':spearman(np.log(y),np.log(p))}

def logistic_metrics(y,p):
    y=np.asarray(y,int);p=np.asarray(p,float)
    return {'n':len(y),'base_rate':float(y.mean()) if len(y) else None,'auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
            'brier':float(brier_score_loss(y,p)) if len(y) else None,'max_p':float(p.max()) if len(p) else None,'mean_p':float(p.mean()) if len(p) else None,
            'n_p80':int((p>=.8).sum()),'precision_p80':float(y[p>=.8].mean()) if (p>=.8).any() else None,'n_p90':int((p>=.9).sum()),'precision_p90':float(y[p>=.9].mean()) if (p>=.9).any() else None}

def validate_inputs(root):
    m1=json.loads((root/'data/cross_index_risk_gate_2026_v1/manifest.json').read_text());m3=json.loads((root/'data/cross_index_risk_gate_2026_3s_v1/manifest.json').read_text())
    rows=[];frames={}
    for manifest,freq in ((m1,'1m'),(m3,'3s')):
        for item in manifest['files']:
            path=root/(item.get('repo_path') or item['path'])
            if not path.exists(): raise FileNotFoundError(path)
            h=sha256(path); assert h==item['sha256'],(path,h,item['sha256'])
            df=pd.read_parquet(path)
            assert len(df)==item['rows'] and set(df.symbol)=={item['symbol']}
            assert str(df.trading_day.min())==item['first_day'] and str(df.trading_day.max())==item['last_day']
            frames[(item['symbol'],freq)]=df
            rows.append({'path':str(path.relative_to(root)),'sha256':h,'rows':len(df),'first_day':str(df.trading_day.min()),'last_day':str(df.trading_day.max())})
    return frames,{'files':rows,'minute_manifest_sha256':sha256(root/'data/cross_index_risk_gate_2026_v1/manifest.json'),'seconds_manifest_sha256':sha256(root/'data/cross_index_risk_gate_2026_3s_v1/manifest.json')}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    root=args.root.resolve();out=args.out;out.mkdir(parents=True,exist_ok=True)
    params=json.loads((root/'docs/research/post_shock_recovery_2026/frozen_params.json').read_text())
    frames,receipt=validate_inputs(root);receipt.update({'role':'held_out_2026_validation','no_refit_on_2026':True,'snapshot_end':'2026-08-21'})
    write_json(out/'input_receipt.json',receipt)
    all_events=[]; checkpoints=[]; rules=[]; pathrows=[]; curves=[]; by_symbol={}
    for symbol in SYMBOLS:
        minute=event_enrich(minute_panel(frames[(symbol,'1m')],symbol)); seconds=seconds_sessions(frames[(symbol,'3s')],symbol); s_events=[]
        for session,sub0 in minute.groupby('session',sort=False):
            sub=sub0.sort_values('minute').reset_index(drop=True);r=sub.return_bp.to_numpy(float)
            for j in np.flatnonzero(sub['first'].to_numpy(float)==1):
                m=int(sub.loc[j,'minute']);sigma=float(sub.loc[j,'sigma_pre']);er=float(sub.loc[j,'return_bp'])
                if m<33 or not np.isfinite(sigma) or sigma<=0:continue
                key=f'{symbol}|{session}|{m}'; info=event_path_info(seconds.get(session),m,sigma)
                rec={'key':key,'symbol':symbol,'year':2026,'session':session,'day':sub.loc[j,'day'],'minute':m,'sigma_pre':sigma,'event_return_bp':er,'abs_event_z':abs(er)/sigma,'is_csi1000':float(symbol=='000852.SH'),**info}
                if np.isfinite(rec.get('pre5m_range_bp',np.nan)):
                    if rec['pre5m_range_bp']<30: rec['context_type']='quiet_first'
                    elif abs(rec.get('pre5m_net_bp',np.nan))>=30:rec['context_type']='prior_directional'
                    else:rec['context_type']='prior_roundtrip_or_active'
                else:rec['context_type']='unknown'
                rec['quiet_first']=float(rec['context_type']=='quiet_first') if rec['context_type']!='unknown' else np.nan
                vals={}
                for k in range(46):
                    s=j+k+1;e=s+5
                    if e<=len(r) and np.isfinite(r[s:e]).all():
                        ratio=float(np.sqrt(np.mean(r[s:e]**2))/sigma);vals[k]=ratio
                        curves.append({'key':key,'symbol':symbol,'lag':k,'r5_ratio':ratio,'state':'Unsafe' if ratio>=1.5 else ('Recovering' if ratio>=1 else 'Clean-candidate')})
                release=None
                for k in range(46):
                    a=j+k+1;b=a+5;c=b+5
                    if c>len(r):break
                    if np.isfinite(r[a:b]).all() and np.isfinite(r[b:c]).all() and np.sqrt(np.mean(r[a:b]**2))/sigma<1 and np.sqrt(np.mean(r[b:c]**2))/sigma<1:
                        release=k;break
                rec['release_start_lag']=release;rec['release_confirm_minutes']=None if release is None else release+10;rec['right_censored']=release is None;rec['max_release_start_observable']=max(-1,len(r)-j-11)
                for k in [0,5,10,15,30]:rec[f'r5_lag{k}']=vals.get(k)
                all_events.append(rec);s_events.append(rec)
                for rule in ['R1','R2','R3']:
                    d=release_rule(r,j,sigma,rule);stable=stable_next10(r,j,d,sigma)
                    rules.append({'key':key,'symbol':symbol,'rule':rule,'trigger':d is not None,'trigger_minute':d,'future_stable':stable,'outcome_censored':d is not None and stable is None})
                for d in [10,15,20,30]:
                    stable=stable_next10(r,j,d,sigma);rules.append({'key':key,'symbol':symbol,'rule':f'FIXED_{d}','trigger':True,'trigger_minute':d,'future_stable':stable,'outcome_censored':stable is None})
                for d in CHECKPOINTS:
                    if j+d>=len(r):continue
                    x5=r[j+d-4:j+d+1];x2=r[j+d-1:j+d+1]
                    if len(x5)<5 or not np.isfinite(x5).all() or not np.isfinite(x2).all():continue
                    ns=j+d+1;ne=ns+5
                    if ne>len(r) or not np.isfinite(r[ns:ne]).all():continue
                    row={**rec,'checkpoint':d,'trail5':float(np.sqrt(np.mean(x5**2))/sigma),'max5':float(np.max(np.abs(x5))/sigma),'trail2':float(np.sqrt(np.mean(x2**2))/sigma),'next5_ratio':float(np.sqrt(np.mean(r[ns:ne]**2))/sigma)}
                    row['stable_next10']=stable_next10(r,j,d,sigma)
                    if all(np.isfinite(row.get(k,np.nan)) for k in ['event_top3','event_eff','quiet_first']):
                        row['top3_share']=row['event_top3'];row['path_efficiency']=row['event_eff'];row['log_sigma_pre']=float(np.log(sigma))
                        row['release_model_p']=lin_score(row,params['release_logistic'],True)
                        plog=lin_score(row,params['recovery_ridge'],False);row['ridge_pred_ratio']=None if plog is None else float(np.exp(plog))
                    checkpoints.append(row)
                stable5=stable_next10(r,j,5,sigma)
                if stable5 is not None and all(np.isfinite(rec.get(k,np.nan)) for k in ['event_top3','event_eff','quiet_first']):
                    row={'key':key,'symbol':symbol,'stable_next10':stable5,'abs_event_z':rec['abs_event_z'],'log_sigma_pre':float(np.log(sigma)),'quiet_first':rec['quiet_first'],'is_csi1000':rec['is_csi1000'],'event_top3':rec['event_top3'],'event_eff':rec['event_eff']}
                    for prefix in ['p2','p5']:
                        for k in ['rms','max','net','range','eff','top3','signchg']:row[f'{prefix}_{k}']=rec.get(f'{prefix}_{k}')
                    for name,p0 in params['path_logistics'].items():row[name+'_p']=lin_score(row,p0,True)
                    pathrows.append(row)
        by_symbol[symbol]={'n_events':len(s_events),'km':km(s_events),'quiet_km':km([x for x in s_events if x.get('context_type')=='quiet_first'])}
    E=pd.DataFrame(all_events);C=pd.DataFrame(checkpoints);R=pd.DataFrame(rules);P=pd.DataFrame(pathrows);CV=pd.DataFrame(curves)
    E.to_csv(out/'events_2026.csv',index=False);C.to_csv(out/'checkpoints_2026.csv',index=False);R.to_csv(out/'release_rules_2026.csv',index=False);P.to_csv(out/'path_model_2026.csv',index=False);CV.to_csv(out/'decay_2026.csv',index=False)
    score={}
    for symbol in SYMBOLS:
        z=C[C.symbol==symbol].copy(); known=z[np.isfinite(z.next5_ratio)&(z.next5_ratio>0)]
        score[symbol]={'persistence':model_metrics(known.next5_ratio,known.trail5) if len(known) else {},'ridge_fixed':{},'release_fixed':{}}
        if 'ridge_pred_ratio' in known:
            zr=known[np.isfinite(known.ridge_pred_ratio)]
            if len(zr):score[symbol]['ridge_fixed']=model_metrics(zr.next5_ratio,zr.ridge_pred_ratio)
        if 'release_model_p' in z:
            zl=z[z.stable_next10.notna()&z.release_model_p.notna()]
            if len(zl):score[symbol]['release_fixed']=logistic_metrics(zl.stable_next10.astype(int),zl.release_model_p)
    known=C[np.isfinite(C.next5_ratio)&(C.next5_ratio>0)]
    score['pooled']={'persistence':model_metrics(known.next5_ratio,known.trail5) if len(known) else {}}
    if 'ridge_pred_ratio' in known:
        zr=known[np.isfinite(known.ridge_pred_ratio)]
        if len(zr):score['pooled']['ridge_fixed']=model_metrics(zr.next5_ratio,zr.ridge_pred_ratio)
    if 'release_model_p' in C:
        zl=C[C.stable_next10.notna()&C.release_model_p.notna()]
        if len(zl):score['pooled']['release_fixed']=logistic_metrics(zl.stable_next10.astype(int),zl.release_model_p)
    rule_summary={}
    for rule,g in R.groupby('rule'):
        rule_summary[rule]={}
        for symbol,z in g.groupby('symbol'):
            trig=z.trigger.fillna(False);e=z[trig&~z.outcome_censored]
            rule_summary[rule][symbol]={'events':int(z.key.nunique()),'trigger_n':int(trig.sum()),'evaluable_n':len(e),'stable_precision':float(e.future_stable.astype(bool).mean()) if len(e) else None,'false_release_share':float((~e.future_stable.astype(bool)).mean()) if len(e) else None,'median_trigger':float(z.loc[trig,'trigger_minute'].median()) if trig.any() else None}
    path_summary={}
    for symbol in SYMBOLS:
        z=P[P.symbol==symbol].dropna(subset=['E0_p','E2_p','E5_p']) if len(P) else pd.DataFrame();path_summary[symbol]={'n':len(z)}
        if len(z):
            for m in ['E0','E2','E5']:path_summary[symbol][m]=logistic_metrics(z.stable_next10.astype(int),z[m+'_p'])
    z=P.dropna(subset=['E0_p','E2_p','E5_p']) if len(P) else pd.DataFrame();path_summary['pooled']={'n':len(z)}
    if len(z):
        for m in ['E0','E2','E5']:path_summary['pooled'][m]=logistic_metrics(z.stable_next10.astype(int),z[m+'_p'])
    decay={}
    for symbol in SYMBOLS:
        decay[symbol]={}
        for lag in [0,5,10,15,30]:
            z=CV[(CV.symbol==symbol)&(CV.lag==lag)];decay[symbol][str(lag)]={'n':len(z),'unsafe_share':float((z.r5_ratio>=1.5).mean()) if len(z) else None,'median_r5':float(z.r5_ratio.median()) if len(z) else None}
    summary={'snapshot':'2026-01-05..2026-08-21','events':by_symbol,'decay':decay,'recovery_scores':score,'release_rules':rule_summary,'path_models':path_summary,'interpretation_guardrails':['2026 held-out validation; no refit/tuning','Clean remains unvalidated unless frozen release rules meet high-confidence criteria','all 2026 support partial through 2026-08-21']}
    write_json(out/'summary_2026.json',summary)
    print('SUMMARY_2026 '+json.dumps(jsafe(summary),ensure_ascii=False))

if __name__=='__main__':main()
