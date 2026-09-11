"""D3 fixed information probes. No changes to the V19 signal or recovery table."""
from __future__ import annotations
import argparse, gzip, hashlib, io, json, platform, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

D2_SHA='cf1c89e1412fd70f27992d9077af10dd7887a6843072e03ef808902bf5a84096'
D2_INPUT_SHA='aa31cf36b09a4708be98c6867ee1db81063855d0fa87885ec52685c3e5fdd2c3'
HORIZONS=(15,30,60)
SYMBOLS=('000688.SH','000852.SH')
STATES=('NORMAL','UNSAFE','RECOVERING')
SLOTS=tuple(list(range(575,691,5))+list(range(785,901,5)))
LAMBDA=.01
SEED=20260912
BOOTSTRAPS=5000
FAMILY=12

def digest(b): return hashlib.sha256(b).hexdigest()
def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def read_gz(z,name): return pd.read_csv(z.open(name),compression='gzip',float_precision='round_trip')

def load_inputs(transport,ledger):
    assert digest(ledger.read_bytes())==D2_SHA,'D2 ZIP drift'
    with zipfile.ZipFile(ledger) as z:
        assert digest(z.read('input_manifest.json'))==D2_INPUT_SHA
        manifest=json.loads(z.read('output_manifest.json'))
        verified=0
        for ent in manifest['files']:
            key=ent.get('path',ent.get('name'))
            assert digest(z.read(key))==ent['sha256'],key
            verified+=1
        records=[]
        with gzip.open(z.open('causal_event_ledger.jsonl.gz'),'rt') as f:
            for line in f:
                r=json.loads(line)
                assert not r['production_authority']
                assert r['frozen_v19_blob']=='ee2fce299d5ee21abf1ab2c2c5183bac101ae822'
                records.append(r)
    assert len(records)==232704
    events=pd.DataFrame(records)
    for c in ['bar_end','decision_time','published_at','valid_until','observation_time']:
        events[c]=pd.to_datetime(events[c],format='ISO8601',utc=True).dt.tz_convert('Asia/Shanghai').dt.tz_localize(None)
    assert not events.event_id.duplicated().any()
    assert set(events.symbol)==set(SYMBOLS)
    assert events.bar_end.dt.year.between(2021,2025).all()
    receipt=json.loads(zipfile.ZipFile(transport).read('TRANSPORT_RECEIPT.json'))
    parts=[]
    with zipfile.ZipFile(transport) as z:
        assert receipt['d2_zip_sha256']==D2_SHA
        assert receipt['statistical_analysis_performed'] is False
        assert len(receipt['exports'])==12
        for r in receipt['exports']:
            assert r['price_roundtrip_exact']
            assert digest(z.read(r['csv_file']))==r['csv_gzip_sha256']
            a=read_gz(z,r['csv_file'])
            assert len(a)==r['rows']
            parts.append(a)
    prices=pd.concat(parts,ignore_index=True)
    prices['bar_end']=pd.to_datetime(prices.bar_end)
    assert prices.bar_end.dt.year.between(2020,2025).all()
    assert np.isfinite(prices.close).all() and (prices.close>0).all()
    assert not prices.duplicated(['symbol','bar_end']).any()
    assert prices.groupby(['symbol','trading_day']).size().eq(48).all()
    return prices,events,{'transport_sha256':digest(transport.read_bytes()),'d2_zip_sha256':D2_SHA,'d2_output_files_verified':verified,'ledger_rows':len(events),'source_files':receipt['exports']}

def history(prices):
    """Every feature at row j uses confirmed closes strictly before j."""
    p=prices.sort_values(['symbol','bar_end']).reset_index(drop=True).copy()
    p['r']=p.groupby(['symbol','trading_day'],sort=False).close.transform(lambda s: np.log(s).diff())
    for name in ['bg48','last_abs']+[f'rms{k}' for k in (3,6,12,48)]: p[name]=np.nan
    for _,g in p.groupby('symbol',sort=False):
        v=g.r.dropna()
        p.loc[v.index,'bg48']=v.shift(1).rolling(48,min_periods=48).std(ddof=0)
        p.loc[v.index,'last_abs']=v.shift(1).abs()
        for k in (3,6,12,48): p.loc[v.index,f'rms{k}']=np.sqrt(v.pow(2).shift(1).rolling(k,min_periods=k).mean())
    p['year']=p.bar_end.dt.year
    p['slot']=p.bar_end.dt.hour*60+p.bar_end.dt.minute
    p['session']=(p.slot>=780).astype(int)
    p['own_tail']=(p.r.abs()>=3*p.bg48)&(p.groupby('symbol').bar_end.diff()==pd.Timedelta(minutes=5))
    p['price_idx']=np.arange(len(p))
    return p

