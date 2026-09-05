"""Outcome-neutral closeout gate: evidence, boundaries, receipts and accounting."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from star50_filter.drawdown_diagnostics import drawdown_summary
OUT=ROOT/'artifacts/drawdown_conditions'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    manifest=read(OUT/'bundle_manifest.json')
    for name,d in manifest['files'].items():assert sha(ROOT/name)==d,f'hash drift: {name}'
    role=read(ROOT/'docs/research/drawdown_conditions/data_usage.json')
    protocol=ROOT/'docs/research/drawdown_conditions/risk_preregistration.json'
    assert not role['fresh_oos'] and not role['production_authority']
    rep=read(OUT/'baseline_reproduction/reproduction_result.json')
    assert rep['default_matches_historical'] and rep['matched_development_path_count']==1
    assert rep['availability_audit']['status']=='source_availability_gap'
    assert rep['input']['last_day']<='2025-12-31'
    source_manifest=read(ROOT/'data/manifest.json')
    material=read(OUT/'input_material_receipt.json')
    originals={v['view_id']:v['sha256'] for v in source_manifest['views']}
    for v in material['views']:assert v['source_sha256']==originals[v['view_id']]
    assert rep['input']['source_sha256']==next(v['export_sha256'] for v in material['views'] if v['view_id']=='5m_offset_0')
    previous=None; daily=[]
    for year in range(2021,2026):
        p=OUT/'sessions'/str(year);s=read(p/'sealed_receipt.json');e=read(p/'evidence_receipt.json')
        assert s['year']==year and s['prior_receipt_sha256']==previous
        assert s['analysis_ledger_sha256']==sha(p/'analysis_ledger.json')
        assert s['evidence_receipt_sha256']==sha(p/'evidence_receipt.json')
        assert s['frozen_policy_sha256']==sha(protocol)==e['risk_protocol_sha256']
        assert e['max_input_year']==year and e['parameter_updates']==0
        assert not s['fresh_oos'] and not s['production_authority']
        for name,d in e['source_digests'].items():assert sha(ROOT/name)==d
        for name,d in e['evidence_files'].items():assert sha(p/name)==d
        previous=sha(p/'sealed_receipt.json')
        q=pd.read_csv(p/'daily_accounts.csv.gz');assert set(q.trading_day.str[:4].astype(int))=={year}
        daily.append(q)
    daily=pd.concat(daily,ignore_index=True)
    assert daily.trading_day.max()<='2025-12-31'
    table=pd.read_csv(OUT/'closeout/five_year_metrics.csv')
    for policy in ['baseline','constant_075','constant_050','slow_conflict_half','chop_half']:
        for cost in [0,1,3,5]:
            d=daily[(daily.policy==policy)&(daily.cost_bps==cost)].sort_values('trading_day')
            row=table[(table.view==0)&(table.policy==policy)&(table.cost_bps==cost)].iloc[0]
            np.testing.assert_allclose(d.net_log_pnl.sum(),row.total_log_return,atol=1e-10)
            np.testing.assert_allclose(np.expm1(d.net_log_pnl.sum()/5),row.cagr,atol=1e-10)
            np.testing.assert_allclose(drawdown_summary(d.net_log_pnl.to_numpy(),0)['mdd'],row.daily_mdd,atol=1e-10)
            assert row.daily_mdd<=row.mdd+1e-10
    v=pd.read_csv(OUT/'descriptive/bar_attribution.csv.gz')
    assert v.trading_day.max()<='2025-12-31'
    np.testing.assert_allclose(v[['slow_log_pnl','work_log_pnl','residual_log_pnl']].sum(axis=1),v.pnl_log,atol=1e-12)
    np.testing.assert_allclose(v[['within_previous_bar_log_pnl','overnight_gap_log_pnl','intraday_gap_log_pnl']].sum(axis=1),v.pnl_log,atol=1e-12)
    np.testing.assert_allclose(drawdown_summary(v.pnl_log.to_numpy(),0)['mdd'],abs(rep['observed_fingerprint']['mdd_pct'])/100,atol=1e-10)
    print(json.dumps({'status':'pass','files':len(manifest['files']),'sessions':5,
        'baseline_reproduced':True,'account_and_attribution_identities':True,
        'scientific_status':'infrastructure or measurement gap',
        'conditional_research_progress_retained':True,'fresh_oos':False,'production_authority':False}))
if __name__=='__main__':main()
