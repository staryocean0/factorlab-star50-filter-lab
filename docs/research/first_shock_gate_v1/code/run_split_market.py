"""Local-only bounded minute comparison, prepared but NOT executed in cloud.

Runs original aggregate and post-synthetic split-scale candidate side by side.
Neither candidate is production-approved. Both use consumed 2021-2025 history.
"""
from __future__ import annotations
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import first_shock_gate as g
import diagnose_measurement as d


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();root=args.repo_root.resolve()
    if args.out.exists() and any(args.out.iterdir()):raise FileExistsError('immutable outputs')
    args.out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    panels={};source_rows={}
    for symbol in ('000688.SH','000852.SH'):
        raw=load_market_data(symbol,'1m','2021-01-01','2025-12-31',root=root)
        source_rows[symbol]=len(raw)
        panels[symbol]=g.minute_panel(raw,symbol)
    a,b=panels['000688.SH'],panels['000852.SH']
    common=set(a.session)&set(b.session)
    a=a[a.session.isin(common)].reset_index(drop=True)
    b=b[b.session.isin(common)].reset_index(drop=True)
    if not a[['session','minute']].equals(b[['session','minute']]):raise ValueError('unpaired grid')
    joint=np.isfinite(a.return_bp)&np.isfinite(b.return_bp)
    individual={s:int(np.isfinite(x.return_bp).sum()) for s,x in (('000688.SH',a),('000852.SH',b))}
    outputs={}
    for symbol,x in (('000688.SH',a),('000852.SH',b)):
        x.loc[~joint,'return_bp']=np.nan
        f=d.add_components(g.make_features(x))
        train=f[f.year.isin([2021,2022])];cal=f[f.year==2023]
        pairs={'aggregate_v1':g.fit_pair(train,cal),'split_post_synthetic':d.fit_split(f)}
        for name,pair in pairs.items():
            joblib.dump(pair,args.out/f'{symbol}_{name}_estimators.joblib')
            for year in (2024,2025):
                summary,points,events=g.evaluate(pair,f[f.year==year])
                label=f'{symbol}_{name}_{year}'
                outputs[label]=summary
                g.write_json(args.out/f'{label}_summary.json',summary)
                points.to_csv(args.out/f'{label}_decisions.csv.gz',index=False,compression='gzip')
                events.to_csv(args.out/f'{label}_events.csv',index=False)
    git=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],capture_output=True,text=True)
    manifest=root/'data/cross_index_risk_gate_v1/manifest.json'
    g.write_json(args.out/'market_run_receipt.json',{
        'status':'completed minute development experiment; not scientific promotion',
        'execution_location':'caller local environment','repository_commit':git.stdout.strip() if git.returncode==0 else None,
        'input_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
        'source_rows':source_rows,'paired_sessions':len(common),'paired_rows':len(a),
        'valid_returns_individual':individual,'valid_returns_joint':int(joint.sum()),
        'post_2025_reads':False,'fresh_oos':False,'production_authority':False,
        'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                         (Path(__file__),Path(g.__file__),Path(d.__file__))},
        'not_run':['subminute market study','individual-quality-support sensitivity',
                   'full seasonal random alarm ensemble','non-overlap phases','economic mechanism identification'],
        'summary_files':[s+'_summary.json' for s in outputs]})
    print('Completed bounded minute comparison; see market_run_receipt.json.')


if __name__=='__main__':main()