def causal_table(p,events,years):
    e=events[(events.event_type=='E15')&events.bar_end.dt.year.isin(years)].copy()
    assert not any(c in e.columns for c in ['final_state','future_return','episode_end'])
    q=e.merge(p,on=['symbol','bar_end'],validate='one_to_one')
    assert len(q)==len(e)
    q['role']=np.where(q.year<=2023,'development','validation')
    q['freshness']=np.where((q.decision_time-q.observation_time).dt.total_seconds()<=15,'LE15s','GT15s')
    timely=(q.published_at<=q.decision_time)&(q.decision_time<q.valid_until)&(q.observation_time<=q.decision_time)
    q['available']=q.state.isin(STATES)&q.availability_reason.eq('AVAILABLE')&timely
    q['available'] &= q[['bg48','last_abs','rms3','rms6','rms12','rms48','vol_ratio','shock_intensity']].notna().all(axis=1)&q.bg48.gt(0)
    assert ((q.bar_end-q.decision_time)==pd.Timedelta(seconds=15)).all()
    return q

def labels(p,q,h,close_events):
    """Evaluation side only; current return is not a future return."""
    n=h//5
    idx=q.price_idx.to_numpy(int)
    future=idx[:,None]+np.arange(1,n+1)
    within=future[:,-1]<len(p)
    clipped=np.minimum(future,len(p)-1)
    times=p.bar_end.to_numpy()[clipped]
    expected=q.bar_end.to_numpy()[:,None]+np.arange(1,n+1)*np.timedelta64(5,'m')
    ok=within&np.all(times==expected,axis=1)
    ok &= np.all(p.symbol.to_numpy()[clipped]==q.symbol.to_numpy()[:,None],axis=1)
    ok &= np.all(p.trading_day.to_numpy()[clipped]==q.trading_day.to_numpy()[:,None],axis=1)
    ok &= np.all(p.session.to_numpy()[clipped]==q.session.to_numpy()[:,None],axis=1)
    returns=p.r.to_numpy()[clipped]
    ok &= np.isfinite(returns).all(axis=1)
    out=q.copy()
    out['label_ok']=ok
    out['sigma']=np.where(ok,np.sqrt(np.mean(returns**2,axis=1)),np.nan)
    out['log_future_sigma']=np.log(np.maximum(out.sigma,1e-12))
    out['future_tail']=np.where(ok,np.max(np.abs(returns),axis=1)>=3*q.bg48.to_numpy(),np.nan)
    out['label_start']=out.bar_end
    out['label_end']=out.bar_end+pd.Timedelta(minutes=h)
    assert (out.label_start>out.decision_time).all()
    close=close_events.set_index(['symbol','bar_end']).state
    state=p.set_index(['symbol','bar_end']).index.map(close).to_numpy()[clipped]
    out['future_risk_fraction']=np.where(ok,np.isin(state,['UNSAFE','RECOVERING']).mean(axis=1),np.nan)
    out['future_any_normal']=np.where(ok,np.any(state=='NORMAL',axis=1),np.nan)
    return out

