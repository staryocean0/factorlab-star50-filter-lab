"""Independent saved-prediction/target verification; does not select or refit."""
import argparse, gzip, hashlib, io, json, math, statistics, zipfile
from collections import deque
from pathlib import Path
import numpy as np
import pandas as pd


def run(transport:Path, out:Path):
    with zipfile.ZipFile(transport) as z:
        meta=json.loads(z.read('TRANSPORT_RECEIPT.json'))
        frames=[pd.read_csv(z.open(x['csv_file']),compression='gzip',float_precision='round_trip') for x in meta['exports']]
    data=pd.concat(frames).sort_values(['symbol','bar_end'])
    prices={}; backgrounds={}; prev={}; buffers={}; lastday={}
    for r in data.itertuples(index=False):
        key=(r.symbol,r.bar_end); prices[key]=float(r.close)
        buf=buffers.setdefault(r.symbol,deque(maxlen=48))
        if lastday.get(r.symbol)!=r.trading_day: prev[r.symbol]=None
        previous=prev.get(r.symbol)
        backgrounds[key]=statistics.pstdev(buf) if len(buf)==48 and previous is not None else None
        if previous is not None: buf.append(math.log(r.close)-math.log(previous))
        prev[r.symbol]=r.close;lastday[r.symbol]=r.trading_day
    s=json.loads((out/'SUMMARY.json').read_text());checked=0;max_y_diff=0.;loss_diffs=[]
    from datetime import datetime,timedelta
    for h in (15,30,60):
        q=pd.read_csv(out/f'validation_predictions_{h}m.csv.gz',float_precision='round_trip')
        assert len(q)==s['coverage'][str(h)]['eligible']
        assert set(q.trading_day.str[:4])=={'2024','2025'}
        assert not q.duplicated(['symbol','bar_end']).any()
        for row in q.itertuples(index=False):
            e=datetime.fromisoformat(row.bar_end); t=datetime.fromisoformat(row.decision_time)
            assert (e-t).total_seconds()==15
            nodes=[e+timedelta(minutes=5*k) for k in range(h//5+1)]
            assert all(v.date()==e.date() and (v.hour>=13)==(e.hour>=13) for v in nodes)
            key=lambda v:(row.symbol,v.isoformat())
            r=[math.log(prices[key(b)])-math.log(prices[key(a)]) for a,b in zip(nodes,nodes[1:])]
            y=math.log(max(math.sqrt(sum(v*v for v in r)/len(r)),1e-12))
            bg=backgrounds[key(e)]
            tail=float(max(abs(v) for v in r)>=3*bg)
            max_y_diff=max(max_y_diff,abs(y-row.log_future_sigma))
            assert abs(y-row.log_future_sigma)<1e-9
            assert tail==row.future_tail
            checked+=1
        for endpoint in ('log_future_sigma','future_tail'):
            for model in ('B0','B1','B2','B3','B4'):
                loss=float(np.mean((q[endpoint]-q[endpoint+'_'+model])**2))
                loss_diffs.append(abs(loss-s['all_probe_losses'][f'{h}|{endpoint}|{model}']))
            for base,enhanced in (('B1','B2'),('B3','B4')):
                gain=(q[endpoint]-q[endpoint+'_'+base])**2-(q[endpoint]-q[endpoint+'_'+enhanced])**2
                record=next(r for r in s['comparisons'] if r['horizon_minutes']==h and r['endpoint']==endpoint and r['comparison']==enhanced+'_vs_'+base)
                assert abs(gain.mean()-record['absolute_gain'])<1e-12
                blocks=pd.read_csv(out/f'blocks_{h}_{endpoint}_{enhanced}_vs_{base}.csv',float_precision='round_trip')
                assert blocks.n.sum()==len(q)
                assert abs(blocks.gain.sum()/blocks.n.sum()-gain.mean())<1e-12
    modelhash=hashlib.sha256((out/'FROZEN_PROBES.json').read_bytes()).hexdigest()
    assert modelhash==s['model_sha256_before_after']
    assert max(loss_diffs)<1e-12
    result={'schema':'d3_independent_target_and_metric_check_v1','execution_location':'current_chat_container',
            'verified_validation_rows_across_three_horizons':checked,'future_tail_mismatches':0,
            'max_abs_log_sigma_difference':max_y_diff,'max_saved_metric_difference':max(loss_diffs),
            'model_hash_unchanged':modelhash,'same_day_same_session_future_nodes':True,'block_counts_match':True,
            'refit_performed':False,'all_passed':True}
    (out/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--transport',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.transport,a.out)
