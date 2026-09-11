"""Independent stdlib verifier. Does not import the D5 consumer or replay runner."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import zipfile

BASE_FIELDS=set('age_clock availability_reason bar_end bucket_key decision_time event_id event_type exit_pending frozen_v16_blob frozen_v19_blob frozen_v9_blob observation_known_at observation_time partial_state previous_confirmed_state probability_target_clock production_authority published_at recent_shock_age_bars recovery_probabilities recovery_reason schema shock shock_intensity state state_basis symbol timing_basis transition valid_until vol_ratio'.split())
ADDED_FIELDS=set('source_schema source_event_sha256 numeric_basis numeric_availability lag_intensity lag_ratio delta_intensity delta_ratio delta_status observation_age_seconds quantile_encoding information_scope'.split())
ZONE=timezone(timedelta(hours=8))
D2_SHA='cf1c89e1412fd70f27992d9077af10dd7887a6843072e03ef808902bf5a84096'
D4_SHA='347abb143e3c56ddb0b41a6e3c1cd1b4c2362329f8fd25e23e21e28151cba903'


def sha(b):return hashlib.sha256(b).hexdigest()

def time_of(v):
    d=datetime.fromisoformat(v)
    if d.utcoffset() is None:raise ValueError('naive consumer timestamp')
    return d.astimezone(ZONE)


def ref_select(items,t):
    # Deliberately separate from bisect-based consumer and its session helper.
    seconds=t.hour*3600+t.minute*60+t.second+t.microsecond/1000000
    if not (34200<=seconds<=41400 or 46800<=seconds<=54000):
        return '', 'NO_CURRENT_SNAPSHOT', 'SESSION_CLOSED'
    lo,hi=0,len(items)
    while lo<hi:
        mid=(lo+hi)//2
        if items[mid][0]<=t:lo=mid+1
        else:hi=mid
    if lo==0:return '', 'NO_CURRENT_SNAPSHOT', 'NO_PUBLISHED_EVENT'
    pub,expiry,eid,state,reason=items[lo-1]
    if t>=expiry:return '', 'NO_CURRENT_SNAPSHOT', 'LATEST_EVENT_EXPIRED'
    return eid, 'AVAILABLE' if state is not None else 'UNAVAILABLE', reason


def run(a):
    out=Path(a.out); errors=Counter(); examples=[]; counts=Counter();indexes={s:[] for s in ('000688.SH','000852.SH')}
    def check(condition,kind,context=''):
        if not condition:
            errors[kind]+=1
            if len(examples)<100:examples.append({'kind':kind,'context':context})
    for path,digest in ((a.d2_zip,D2_SHA),(a.d4_zip,D4_SHA)):
        if sha(Path(path).read_bytes())!=digest:raise ValueError('source zip identity mismatch')
    manifest=json.loads((out/'OUTPUT_MANIFEST.json').read_text())
    for entry in manifest['files']:
        p=out/entry['path']
        if sha(p.read_bytes())!=entry['sha256']:raise ValueError('output identity mismatch: '+str(p))
    with zipfile.ZipFile(a.d4_zip) as z:
        attrs={}
        with gzip.GzipFile(fileobj=z.open('results_d4/causal_attributes.csv.gz')) as gz:
            for r in csv.DictReader(io.TextIOWrapper(gz,encoding='utf-8')):
                key=(r['symbol'],datetime.fromisoformat(r['bar_end']).replace(tzinfo=ZONE).isoformat())
                if key in attrs:raise ValueError('duplicate attribute key')
                attrs[key]=r
    max_numeric_difference=0.
    with zipfile.ZipFile(a.d2_zip) as z, gzip.open(out/'consumer_events.jsonl.gz','rt') as views:
        with gzip.GzipFile(fileobj=z.open('causal_event_ledger.jsonl.gz')) as gz:
            for line in io.TextIOWrapper(gz,encoding='utf-8'):
                e=json.loads(line);viewline=views.readline()
                if not viewline:raise ValueError('missing output event')
                v=json.loads(viewline);eid=e['event_id'];kind=e['event_type'];counts['events']+=1
                check(set(v)==BASE_FIELDS|ADDED_FIELDS,'output_whitelist',eid)
                for k in BASE_FIELDS-{'schema'}:check(v.get(k)==e[k],'source_'+k,eid)
                check(v['schema']=='state_degree_research_consumer_d5_v1','schema',eid)
                check(v['source_schema']==e['schema'],'source_schema',eid)
                data=json.dumps(e,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
                check(v['source_event_sha256']==sha(data),'source_hash',eid)
                check(v['quantile_encoding']=='OMITTED_NOT_ADMITTED_AS_GATE','quantile_quarantine',eid)
                check(v['numeric_availability']==e['availability_reason'],'availability',eid)
                numbers=('lag_intensity','lag_ratio','delta_intensity','delta_ratio')
                if kind=='E15':
                    r=attrs[(e['symbol'],e['bar_end'])];counts['matched_E15']+=1
                    check(v['numeric_basis']=='D4_E15_ENRICHED','E15_basis',eid)
                    check(v['information_scope']=='D4_E15_SPECIFIED_ENDPOINTS_ONLY','E15_scope',eid)
                    for k in numbers:
                        expected=float(r[k]) if r[k] else None
                        actual=v[k]
                        if expected is None:check(actual is None,'missing_'+k,eid)
                        elif actual is None:check(False,'missing_'+k,eid)
                        else:
                            difference=abs(actual-expected);max_numeric_difference=max(max_numeric_difference,difference)
                            check(difference<=1e-12,'numeric_'+k,eid)
                else:
                    check(v['numeric_basis']=='D2_CLOSE_CONFIRMED','CLOSE_basis',eid)
                    check(v['information_scope']=='D2_CONTEXT_NOT_D4_E15_UTILITY','CLOSE_scope',eid)
                    check(all(v[k] is None for k in numbers),'CLOSE_enrichment_leak',eid)
                expect_delta='UNAVAILABLE' if e['state'] is None else 'NOT_DEFINED_FOR_CLOSE' if kind=='CLOSE' else 'DESCRIPTIVE_ONLY'
                check(v['delta_status']==expect_delta,'delta_status',eid)
                obs=time_of(e['observation_time']) if e['observation_time'] else None
                expected_age=(time_of(e['decision_time'])-obs).total_seconds() if obs else None
                check(v['observation_age_seconds']==expected_age,'observation_age',eid)
                indexes[e['symbol']].append((time_of(e['published_at']),time_of(e['valid_until']),eid,e['state'],e['availability_reason']))
            check(not views.readline(),'extra_output_event')
    print('independent event parity complete:',counts['events'],flush=True)
    with gzip.open(out/'asof_probes.csv.gz','rt') as f:
        for r in csv.DictReader(f):
            expected=ref_select(indexes[r['symbol']],time_of(r['as_of']))
            actual=(r['selected_event_id'],r['status'],r['reason'])
            check(actual==expected,'asof_selection',r['source_event_id']+'@'+r['as_of']);counts['asof_probes']+=1
    checks=json.loads((out/'PREFIX_CHECKS.json').read_text())
    for r in checks:
        check(r['prefix_sha256']==r['full_history_sha256']==r['future_perturbed_sha256'],'prefix_hash',r['event_id'])
    check(counts['events']==232704,'event_count');check(counts['matched_E15']==116352,'E15_count')
    check(counts['asof_probes']==930816,'query_count');check(len(checks)==20,'prefix_count')
    result=dict(schema='d5_independent_acceptance_verification_v1',passed=not errors,counts=dict(counts),
                mismatches=dict(errors),mismatch_examples=examples,max_enrichment_abs_difference=max_numeric_difference,
                prefix_receipts_checked=len(checks),output_files_sha256_verified=len(manifest['files']),
                consumer_imported=False,raw_prices_read=False,new_predictive_utility_claim=False,production_authority=False)
    Path(a.report).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(result,sort_keys=True),flush=True)
    if errors:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--d2-zip',required=True);p.add_argument('--d4-zip',required=True);p.add_argument('--out',required=True);p.add_argument('--report',required=True)
    run(p.parse_args())