def design(q,model):
    """Explicit whitelist: final close/r/labels are never read here."""
    values={}
    def oh(prefix,v,levels):
        for level in levels: values[f'{prefix}:{level}']=(np.asarray(v)==level).astype(float)
    oh('symbol',q.symbol,SYMBOLS); oh('slot',q.slot,SLOTS); oh('previous',q.previous_confirmed_state,STATES)
    age=q.recent_shock_age_bars.fillna(-1).to_numpy()
    bucket=np.select([age<0,age<=2,age<=5,age<=8],['NONE','LT15','M15_25','M30_40'],default='GE45')
    oh('age',bucket,('NONE','LT15','M15_25','M30_40','GE45'))
    if model!='B0':
        for k in (3,6,12,48): values[f'log_rms{k}']=np.log(np.maximum(q[f'rms{k}'].to_numpy(),1e-12))
        values['log_bg']=np.log(q.bg48.to_numpy())
        values['log_previous_abs_z']=np.log1p(q.last_abs.to_numpy()/q.bg48.to_numpy())
    if model in ('B3','B4'):
        a=np.log1p(q.shock_intensity.to_numpy()); b=np.log(np.maximum(q.vol_ratio.to_numpy(),1e-12))
        for name,v in zip(('intensity','ratio','intensity2','ratio2','cross'),(a,b,a*a,b*b,a*b)):
            values[name]=v
            for state in STATES: values[name+':'+state]=v*q.previous_confirmed_state.eq(state).to_numpy()
    if model in ('B2','B4'):
        oh('state',q.state,STATES)
        for prev in STATES:
            for state in STATES: values[f'pair:{prev}:{state}']=(q.previous_confirmed_state.eq(prev)&q.state.eq(state)).to_numpy(float)
        values['exit_pending']=q.exit_pending.to_numpy(float)
        values['recovery_available']=q.recovery_probabilities.notna().to_numpy(float)
        for h in HORIZONS:
            values[f'frozen_p{h}']=q.recovery_probabilities.map(lambda x: float(x[HORIZONS.index(h)]) if isinstance(x,(list,tuple)) and len(x)==3 else (float(x.get(str(h),np.nan)) if isinstance(x,dict) else 0.)).to_numpy(float)
    x=np.column_stack(list(values.values())).astype(float)
    if not np.isfinite(x).all(): raise ValueError('nonfinite feature or unrecognized frozen-probability schema')
    return x,list(values)

def fit_probe(x,y,names):
    mean=x.mean(axis=0); scale=x.std(axis=0); scale[scale<1e-14]=1.
    z=(x-mean)/scale; intercept=float(np.mean(y))
    beta=np.linalg.solve(z.T@z/len(z)+LAMBDA*np.eye(z.shape[1]),z.T@(y-intercept)/len(z))
    return {'names':names,'mean':mean.tolist(),'scale':scale.tolist(),'beta':beta.tolist(),'intercept':intercept,'n':len(y)}

def predict(q,model,probe,endpoint):
    x,names=design(q,model); assert names==probe['names']
    v=((x-np.array(probe['mean']))/np.array(probe['scale']))@np.array(probe['beta'])+probe['intercept']
    return np.clip(v,0,1) if endpoint=='future_tail' else v

def block_stats(q,improvement,block_days):
    d=pd.DataFrame({'day':q.trading_day.to_numpy(),'year':q.year.to_numpy(),'gain':improvement,'n':1})
    days=d[['year','day']].drop_duplicates().sort_values(['year','day'])
    days['block']=days.groupby('year').cumcount()//block_days
    d=d.merge(days,on=['year','day'],validate='many_to_one')
    return d.groupby(['year','block'],as_index=False)[['gain','n']].sum()

def uncertainty(blocks):
    rng=np.random.default_rng(SEED); gains=np.zeros(BOOTSTRAPS); count=np.zeros(BOOTSTRAPS)
    for _,g in blocks.groupby('year',sort=True):
        idx=rng.integers(0,len(g),size=(BOOTSTRAPS,len(g)))
        gains+=g.gain.to_numpy()[idx].sum(axis=1); count+=g.n.to_numpy()[idx].sum(axis=1)
    samples=gains/count; a=.05/(2*FAMILY)
    lo,hi=np.quantile(samples,[a,1-a])
    return {'mean_gain':float(blocks.gain.sum()/blocks.n.sum()),'adjusted_low':float(lo),'adjusted_high':float(hi),'bootstrap_repetitions':BOOTSTRAPS,'block_count':len(blocks)}

