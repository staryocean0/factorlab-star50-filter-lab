"""Independent sequential scalar/label/loss checks; does not import the evaluator."""
from __future__ import annotations
import argparse
from collections import deque
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import statistics
import zipfile
import numpy as np
import pandas as pd


def run(transport: Path, out: Path) -> None:
    with zipfile.ZipFile(transport) as archive:
        receipt = json.loads(archive.read('TRANSPORT_RECEIPT.json'))
        frames = [pd.read_csv(archive.open(e['csv_file']), compression='gzip', float_precision='round_trip')
                  for e in receipt['exports']]
    data = pd.concat(frames).sort_values(['symbol','bar_end'])
    prices, features, buffers, previous, lastday = {}, {}, {}, {}, {}
    for row in data.itertuples(index=False):
        key = (row.symbol, row.bar_end)
        price = float(row.close)
        prices[key] = price
        buf = buffers.setdefault(row.symbol, deque(maxlen=48))
        if lastday.get(row.symbol) != row.trading_day:
            previous[row.symbol] = None
        prev = previous.get(row.symbol)
        if len(buf) == 48 and prev is not None:
            bg = statistics.pstdev(buf)
            features[key] = (bg, abs(buf[-1])/bg, statistics.pstdev(list(buf)[-12:])/bg)
        else:
            features[key] = None
        if prev is not None:
            buf.append(math.log(price)-math.log(prev))
        previous[row.symbol], lastday[row.symbol] = price, row.trading_day
    summary = json.loads((out/'SUMMARY.json').read_text())
    frozen = json.loads((out/'FROZEN_MODELS.json').read_text())
    attrs = pd.read_csv(out/'causal_attributes.csv.gz', float_precision='round_trip')
    assert len(attrs) == 116352 and int(attrs.available.sum()) == 113928
    assert not set(attrs.columns) & {'close','r','final_state','future_tail','log_future_sigma','episode_end'}
    maxlag = np.zeros(2); verified_attrs = 0
    for row in attrs.itertuples(index=False):
        if not row.available:
            assert row.numeric_bucket == 'UNAVAILABLE'
            assert all(pd.isna(getattr(row,c)) for c in ('shock_intensity','vol_ratio','lag_intensity','lag_ratio','delta_intensity','delta_ratio'))
            continue
        e = datetime.fromisoformat(row.bar_end)
        key = (row.symbol,e.isoformat())
        expected = features[key]
        assert expected is not None
        diff = np.abs(np.array(expected[1:])-np.array([row.lag_intensity,row.lag_ratio]))
        maxlag = np.maximum(maxlag,diff)
        assert float(diff.max()) < 1e-8
        assert abs(row.delta_intensity-(row.shock_intensity-row.lag_intensity)) < 1e-12
        assert abs(row.delta_ratio-(row.vol_ratio-row.lag_ratio)) < 1e-12
        parts=[]
        for col,prefix in (('shock_intensity','I'),('vol_ratio','V')):
            low,high=frozen['quantile_boundaries'][row.symbol][col]; value=getattr(row,col)
            parts.append(prefix+'_'+('QLOW' if value<=low else 'QMID' if value<=high else 'QHIGH'))
        assert row.numeric_bucket=='|'.join(parts)
        t=datetime.fromisoformat(row.decision_time)
        assert e-t==timedelta(seconds=15)
        assert datetime.fromisoformat(row.observation_time)<=t
        assert datetime.fromisoformat(row.published_at)<=t<datetime.fromisoformat(row.valid_until)
        verified_attrs+=1
    checked=0; maxlabel=0.; maxloss=0.; maxblock=0.
    for h in (15,30,60):
        q=pd.read_csv(out/f'validation_predictions_{h}m.csv.gz',float_precision='round_trip')
        assert len(q)==summary['coverage'][str(h)]['eligible']
        assert set(q.trading_day.str[:4])=={'2024','2025'}
        assert not q.duplicated(['symbol','bar_end']).any()
        for row in q.itertuples(index=False):
            e=datetime.fromisoformat(row.bar_end);t=datetime.fromisoformat(row.decision_time)
            nodes=[e+timedelta(minutes=5*i) for i in range(h//5+1)]
            assert e>t and all(v.date()==e.date() and (v.hour>=13)==(e.hour>=13) for v in nodes)
            r=[math.log(prices[(row.symbol,b.isoformat())])-math.log(prices[(row.symbol,a.isoformat())]) for a,b in zip(nodes,nodes[1:])]
            y=math.log(max(math.sqrt(sum(v*v for v in r)/len(r)),1e-12))
            bg=features[(row.symbol,e.isoformat())][0]
            maxlabel=max(maxlabel,abs(y-row.log_future_sigma))
            assert abs(y-row.log_future_sigma)<1e-9
            assert float(max(abs(v) for v in r)>=3*bg)==row.future_tail
            checked+=1
        for endpoint in ('log_future_sigma','future_tail'):
            for base in ('H','L'):
                rec=next(x for x in summary['comparisons'] if x['horizon']==h and x['endpoint']==endpoint and x['comparison']=='C_vs_'+base)
                l0=(q[endpoint]-q[endpoint+'_'+base])**2
                l1=(q[endpoint]-q[endpoint+'_C'])**2
                gain=l0-l1
                difference=max(abs(float(l0.mean())-rec['baseline_loss']),abs(float(l1.mean())-rec['continuous_loss']),abs(float(gain.mean())-rec['absolute_gain']))
                maxloss=max(maxloss,difference)
                assert difference<1e-12
                for days in (5,20):
                    blocks=pd.read_csv(out/f'blocks_{h}_{endpoint}_C_vs_{base}_{days}d.csv',float_precision='round_trip')
                    assert int(blocks.n.sum())==len(q)
                    d=q[['trading_day']].copy(); d['year']=q.trading_day.str[:4].astype(int); d['gain']=gain;d['n']=1
                    calendar=d[['year','trading_day']].drop_duplicates().sort_values(['year','trading_day'])
                    calendar['block']=calendar.groupby('year').cumcount()//days
                    independent=d.merge(calendar,on=['year','trading_day']).groupby(['year','block'],as_index=False)[['gain','n']].sum()
                    np.testing.assert_array_equal(independent[['year','block','n']],blocks[['year','block','n']])
                    delta=float(np.max(np.abs(independent.gain-blocks.gain)));maxblock=max(maxblock,delta);assert delta<1e-10
    digest=hashlib.sha256((out/'FROZEN_MODELS.json').read_bytes()).hexdigest()
    assert digest==summary['model_sha256_before_after']
    # Re-evaluate all point/interval/sign/forward gates from saved metrics, not the stated verdict.
    joint=[]
    for h in (15,30,60):
        for endpoint in ('log_future_sigma','future_tail'):
            rows=[r for r in summary['comparisons'] if r['horizon']==h and r['endpoint']==endpoint]
            assert len(rows)==2
            for r in rows:
                assert r['gates']['relative_at_least_one_percent']==(r['relative_gain']>=.01)
                assert r['gates']['tail_absolute_at_least_0005']==(endpoint!='future_tail' or r['absolute_gain']>=.0005)
                assert r['gates']['adjusted_5day_interval_positive']==(r['ci_5day']['low']>0)
                assert r['supported']==all(r['gates'].values())
            if all(r['supported'] for r in rows):joint.append(f'{h}|{endpoint}')
    assert joint==summary['supported_endpoints']
    result={'schema':'d4_independent_verification_v1','verified_attribute_rows':verified_attrs,
            'explicit_unavailable_rows':len(attrs)-verified_attrs,'verified_validation_rows':checked,
            'max_lag_intensity_difference':float(maxlag[0]),'max_lag_ratio_difference':float(maxlag[1]),
            'future_tail_mismatches':0,'max_log_future_RMS_difference':maxlabel,
            'max_saved_loss_difference':maxloss,'max_joint_block_sum_difference':maxblock,
            'frozen_model_sha256':digest,'quantile_assignments_verified':True,
            'causal_export_contains_no_outcomes':True,'joint_decision_verified':True,
            'no_refit':True,'all_passed':True}
    (out/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--transport',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();run(a.transport,a.out)
