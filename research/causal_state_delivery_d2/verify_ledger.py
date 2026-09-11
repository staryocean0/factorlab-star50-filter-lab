"""Independent stdlib verifier for the sealed D2 JSONL ledger, not raw-price replay."""
import argparse, gzip, hashlib, json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

TABLE={
 ('UNSAFE','LT15'):(.007220216606498195,.032490974729241874,.718728403593642),
 ('UNSAFE','M15_25'):(.007858546168958742,.0550098231827112,.8646694214876033),
 ('UNSAFE','M30_40'):(.013628620102214651,.6252129471890971,.944254835039818),
 ('UNSAFE','GE45'):(.5246252676659529,.8244111349036403,.9799453053783045),
 ('RECOVERING','LT15'):(.04778156996587031,.08276450511945392,.718728403593642),
 ('RECOVERING','M15_25'):(.04478656403079076,.10286913925822254,.8646694214876033),
 ('RECOVERING','M30_40'):(.08525149190110827,.7689684569479965,.944254835039818),
 ('RECOVERING','GE45'):(.7501445922498554,.9097744360902256,.9799453053783045)}

def verify(root):
    manifest=json.loads((root/'output_manifest.json').read_text())
    for f in manifest['files']:
        b=(root/f['name']).read_bytes()
        assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
    s=json.loads((root/'summary.json').read_text());head='0'*64;last=None;seen=set();counts=Counter();ctx={};staleness=[];retained=Counter();freshness={};stale_end=Counter();stale_obs=Counter();other_stale=0
    with gzip.open(root/'causal_event_ledger.jsonl.gz','rt',encoding='utf-8') as stream:
        for line in stream:
            d=json.loads(line);end=datetime.fromisoformat(d['bar_end']);decision=datetime.fromisoformat(d['decision_time']);pub=datetime.fromisoformat(d['published_at'])
            assert 2021<=end.year<=2025 and d['production_authority'] is False
            assert last is None or pub>=last;last=pub
            assert d['event_id'] not in seen;seen.add(d['event_id'])
            assert pub>=decision and not ({'final_state','future_return','episode_end','trade_allowed','position','pnl'}&d.keys())
            c=ctx.setdefault((d['symbol'],end.date()),{'pos':-1,'last_shock':None})
            pos=c['pos']+1
            if d['event_type']=='E15':
                assert decision==end-timedelta(seconds=15) and datetime.fromisoformat(d['valid_until'])==end
                if d['state'] is not None:
                    partial=d['partial_state'];prev=d['previous_confirmed_state']
                    expected=partial if partial in ('UNSAFE','RECOVERING') else prev if prev in ('UNSAFE','RECOVERING') else 'NORMAL'
                    assert d['state']==expected
                    obs=datetime.fromisoformat(d['observation_time']);known=datetime.fromisoformat(d['observation_known_at'])
                    assert obs<=known<=decision;lag=(decision-obs).total_seconds();staleness.append(lag)
                    freshness.setdefault(f"{d['symbol']}|{end.year}",[]).append(lag)
                    if lag>120:stale_end[end.strftime('%H:%M')]+=1;stale_obs[obs.strftime('%H:%M:%S')]+=1
                    if lag>15 and end.strftime('%H:%M')!='15:00':other_stale+=1
            else:
                assert d['event_type']=='CLOSE' and decision==end
                assert datetime.fromisoformat(d['observation_known_at'])>=end
                if d['shock']:c['last_shock']=pos
                c['pos']=pos
            if d['state'] is None:
                assert d['bucket_key']=='UNAVAILABLE' and d['recovery_probabilities'] is None
                assert d['previous_confirmed_state'] is None and d['partial_state'] is None
                retained[(d['event_type'],end.strftime('%H:%M:%S'))]+=1
            else:
                age=None if c['last_shock'] is None else pos-c['last_shock']
                assert age==d['recent_shock_age_bars']
            p=d['recovery_probabilities']
            if p is not None:
                a=d['recent_shock_age_bars'];b='LT15' if a<=2 else 'M15_25' if a<=5 else 'M30_40' if a<=8 else 'GE45'
                state=d['partial_state'] if d['event_type']=='E15' else d['state']
                assert tuple(p)==TABLE[(state,b)] and d['recovery_reason']=='scored' and a>0 and not d['shock']
            counts[d['event_type']]+=1
            counts[d['event_type']+'|'+d['availability_reason']]+=1
            digest=hashlib.sha256(line.rstrip('\n').encode()).hexdigest()
            head=hashlib.sha256((head+digest).encode()).hexdigest()
    assert head==s['ledger_hash_chain_head'] and len(seen)==s['ledger_event_count']
    assert counts['E15']==counts['CLOSE']==116352
    assert retained=={('E15','09:35:00'):2424,('CLOSE','09:35:00'):2424}
    return {'schema':'d2_independent_ledger_verification_v1','execution_location':'current_chat_container',
      'events_verified':len(seen),'all_output_files_sha256_verified':len(manifest['files']),
      'ledger_hash_chain_head':head,'hash_chain_verified':True,'timing_and_no_backdating_verified':True,
      'e15_rule_and_confirmed_shock_clock_verified':True,'probabilities_match_connector_read_frozen_v16_table':True,
      'all_unavailable_events_are_first_daily_bar':True,'complete_grid_state_coverage':counts['E15|AVAILABLE']/counts['E15'],
      'e15_observation_staleness_seconds':{'min':min(staleness),'max':max(staleness),'mean':sum(staleness)/len(staleness)},
      'stale_observation_counts':{str(t):sum(x>t for x in staleness) for t in (3,15,30,60,120)},
      'freshness_by_symbol_year':{g:{'n':len(xs),'max':max(xs),'mean':sum(xs)/len(xs),'older_than_15s':sum(x>15 for x in xs)} for g,xs in freshness.items()},
      'freshness_boundary_detail':{'older_than_120s_by_bar_end':dict(stale_end),'older_than_120s_observation_times':dict(stale_obs),'older_than_15s_excluding_1500_rows':other_stale},
      'raw_price_replay_repeated_in_current_container':False,'measured_latency':False,'passed':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('artifact_directory',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args();v=verify(a.artifact_directory);text=json.dumps(v,indent=2,sort_keys=True)+'\n'
    if a.out:a.out.write_text(text)
    print(text)