def compare(q,endpoint,base,enhanced,probes,h,dev_n,coverage,out):
    y=q[endpoint].to_numpy(float)
    l0=(y-predict(q,base,probes[f'{h}|{endpoint}|{base}'],endpoint))**2
    l1=(y-predict(q,enhanced,probes[f'{h}|{endpoint}|{enhanced}'],endpoint))**2
    gain=l0-l1; rel=float(gain.mean()/l0.mean())
    slices={}
    for col in ('year','symbol'):
        for k,inds in q.groupby(col,sort=True).indices.items():
            slices[f'{col}:{k}']={'n':len(inds),'mean_gain':float(gain[inds].mean()),'relative_gain':float(gain[inds].mean()/l0[inds].mean())}
    blocks=block_stats(q,gain,5); ci=uncertainty(blocks)
    blocks.to_csv(out/f'blocks_{h}_{endpoint}_{enhanced}_vs_{base}.csv',index=False)
    ci20=uncertainty(block_stats(q,gain,20))
    gates={'sample_size':len(q)>=10000 and dev_n>=20000 and all(v['n']>=1000 for v in slices.values()),
           'positive_events':endpoint!='future_tail' or int(y.sum())>=100,
           'practical_relative':rel>=.01,'practical_absolute':endpoint!='future_tail' or float(gain.mean())>=.0005,
           'adjusted_ci_positive':ci['adjusted_low']>0,'annual_and_symbol_signs':all(v['mean_gain']>=0 for v in slices.values()),
           'coverage':coverage>=.95}
    return {'horizon_minutes':h,'endpoint':endpoint,'comparison':enhanced+'_vs_'+base,'n':len(q),
            'development_n':dev_n,'positive_events':int(y.sum()) if endpoint=='future_tail' else None,
            'baseline_loss':float(l0.mean()),'enhanced_loss':float(l1.mean()),'absolute_gain':float(gain.mean()),'relative_gain':rel,
            'ci_5day':ci,'ci_20day_sensitivity':ci20,'slices':slices,'gates':gates,'supported':all(gates.values())}

def describe(q,p,h):
    tables={}
    for col in ('state','transition','freshness','symbol','year','exit_pending'):
        rows=[]
        for key,g in q.groupby(col,sort=True):
            rows.append({'bucket':str(key),'n':len(g),'occupancy':len(g)/len(q),'sigma_mean':float(g.sigma.mean()),
                         'sigma_median':float(g.sigma.median()),'tail_rate':float(g.future_tail.mean()),
                         'future_risk_fraction':float(g.future_risk_fraction.mean()),
                         'future_any_normal':float(g.future_any_normal.mean()) if col=='state' and key!='NORMAL' else None})
        tables[col]=rows
    n=h//5; fut=q.price_idx.to_numpy(int)[:,None]+np.arange(1,n+1)
    target=p.own_tail.to_numpy()[fut]
    risk=q.state.isin(['UNSAFE','RECOVERING']).to_numpy()
    eligible=np.unique(fut[target]); captured=np.unique(fut[target&risk[:,None]])
    # Row precision and unique-event recall use explicitly different denominators/normalizations.
    tables['event_dedup']={'eligible_unique_finalized_shocks':len(eligible),'captured_unique_shocks':len(captured),
                           'capture_rate':len(captured)/len(eligible) if len(eligible) else None,'missed_unique_shocks':len(eligible)-len(captured),
                           'risk_row_occupancy':float(risk.mean()),'risk_window_no_tail_rate':float(q.loc[risk,'future_tail'].eq(0).mean()) if risk.any() else None,
                           'normal_window_tail_rate':float(q.loc[~risk,'future_tail'].mean()) if (~risk).any() else None}
    return tables

