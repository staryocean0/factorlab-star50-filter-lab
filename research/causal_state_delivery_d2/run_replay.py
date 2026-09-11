"""Bounded raw replay versus sealed upstream records; engineer, do not refit."""
from __future__ import annotations
import argparse, copy, gzip, hashlib, importlib.util, json, os, platform, subprocess, sys, zipfile
from bisect import bisect_right
from collections import Counter
from datetime import timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from engine import Kernel, Ledger, TZ, V9, V19, V16, bucket, canonical

HERE=Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def materialize(root,contract,out):
    subprocess.run(['git','fetch','--filter=blob:none','--no-tags','--depth=1','origin',contract['source_commit']],check=True)
    manifest={'schema':'d2_actual_input_manifest_v1','source_commit':contract['source_commit'],'files':[]}
    for label in ('frozen_v9','frozen_v19','frozen_surface'):
        item=contract[label]
        subprocess.run(['git','fetch','--filter=blob:none','--no-tags','--depth=1','origin',item['commit']],check=True)
        b=subprocess.check_output(['git','show',item['commit']+':'+item['path']])
        assert blob(b)==item['blob'],label
        p=HERE/(label+('.json' if label=='frozen_surface' else '.py'));p.write_bytes(b)
        manifest['files'].append({'path':str(p.relative_to(root)),'git_blob':blob(b),'sha256':sha(b),'bytes':len(b)})
    expected=[]
    for sym in contract['symbols']:
        expected += [f'data/market/5m/{sym}/{y}.parquet' for y in range(2020,2026)]
        expected += [f'data/cross_index_risk_gate_3s_v1/{sym}_{y}.parquet' for y in range(2021,2026)]
    got=sorted(str(p.relative_to(root)) for p in (root/'data').rglob('*.parquet'))
    assert got==sorted(expected),('physical input boundary',got)
    for name in expected:
        b=(root/name).read_bytes()
        wanted=subprocess.check_output(['git','rev-parse',contract['source_commit']+':'+name],text=True).strip()
        assert blob(b)==wanted,name
        manifest['files'].append({'path':name,'git_blob':wanted,'sha256':sha(b),'bytes':len(b)})
    # Sealed artifacts are obtained directly; never trigger their workflows.
    import urllib.request, urllib.error
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    opener=urllib.request.build_opener(NoRedirect)
    for a in contract['artifacts']:
        req=urllib.request.Request(f"https://api.github.com/repos/staryocean0/factorlab-star50-filter-lab/actions/artifacts/{a['id']}/zip",
                                   headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'})
        try:
            with opener.open(req,timeout=90) as r:b=r.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (301,302,303,307,308):raise
            location=exc.headers['Location']
            if not location.startswith('https://'):raise RuntimeError('non-HTTPS artifact redirect')
            # Deliberately do not forward the GitHub credential to blob storage.
            with urllib.request.urlopen(location,timeout=90) as r:b=r.read()
        assert sha(b)==a['sha256'],('ZIP identity',a['role'])
        zp=out/(a['role']+'.zip');zp.write_bytes(b);d=out/a['role'];d.mkdir(exist_ok=True)
        with zipfile.ZipFile(zp) as z:
            assert all('/' not in n and '..' not in n for n in z.namelist()),'unexpected artifact members'
            z.extractall(d)
        mf=json.loads((d/'output_manifest.json').read_text())
        for f in mf['files']:
            fb=(d/f['name']).read_bytes();assert sha(fb)==f['sha256'] and len(fb)==f['bytes']
        manifest['files'].append({'artifact_id':a['id'],'role':a['role'],'zip_sha256':sha(b),'manifest':mf})
    (out/'input_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

def dt(x):return pd.Timestamp(x).to_pydatetime().replace(tzinfo=TZ)
def age_or_none(x):return None if pd.isna(x) else int(x)
def key(sym,end):return (sym,end.replace(tzinfo=None).isoformat())
def choose(times,prices,start,target):
    p=bisect_right(times,target)-1
    if p<0 or times[p]<start:return None,None
    return float(prices[p]),pd.Timestamp(int(times[p])).to_pydatetime().replace(tzinfo=TZ)
def ns(t):return int(np.datetime64(t.replace(tzinfo=None),'ns').astype('int64'))

def run(root,out):
    contract=json.loads((HERE/'FROZEN_INPUTS.json').read_text());out.mkdir(parents=True,exist_ok=True)
    manifest=materialize(root,contract,out)
    v9=module(HERE/'frozen_v9.py','d2_frozen_v9');v19=module(HERE/'frozen_v19.py','d2_frozen_v19')
    assert (v9.RV_WINDOW,v9.BG_WINDOW,v9.HIGHVOL_RATIO,v9.RECOVERY_NORMAL_RATIO,v9.SHOCK_SIGMA)==(12,48,1.5,1.1,3.0)
    v9.REF_YEARS=tuple(range(2020,2026))
    surf=json.loads((HERE/'frozen_surface.json').read_text())
    surface={(r['current_state'],r['age_bucket']):tuple(r[f'p_{h}m'] for h in (15,30,60)) for r in surf['adaptive_surface']}
    anchor={r['age_bucket']:r['p_60m'] for r in surf['age_only_comparator']}
    assert len(surface)==8
    for (_,b),p in surface.items():assert 0<=p[0]<=p[1]<=p[2]<=1 and p[2]==anchor[b]
    expected={};roles={};source_rows={}
    for a in contract['artifacts']:
        x=pd.read_parquet(out/a['role']/'checkpoint_detail.parquet');assert len(x)==a['rows']
        assert x.year.isin([2021,2022,2023] if a['role']=='development' else [2024,2025]).all()
        source_rows[a['role']]=len(x)
        for r in x.itertuples(index=False):
            kk=key(r.symbol,dt(r.bar_end));assert kk not in expected;expected[kk]=r;roles[kk]=a['role']
    events=[];mismatches=[];stats=Counter();reasons=Counter();transitions=Counter();by_group={};seen=set();prefix_checks=[]
    max_ratio_diff=0.;max_intensity_diff=0.;max_probability_diff=0.
    def bad(kind,ident,got,want):mismatches.append({'kind':kind,'key':str(ident),'got':str(got),'expected':str(want)})
    for sym in contract['symbols']:
        # Frozen evaluator is kept outside the chronological input record.
        reference=v9.load_reference(root,sym)
        bars=reference[['trading_day','bar_end','close','year']].copy()
        assert bars.bar_end.dt.year.le(2025).all()
        k=Kernel(sym,surface);quotes={};firstlast={}
        for year in contract['score_years']:
            sec=v9.load_3s(root,sym,year);assert pd.to_datetime(sec.trading_day).dt.year.eq(year).all()
            stats['raw_3s_rows']+=len(sec);stats['same_timestamp_rows']=stats.get('same_timestamp_rows',0)+int(sec.obs_dt.duplicated(keep=False).sum())
            days=sorted(bars.loc[bars.year.eq(year),'trading_day'].unique());firstlast[year]={days[0],days[-1]}
            for day,g in sec.groupby('trading_day',sort=False):
                quotes[str(day)]=(g.obs_dt.to_numpy(dtype='datetime64[ns]').view('int64'),g.price.to_numpy(float))
        for rr in bars.itertuples():
            end=dt(rr.bar_end);year=int(rr.year);scored=year>=2021
            if scored:
                times,prices=quotes.get(str(rr.trading_day),(np.array([],dtype='int64'),np.array([])))
                target=end-timedelta(seconds=15);start=end-timedelta(minutes=5)
                price,obs=choose(times,prices,ns(start),ns(target))
                context=copy.deepcopy(k) if str(rr.trading_day) in firstlast[year] and (end.hour,end.minute)==(10,0) else None
                e=k.e15(bar_end=end,price=price,observation_time=obs)
                events.append(e);stats['e15_grid_rows']+=1;reasons['E15|'+e.availability_reason]+=1
                group=f'{sym}|{year}';gg=by_group.setdefault(group,Counter());gg['grid']+=1
                transitions['E15|'+e.transition]+=1
                if e.state is not None:stats['e15_available']+=1;gg['available']+=1
                if e.recovery_probabilities is not None:stats['e15_probability_rows']+=1;gg['probability_rows']+=1
                reasons['E15_PROB|'+e.recovery_reason]+=1
                if e.state in ('UNSAFE','RECOVERING'):stats['e15_risk_rows']+=1
                kk=key(sym,end);r=expected.get(kk)
                if r is not None:
                    seen.add(kk);checks={'partial_state':(e.partial_state,r.partial_state),'machine_state':(e.state,r.machine_state),
                         'partial_shock':(e.shock,bool(r.partial_shock)),'observation':(e.observation_time,dt(r.selected_observation_time)),
                         'age':(e.recent_shock_age_bars,age_or_none(r.prior_final_shock_age_bars)),
                         'probability_reason':(e.recovery_reason,r.probability_reason),
                         'frozen_mapping':(e.state,v19.machine_e15_state(str(r.prev_state),e.partial_state))}
                    for name,(got,want) in checks.items():
                        if got!=want:bad(name,kk,got,want)
                    pp=tuple(getattr(r,f'realtime_p_{h}m') for h in (15,30,60))
                    if all(pd.isna(x) for x in pp):
                        if e.recovery_probabilities is not None:bad('probability_null',kk,e.recovery_probabilities,None)
                    elif e.recovery_probabilities is None:bad('probability_missing',kk,None,pp)
                    else:
                        diff=max(abs(x-y) for x,y in zip(e.recovery_probabilities,pp));max_probability_diff=max(max_probability_diff,diff)
                        if diff>1e-15:bad('probability_drift',kk,e.recovery_probabilities,pp)
                    if e.vol_ratio is not None:max_ratio_diff=max(max_ratio_diff,abs(e.vol_ratio-r.partial_vol_ratio))
                    if e.shock_intensity is not None:max_intensity_diff=max(max_intensity_diff,abs(e.shock_intensity-r.partial_shock_intensity))
                elif e.state is not None:bad('extra_eligible_row',kk,e.state,None)
                if context is not None:
                    altered=prices.copy();altered[times>ns(target)]*=1.37
                    ap,ao=choose(times,altered,ns(start),ns(target))
                    alt=context.e15(bar_end=end,price=ap,observation_time=ao)
                    context.close(bar_end=end,price=float(rr.close)*1.2)
                    same=canonical(e.record())==canonical(alt.record())
                    prefix_checks.append({'symbol':sym,'bar_end':end.isoformat(),'future_quote_and_close_perturbation_prefix_equal':same})
                    if not same:bad('future_prefix',kk,False,True)
            c=k.close(bar_end=end,price=float(rr.close))
            # The entire final-reference trajectory is independently checked.
            oracle=reference.loc[rr.Index]
            if k.state!=str(oracle.risk_state):bad('final_state',key(sym,end),k.state,oracle.risk_state)
            if scored:
                events.append(c);stats['close_grid_rows']+=1;transitions['CLOSE|'+c.transition]+=1
                reasons['CLOSE|'+c.availability_reason]+=1;reasons['CLOSE_PROB|'+c.recovery_reason]+=1
                if c.state is not None:
                    stats['close_available']+=1
                    if c.shock!=bool(oracle.shock):bad('final_shock',key(sym,end),c.shock,oracle.shock)
                if c.recovery_probabilities is not None:
                    stats['close_probability_rows']+=1
                    wanted=surface[(str(oracle.risk_state),v9.age_bucket(c.recent_shock_age_bars))]
                    if c.recovery_probabilities!=wanted:bad('close_probability',key(sym,end),c.recovery_probabilities,wanted)
        del quotes
    for kk in expected.keys()-seen:bad('missing_reference_row',kk,None,'present')
    events.sort(key=lambda e:(e.published_at,e.symbol,e.event_type));ledger=Ledger()
    for e in events:ledger.append(e)
    for e in events:
        if ledger.as_of(e.symbol,e.published_at)!=e:bad('asof_at_publication',e.event_id,None,e.state)
        if e.event_type=='E15':
            atclose=ledger.as_of(e.symbol,e.bar_end)
            if atclose is not None and atclose.event_type=='E15':bad('stale_e15',e.event_id,atclose.event_type,'CLOSE_OR_UNAVAILABLE')
        if e.recovery_probabilities is not None:
            p=e.recovery_probabilities
            if not(p[0]<=p[1]<=p[2]) or p[2]!=anchor[bucket(e.recent_shock_age_bars)]:bad('surface_integrity',e.event_id,p,'frozen')
    with gzip.open(out/'causal_event_ledger.jsonl.gz','wt',encoding='utf-8') as f:
        for e in events:f.write(canonical(e.record())+'\n')
    (out/'mismatches.json').write_text(json.dumps(mismatches,indent=2)+'\n')
    (out/'market_prefix_checks.json').write_text(json.dumps(prefix_checks,indent=2)+'\n')
    summary={'schema':'d2_replay_summary_v1','execution_location':'github_actions','execution_commit':os.environ.get('GITHUB_SHA'),
      'run_id':os.environ.get('GITHUB_RUN_ID'),'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
      'source_rows':source_rows,'stats':dict(stats),'by_symbol_year':{g:dict(z) for g,z in by_group.items()},
      'reasons':dict(reasons),'transitions':dict(transitions),'mismatch_count':len(mismatches),'matched_expected_keys':len(seen),
      'market_prefix_check_count':len(prefix_checks),'all_market_prefix_checks_pass':all(x['future_quote_and_close_perturbation_prefix_equal'] for x in prefix_checks),
      'max_abs_e15_probability_diff':max_probability_diff,'max_abs_partial_ratio_diff':max_ratio_diff,
      'max_abs_partial_intensity_diff':max_intensity_diff,'ledger_event_count':len(events),'ledger_hash_chain_head':ledger.digest,
      'timing_basis':'owner_realtime_assumption','assumed_e15_publication_lead_seconds':15,'measured_feed_latency':False,
      'full_repository_test_suite_run':False,'d3_executed':False,'new_statistical_validation':False,'v20_started':False,
      'queried_2026_3s':False,'blackbox_queried':False,'pnl_computed':False,'production_authority':False}
    gates={'no_mismatch':not mismatches,'all_original_keys':len(seen)==sum(source_rows.values()),
      'same_eligible_count':stats['e15_available']==sum(source_rows.values()),'two_events_per_grid_bar':len(events)==2*stats['e15_grid_rows'],
      'market_prefix_count_20':len(prefix_checks)==20,'market_prefix_pass':summary['all_market_prefix_checks_pass']}
    summary['acceptance']=gates;summary['d2_supported']=all(gates.values());summary['decision']='D2_CAUSAL_REPLAY_SUPPORTED_D3_NOT_EXECUTED' if summary['d2_supported'] else 'D2_REPLAY_NOT_SUPPORTED'
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)
    return 0 if summary['d2_supported'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,default=Path('.'));p.add_argument('--out',type=Path,default=Path('artifacts/d2_causal_replay'))
    a=p.parse_args();raise SystemExit(run(a.repo_root.resolve(),a.out.resolve()))
