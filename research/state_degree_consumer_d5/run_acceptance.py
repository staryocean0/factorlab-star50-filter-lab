"""Replay sealed D2/D4 delivery artifacts only; no statistical evaluation."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from datetime import timedelta
import gzip
import hashlib
import io
import json
from pathlib import Path
import platform
import zipfile

from consumer import (ATTRIBUTE_FIELDS, SYMBOLS, ResearchConsumer, aware,
                      build_snapshot, canonical, csv_time)

D2_SHA = "cf1c89e1412fd70f27992d9077af10dd7887a6843072e03ef808902bf5a84096"
D4_SHA = "347abb143e3c56ddb0b41a6e3c1cd1b4c2362329f8fd25e23e21e28151cba903"
ROOT_MAIN = "11ade25e0ea7a25321955015e327854915cc211a"
PROTOCOL_COMMIT = "e0eb6d0006c326430aa6429ce52a24df60d65e3f"


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def verified_archive(path: Path, expected: str, manifest: str) -> tuple[zipfile.ZipFile, dict]:
    if digest(path.read_bytes()) != expected:
        raise ValueError(f"archive identity mismatch: {path.name}")
    z = zipfile.ZipFile(path)
    names = z.namelist()
    if len(names) != len(set(names)) or any(n.startswith('/') or '..' in Path(n).parts for n in names):
        raise ValueError("invalid archive members")
    m = json.loads(z.read(manifest))
    for r in m['files']:
        name = r.get('path', r.get('name'))
        if digest(z.read(name)) != r['sha256']:
            raise ValueError(f"manifest mismatch: {name}")
    return z, dict(archive_sha256=expected, manifest_sha256=digest(z.read(manifest)), files_verified=len(m['files']))


def json_out(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def signature(view: dict) -> str:
    return digest(canonical(view).encode())


def load_attributes(z: zipfile.ZipFile) -> dict:
    m = json.loads(z.read('results_d4/ATTRIBUTE_METADATA.json'))
    if (m['timezone'], m['clock_basis'], m['production_authority']) != ('Asia/Shanghai', 'owner_realtime_assumption', False):
        raise ValueError('D4 metadata mismatch')
    rows = {}
    with gzip.GzipFile(fileobj=z.open('results_d4/causal_attributes.csv.gz')) as gz:
        reader = csv.DictReader(io.TextIOWrapper(gz, encoding='utf-8'))
        if set(reader.fieldnames) != ATTRIBUTE_FIELDS:
            raise ValueError('D4 column whitelist mismatch')
        for a in reader:
            k = (a['symbol'], csv_time(a['bar_end'], m['timezone']).isoformat())
            if k in rows:
                raise ValueError('duplicate D4 key')
            rows[k] = a
    if len(rows) != 116352:
        raise ValueError('D4 row coverage mismatch')
    return rows


def run(args) -> None:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    d2, m2 = verified_archive(Path(args.d2_zip), D2_SHA, 'output_manifest.json')
    d4, m4 = verified_archive(Path(args.d4_zip), D4_SHA, 'BUNDLE_MANIFEST.json')
    json_out(out/'INPUT_VERIFICATION.json', {'D2':m2, 'D4':m4, 'raw_market_files_opened':False, 'future_target_files_parsed':False})
    attrs = load_attributes(d4)
    dates = {}
    for symbol, end in attrs:
        dates.setdefault((symbol, end[:4]), set()).add(end[:10])
    anchors = {(s, day+'T10:00:00+08:00') for (s,y),days in dates.items() for day in (min(days), max(days))}
    consumer = ResearchConsumer()
    event_index, anchor_checks, samples = [], [], []
    counts = Counter(); scalar_max = 0.; used = set()
    # Stable compressed bytes, independent of wallclock run time.
    with gzip.GzipFile(filename=str(out/'consumer_events.jsonl.gz'), mode='wb', compresslevel=1, mtime=0) as output:
        with gzip.GzipFile(fileobj=d2.open('causal_event_ledger.jsonl.gz')) as gz:
            for line in io.TextIOWrapper(gz, encoding='utf-8'):
                e = json.loads(line); key = (e['symbol'], e['bar_end']); kind = e['event_type']
                a = attrs.get(key) if kind == 'E15' else None
                if kind == 'E15':
                    if a is None: raise ValueError('missing sealed D4 counterpart')
                    used.add(key)
                snap = build_snapshot(e, a)
                consumer.ingest(snap, received_at=snap.published)
                output.write((snap.payload+'\n').encode())
                v=snap.as_dict(); counts['events']+=1; counts[kind]+=1
                if counts['events'] % 25000 == 0:print('joined',counts['events'],flush=True)
                counts[kind+'_'+e['availability_reason']]+=1
                counts['transition_'+e['transition']]+=1
                if e['recovery_probabilities'] is not None:counts[kind+'_recovery_curves']+=1
                if kind=='CLOSE' and any(v[k] is not None for k in ('lag_intensity','lag_ratio','delta_intensity','delta_ratio')):
                    raise ValueError('CLOSE received E15 enhancements')
                if kind=='E15' and v['observation_age_seconds'] is not None:
                    age=v['observation_age_seconds']; scalar_max=max(scalar_max,age)
                    if age>120:counts['E15_observation_age_gt120']+=1
                    if age>15:counts['E15_observation_age_gt15']+=1
                event_index.append((snap.symbol,snap.event_id,snap.published,snap.expires))
                if kind=='E15' and key in anchors:
                    before=signature(consumer.as_of(snap.symbol,snap.published))
                    # A changed future CLOSE must not overwrite this published E15.
                    alt=ResearchConsumer();alt.ingest(snap,received_at=snap.published)
                    close=dict(e,event_type='CLOSE',event_id=e['event_id'].replace('|E15','|CLOSE'),
                               decision_time=e['bar_end'],published_at=e['bar_end'],observation_time=e['bar_end'],
                               observation_known_at=e['bar_end'],partial_state=None,state='NORMAL',state_basis='CLOSE_CONFIRMED',
                               bucket_key='NORMAL|CLOSE_CONFIRMED',exit_pending=False,shock=False,recovery_probabilities=None,
                               recovery_reason='confirmed_normal',transition='SYNTHETIC_FUTURE_CHANGE',
                               valid_until=(aware(e['bar_end'])+timedelta(minutes=4,seconds=45)).isoformat())
                    future=build_snapshot(close);alt.ingest(future,received_at=future.published)
                    changed=signature(alt.as_of(snap.symbol,snap.published))
                    if before!=changed:raise ValueError('future perturbation rewrote prefix')
                    anchor_checks.append(dict(symbol=snap.symbol,as_of=snap.published.isoformat(),event_id=snap.event_id,
                                              prefix_sha256=before,future_perturbed_sha256=changed))
                if e['symbol']=='000688.SH' and e['bar_end'][:10]=='2024-01-02' and e['bar_end'][11:16] in ('09:35','10:00','11:30','13:05','15:00'):
                    samples.append(v)
    if used != set(attrs) or counts['events']!=232704 or counts['E15_AVAILABLE']!=113928 or counts['CLOSE_AVAILABLE']!=113928:
        raise ValueError('coverage changed')
    for r in anchor_checks:
        full=signature(consumer.as_of(r['symbol'],r['as_of']));r['full_history_sha256']=full
        if full != r['prefix_sha256']:raise ValueError('future append rewrote history')
    if len(anchor_checks)!=20:raise ValueError('anchor coverage mismatch')
    print('event join complete:',counts['events'],flush=True)
    statuses=Counter()
    with gzip.GzipFile(filename=str(out/'asof_probes.csv.gz'),mode='wb',compresslevel=1,mtime=0) as gz:
        with io.TextIOWrapper(gz,encoding='utf-8',newline='') as text:
            writer=csv.writer(text);writer.writerow(['source_event_id','symbol','as_of','selected_event_id','status','reason'])
            for symbol,event_id,pub,expiry in event_index:
                for t in (pub-timedelta(microseconds=1),pub,expiry-timedelta(microseconds=1),expiry):
                    v=consumer.as_of(symbol,t);selected=v['snapshot']['event_id'] if v['snapshot'] else ''
                    writer.writerow([event_id,symbol,t.isoformat(),selected,v['status'],v['reason']]);statuses[v['status']]+=1
    json_out(out/'PREFIX_CHECKS.json',anchor_checks)
    json_out(out/'SAMPLE_EVENTS.json',samples)
    summary=dict(schema='d5_bounded_consumer_acceptance_summary_v1',source_main=ROOT_MAIN,protocol_commit=PROTOCOL_COMMIT,
                 counts=dict(counts),asof_probes=sum(statuses.values()),probe_status_counts=dict(statuses),
                 max_observation_age_seconds=scalar_max,consumer_prefix_checks=len(anchor_checks),
                 actual_receipt_log=False,execution_location='current_chat_container',python=platform.python_version(),
                 independent_verification_required=True,statistical_evaluation_performed=False,new_models_fit=0,
                 raw_3s_reread=False,queried_2026=False,blackbox_queried=False,pnl_computed=False,production_authority=False)
    json_out(out/'SUMMARY.json',summary)
    manifest=[]
    for p in sorted(out.iterdir()):
        if p.is_file():manifest.append(dict(path=p.name,bytes=p.stat().st_size,sha256=digest(p.read_bytes())))
    json_out(out/'OUTPUT_MANIFEST.json',{'schema':'d5_output_manifest_v1','files':manifest})
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--d2-zip',required=True);p.add_argument('--d4-zip',required=True);p.add_argument('--out',required=True)
    run(p.parse_args())