def execute(args):
    out=args.out; out.mkdir(parents=True,exist_ok=True)
    p0,events,identity=load_inputs(args.transport,args.ledger)
    p=history(p0)
    close=events[events.event_type=='CLOSE']
    protocol=Path(__file__).with_name('PROTOCOL.md')
    identity.update({'protocol_sha256':digest(protocol.read_bytes()),'runner_sha256':digest(Path(__file__).read_bytes()),
                     'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__})
    dump(out/'INPUT_IDENTITY.json',identity)
    if args.phase=='fit':
        assert not (out/'FROZEN_PROBES.json').exists(),'refuse overwrite of frozen probes'
        q=causal_table(p,events,(2021,2022,2023)); probes={}; summaries={}; coverage={}
        for h in HORIZONS:
            all_rows=labels(p,q,h,close); z=all_rows[all_rows.label_ok&all_rows.available].copy().reset_index(drop=True)
            assert z.year.between(2021,2023).all()
            coverage[str(h)]={'grid':len(all_rows),'time_feasible':int(all_rows.label_ok.sum()),'eligible':len(z),'coverage':len(z)/int(all_rows.label_ok.sum())}
            for endpoint in ('log_future_sigma','future_tail'):
                for model in ('B0','B1','B2','B3','B4'):
                    x,names=design(z,model); key=f'{h}|{endpoint}|{model}'
                    probes[key]=fit_probe(x,z[endpoint].to_numpy(float),names)
            summaries[str(h)]=describe(z,p,h)
        dump(out/'FROZEN_PROBES.json',{'schema':'d3_fixed_ridge_probes_v1','identity':identity,'penalty':LAMBDA,'probes':probes,'development_coverage':coverage})
        dump(out/'DEVELOPMENT_DESCRIPTIVE.json',summaries)
        dump(out/'FIT_RECEIPT.json',{'phase':'fit','training_years':[2021,2022,2023],'validation_scored':False,'model_sha256':digest((out/'FROZEN_PROBES.json').read_bytes()),'model_count':len(probes)})
        print('FIT_COMPLETE',json.dumps(coverage),'model_sha256',digest((out/'FROZEN_PROBES.json').read_bytes()),flush=True)
        return
    before=digest((out/'FROZEN_PROBES.json').read_bytes()); frozen=json.loads((out/'FROZEN_PROBES.json').read_text())
    assert frozen['identity']==identity,'code/protocol/source changed after probe freeze'
    assert before==json.loads((out/'FIT_RECEIPT.json').read_text())['model_sha256']
    q=causal_table(p,events,(2024,2025)); probes=frozen['probes']; comparisons=[]; coverage={}; descriptive={}; losses={}
    for h in HORIZONS:
        all_rows=labels(p,q,h,close); z=all_rows[all_rows.label_ok&all_rows.available].copy().reset_index(drop=True)
        count=int(all_rows.label_ok.sum()); coverage[str(h)]={'grid':len(all_rows),'time_feasible':count,'eligible':len(z),'coverage':len(z)/count,
                'future_window_unavailable':int((~all_rows.label_ok).sum()),'state_or_history_unavailable_with_window':int((all_rows.label_ok&~all_rows.available).sum()),
                'stale_over15s_eligible':int(z.freshness.eq('GT15s').sum())}
        evidence=z[['symbol','trading_day','bar_end','decision_time','state','transition','freshness','exit_pending','log_future_sigma','future_tail']].copy()
        for endpoint in ('log_future_sigma','future_tail'):
            for model in ('B0','B1','B2','B3','B4'):
                pred=predict(z,model,probes[f'{h}|{endpoint}|{model}'],endpoint)
                evidence[endpoint+'_'+model]=pred
                losses[f'{h}|{endpoint}|{model}']=float(np.mean((z[endpoint].to_numpy()-pred)**2))
            for base,enh in (('B1','B2'),('B3','B4')):
                comparisons.append(compare(z,endpoint,base,enh,probes,h,frozen['development_coverage'][str(h)]['eligible'],len(z)/count,out))
        evidence.to_csv(out/f'validation_predictions_{h}m.csv.gz',index=False,compression={'method':'gzip','mtime':0},float_format='%.17g')
        descriptive[str(h)]=describe(z,p,h)
    main=[r for r in comparisons if r['comparison']=='B2_vs_B1']; strong=[r for r in comparisons if r['comparison']=='B4_vs_B3']
    decision='D3_INCREMENTAL_UTILITY_SUPPORTED' if any(r['supported'] for r in main) else 'D3_INCREMENTAL_UTILITY_NOT_SUPPORTED'
    assert before==digest((out/'FROZEN_PROBES.json').read_bytes())
    result={'schema':'d3_utility_result_v1','decision':decision,'comparisons':comparisons,'coverage':coverage,'all_probe_losses':losses,
            'main_supported':[f"{r['endpoint']}|{r['horizon_minutes']}" for r in main if r['supported']],
            'strong_baseline_supported':[f"{r['endpoint']}|{r['horizon_minutes']}" for r in strong if r['supported']],
            'model_sha256_before_after':before,'fresh_oos':False,'v19_modified':False,'v20_started':False,'queried_2026':False,
            'blackbox_queried':False,'pnl_computed':False,'production_authority':False,'execution_location':'current_chat_container'}
    dump(out/'SUMMARY.json',result); dump(out/'VALIDATION_DESCRIPTIVE.json',descriptive)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--phase',choices=['fit','evaluate'],required=True)
    parser.add_argument('--transport',type=Path,required=True); parser.add_argument('--ledger',type=Path,required=True); parser.add_argument('--out',type=Path,required=True)
    execute(parser.parse_args())
