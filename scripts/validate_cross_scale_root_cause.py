"""Outcome-neutral boundary, identity, accounting and immutable evidence audit."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from run_cross_scale_root_cause import OUT,PROTOCOL,sha,write_json,read_bar,read_daily
from reproduce_historical_baseline import load_bars,baseline_frame,HISTORICAL,fingerprint
from star50_filter.cross_scale_root_cause import FEATURES

SOURCES=['src/star50_filter/cross_scale_root_cause.py','scripts/run_cross_scale_root_cause.py',
    'scripts/complete_cross_scale_root_cause.py','scripts/validate_cross_scale_root_cause.py',
    'tests/test_cross_scale_root_cause.py','.github/workflows/cross-scale-root-cause.yml']
DOCS=['docs/research/cross_scale_root_cause/preregistration.json','docs/research/cross_scale_root_cause/preanalysis.md',
    'docs/research/cross_scale_root_cause/report.md','docs/research/cross_scale_root_cause/whitepaper.md',
    'docs/research/cross_scale_root_cause/workflow.md']

def validate(data_dir=None,check_manifest=True):
    protocol=json.loads(PROTOCOL.read_text());receipt=json.loads((OUT/'input_receipt.json').read_text())
    assert protocol['price_attributes']['features']==FEATURES
    assert receipt['protocol_sha256']==sha(PROTOCOL)
    assert len(receipt['inputs'])==14
    assert all(i['last']<='2025-12-31' for i in receipt['inputs'])
    for p,h in protocol['source_hashes'].items():assert sha(ROOT/p)==h,p
    assert protocol['authority']['production'] is False
    f=read_bar();d=read_daily();p=d.loc[d.view=='5m_offset_0']
    assert len(f)==58176 and len(p)==1212 and int(p.inference_ok.sum())==1192
    assert f.timestamp.is_monotonic_increasing and not f.timestamp.duplicated().any()
    assert f.trading_day.max()<='2025-12-31' and set(f.year)==set(range(2021,2026))
    assert set(f.exec_pos)=={-1.0,1.0},'Original full exposure changed'
    assert np.allclose(np.exp(np.cumsum(f.pnl_log)),f.nav,rtol=2e-13,atol=2e-13)
    daily=f.groupby('trading_day').pnl_log.sum()
    assert np.allclose(daily,p.set_index('trading_day').pnl_log,rtol=0,atol=1e-13)
    assert np.isclose(100*np.expm1(f.pnl_log.sum()/5),HISTORICAL['cagr_pct'],atol=1e-9)
    assert np.isclose(100*f.drawdown.min(),HISTORICAL['mdd_pct'],atol=1e-9)
    t=pd.read_csv(OUT/'trades.csv.gz');assert np.isclose(t.pnl_log.sum(),f.pnl_log.sum(),atol=1e-12)
    assert np.allclose(t.mfe_log-t.giveback_log,t.pnl_log,atol=1e-13)
    assert t.bars.sum()==len(f)
    e=pd.read_csv(OUT/'top10_legs.csv');assert len(e)==20
    components=pd.read_csv(OUT/'fixed_position_component_legs.csv')
    cells=pd.read_csv(OUT/'event_condition_cells.csv',dtype={'cell':str})
    for _,row in e.iterrows():
        total=f.pnl_log.iloc[int(row.start_return_index):int(row.end_return_index_exclusive)].sum()
        assert np.isclose(total,row.pnl_log,atol=1e-12)
        q=components[(components['rank']==row['rank'])&(components.leg==row.leg)]
        assert np.isclose(q.fixed_position_log_pnl.sum(),total,atol=1e-12)
        for name in ('fast_slow','short_long_eff'):
            z=cells[(cells['rank']==row['rank'])&(cells.leg==row.leg)&(cells.table==name)]
            assert np.isclose(z.pnl_log.sum(),total,atol=1e-12)
            assert z.bars.sum()==row.bars
    a=pd.read_csv(OUT/'ablation_paths.csv');assert len(a)==7
    a=pd.read_csv(OUT/'ablation_daily.csv.gz');a=a[a.components=='fast+medium+slow']
    assert np.allclose(a.pnl_log,p.pnl_log,atol=1e-12)
    s=pd.read_csv(OUT/'synthetic_wave_grid.csv');assert len(s)==84
    assert (s.kind=='wave').sum()==63 and (s.kind=='drift').sum()==21
    for name in ('associations.csv','causal_proxy_associations.csv'):
        a=pd.read_csv(OUT/name)
        assert len(a)==40 and set(a.feature)==set(FEATURES)
        assert set(a.outcome)=={'capture','pnl_log'}
        for method in ('circular','block20'):
            assert (a[f'{method}_maxT_p']>=a[f'{method}_p']).all()
            assert a[f'{method}_maxT_p'].between(.0005,1).all()
    previous=sha(PROTOCOL)
    for year in range(2021,2026):
        r=OUT/'sessions'/str(year)/'receipt.json';j=json.loads(r.read_text())
        assert j['year']==year and j['prior_receipt_sha256']==previous
        for path,h in j['files'].items():assert sha(ROOT/path)==h,path
        assert j['production_authority'] is False and j['policy_change'] is False
        previous=sha(r)
    from PIL import Image
    for path in OUT.rglob('*.png'):
        with Image.open(path) as im:im.verify()
    if data_dir is not None:
        original=baseline_frame(load_bars(data_dir));dev=original.loc[original.is_development]
        assert np.array_equal(dev.exec_pos.to_numpy(),f.exec_pos.to_numpy())
        assert np.allclose(dev.pnl_log,f.pnl_log,rtol=0,atol=1e-14)
        for k,v in HISTORICAL.items():assert np.isclose(fingerprint(original)[k],v,atol=1e-8),k
        # Material hashes identify the observed export; different Parquet
        # writers may re-encode identical prices, so replay uses numeric parity.
    manifest=OUT/'manifest.json'
    if check_manifest:
        j=json.loads(manifest.read_text())
        assert j['production_authority'] is False and j['fresh_oos'] is False
        for path,h in j['files'].items():assert sha(ROOT/path)==h,path
        for path,h in j['dependencies'].items():assert sha(ROOT/path)==h,path
        expected={str(x.relative_to(ROOT)) for x in OUT.rglob('*') if x.is_file() and x.name!='manifest.json'}|set(SOURCES)|set(DOCS)
        assert set(j['files'])==expected,'Evidence inventory changed after seal'
    return {'valid':True,'original_positions_unchanged':True,'years_reviewed_in_order':5,'market_policy_candidates':0,
        'primary_tests':40,'causal_proxy_tests':40,'synthetic_cases':84,'ablation_paths':7,'data_2026_used':False,'production_authority':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--data-dir',type=Path);ap.add_argument('--seal-manifest',action='store_true');a=ap.parse_args()
    if a.seal_manifest:
        if (OUT/'manifest.json').exists():raise ValueError('Manifest is already sealed; preserve it')
        result=validate(a.data_dir,check_manifest=False)
        paths=[x for x in OUT.rglob('*') if x.is_file()]+[ROOT/p for p in SOURCES+DOCS]
        dependencies=json.loads(PROTOCOL.read_text())['source_hashes']
        baseline='artifacts/drawdown_conditions/baseline_reproduction/reproduced_baseline_frame.csv.gz'
        dependencies[baseline]=sha(ROOT/baseline)
        write_json(OUT/'manifest.json',{'schema':'star50_cross_scale_root_cause_manifest@1','preregistration_commit':'dda728840fb142061572e80334089ed3ed70b3f2',
            'files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},'dependencies':dependencies,
            'mutable_entry_excluded':'CURRENT_RESEARCH.md','fresh_oos':False,'production_authority':False,'validation':result})
    result=validate(a.data_dir);print(json.dumps(result))
if __name__=='__main__':main()
