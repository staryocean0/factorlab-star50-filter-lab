"""One frozen family, baseline review before family, actual BBO account paths."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
import shutil
from pathlib import Path
import sys

import duckdb
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
HUB=Path('/home/starryocean/桌面/量化/unified_datahub')
sys.path[:0]=[str(ROOT/'src'),str(HUB/'src')]
from star50_filter.bbo_bucket_account import Account,Book,POLICIES,calibrated_cutoffs,veto_matrix
from datahub.core.services.star50_history_bbo.service import Star50HistoryBboService

DOC=ROOT/'docs/research/conditional_bucket_v1'
OUT=ROOT/'artifacts/conditional_bucket_accounts_v1p3'
BINDING=DOC/'datahub_binding_v1.json'
PANEL=ROOT/'artifacts/conditional_bucket_v1_preflight/causal_measurement_panel.parquet'
ENTRIES=ROOT/'artifacts/conditional_bucket_v1_preflight/entry_measurements.parquet'
SOURCE_PATHS=['src/star50_filter/bbo_bucket_account.py','src/star50_filter/conditional_bucket_measurements.py',
 'scripts/run_conditional_bucket_accounts_v1.py','tests/test_bbo_bucket_account.py',
 'docs/research/conditional_bucket_v1/campaign_v1.json','docs/research/conditional_bucket_v1/datahub_binding_v1.json']


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')


def check():
    j=json.loads((OUT/'source_freeze.json').read_text())
    for p,h in j['sources'].items():assert sha(ROOT/p)==h,p
    assert sha(PANEL)==j['panel_sha256'] and sha(ENTRIES)==j['entries_sha256']
    return j


def freeze():
    assert not OUT.exists()
    OUT.mkdir()
    e=pd.read_parquet(ENTRIES)
    cut=calibrated_cutoffs(e)
    save(OUT/'source_freeze.json',{'sources':{p:sha(ROOT/p) for p in SOURCE_PATHS},
        'panel_sha256':sha(PANEL),'entries_sha256':sha(ENTRIES),'cutoffs':cut,
        'calibration_years':[2021,2022,2023],'primary_economic_year':2025,
        'primary_accounts':['588000_spot','588000_option'],
        'secondary_account':'588080_spot_with_dividend',
        'blocked_account':'588080_option_historical_terms_precede_official_2025_10_17_adjustment',
        'new_policy_candidates':5,'fresh_oos':False,'production_authority':False})
    f=pd.read_parquet(PANEL)
    f['time']=pd.to_datetime(f.timestamp.str[:19]).dt.tz_localize('Asia/Shanghai').astype('datetime64[ns, Asia/Shanghai]')
    v=veto_matrix(f,cut)
    for policy in POLICIES:
        blocked=v[policy].where(f.original_entry_event).ffill().fillna(False)
        f[policy]=np.where(blocked,0,f.frozen_signal).astype(int)
    f['entry_signal_time']=f.time.where(f.original_entry_event).ffill()
    f=f.loc[f.trading_day>='2024-01-01']
    f.to_parquet(OUT/'frozen_signals.parquet',index=False)
    save(OUT/'science_acceptance.json',{
        'status':'diagnostic_signal_present_account_contract_may_open',
        'scope':'existing causal STAR50 signal and observable condition inputs, not proof of a successful veto',
        'baseline_identity':'LP12_sigma48_ddof0_k1_original',
        'prior_signal_evidence':'streak_mechanism_v1 source-bound exact baseline replay',
        'candidate_economic_success_not_assumed':True,
        'all_entry_inputs_present':bool(e.all_measurements_present.all()),
        'no_REAKA_N30_K_residual_rules_imported':True,
        'input_reads_post2025':0,'production_authority':False})
    print('Frozen family and causal signals',cut)


class DailyMarket:
    def __init__(self):
        self.binding=json.loads(BINDING.read_text())
        self.service=Star50HistoryBboService(repo_root=HUB)
        self.roots={k:Path(v['storage_uri']) for k,v in self.binding.items() if k in ['spot','option']}
        self.manifests={k:json.loads((r/'manifest.json').read_text()) for k,r in self.roots.items()}
        self.files={k:{x['trading_day']:x for x in m['files']} for k,m in self.manifests.items()}
        self.con=duckdb.connect();self.con.execute("SET TimeZone='UTC'");self.con.execute('SET threads=1')

    def read_day(self,day):
        compact=day.replace('-','')
        for k in ['spot','option']:
            grant=self.service.coverage(k,self.binding[k]['dataset_version'])
            assert grant['serving_grant']['dataset_version']==self.binding[k]['dataset_version']
        sp=self.roots['spot']/self.files['spot'][compact]['path']
        op=self.roots['option']/self.files['option'][compact]['path']
        spots={}
        f=self.con.execute('''SELECT instrument_id,
          epoch_ns(market_observed_at AT TIME ZONE 'Asia/Shanghai') t,
          bid_price_x10000_1/10000.0 bid,ask_price_x10000_1/10000.0 ask,
          bid_size_1 bq,ask_size_1 aq,session_phase,
          epoch_ns(valid_until AT TIME ZONE 'Asia/Shanghai') valid_until_ns
          FROM read_parquet(?,hive_partitioning=false)
          ORDER BY instrument_id,market_observed_at,event_seq''',[str(sp)]).fetchdf()
        for symbol,g in f.groupby('instrument_id',sort=False):
            code=symbol[:6]
            seconds=((g.t.to_numpy(np.int64)+8*3600*10**9)%(86400*10**9))/1e9
            # SSE funds trade continuously until 15:00; do not inherit the
            # generic stock close-auction label as the fund execution rule.
            executable=((seconds>=9.5*3600)&(seconds<11.5*3600))|((seconds>=13*3600)&(seconds<15*3600))
            markable=(((seconds>=9.5*3600)&(seconds<=11.5*3600))|((seconds>=13*3600)&(seconds<15*3600+60)))&(g.valid_until_ns.to_numpy()>g.t.to_numpy())
            spots[code]=Book(g.t.to_numpy(np.int64),g.bid.to_numpy(),g.ask.to_numpy(),g.bq.to_numpy(),g.aq.to_numpy(),
                             executable,markable,g.valid_until_ns.to_numpy(np.int64),code=code)
        f=self.con.execute('''SELECT order_book_id,epoch_ns(observation_datetime) t,
          bid_price_1 bid,ask_price_1 ask,bid_volume_1 bq,ask_volume_1 aq,
          session_phase,expiry_date,strike,contract_multiplier,option_type
          FROM read_parquet(?,hive_partitioning=false) WHERE underlying_symbol='588000.XSHG'
          ORDER BY order_book_id,observation_datetime,source_sequence''',[str(op)]).fetchdf()
        options={}
        for code,g in f.groupby('order_book_id',sort=False):
            assert g.contract_multiplier.nunique()==1 and g.strike.nunique()==1
            assert g.contract_multiplier.iloc[0]==10000
            seconds=((g.t.to_numpy(np.int64)+8*3600*10**9)%(86400*10**9))/1e9
            executable=((seconds>=9.5*3600)&(seconds<11.5*3600))|((seconds>=13*3600)&(seconds<14*3600+57*60))
            # Auction indicative zeros are not zero asset values. A positive
            # observed closing book can value inventory, but cannot execute it.
            markable=executable|((seconds>=15*3600)&(seconds<15*3600+60))
            options[str(code)]=Book(g.t.to_numpy(np.int64),g.bid.to_numpy(),g.ask.to_numpy(),g.bq.to_numpy(),g.aq.to_numpy(),
                executable,markable,code=str(code),expiry=str(g.expiry_date.iloc[0])[:10],
                strike=float(g.strike.iloc[0]),multiplier=10000.,option_type=str(g.option_type.iloc[0]))
        return spots,options


def write_accounts(folder,accounts):
    rows=[]
    for a in accounts:
        key=f'{a.underlying}_{a.carrier}_{a.policy}';p=folder/key;p.mkdir(parents=True,exist_ok=True)
        for name,records in [('trades',a.trades),('orders',a.orders),('marks',a.marks),('drawdown_segments',a.segments),('incidents',a.incidents)]:
            pd.DataFrame(records).to_parquet(p/(name+'.parquet'),index=False)
        rows.append(a.summary())
    pd.DataFrame(rows).to_csv(folder/'summary.csv',index=False)
    return rows


def execute(mode,stop_day=None):
    check()
    if mode=='family':assert (OUT/'baseline_review.json').exists(),'Controller baseline review required'
    folder=OUT/(mode+'_smoke_'+stop_day if stop_day else mode)
    assert not folder.exists()
    folder.mkdir()
    policies=('baseline',) if mode=='baseline' else POLICIES
    accounts=[Account(p,c,u) for p in policies for c,u in [('spot','588000'),('option','588000'),('spot','588080')]]
    if mode=='baseline' and stop_day is None:
        accounts=[a for a in accounts if a.carrier=='option']
    market=DailyMarket()
    signals=pd.read_parquet(OUT/'frozen_signals.parquet').sort_values('time')
    times=signals.time.astype('int64').to_numpy()
    days=sorted(signals.loc[signals.trading_day.str.startswith('2025'),'trading_day'].unique())
    if stop_day:days=[d for d in days if d<=stop_day]
    primary_prices=[]
    for n,day in enumerate(days):
        spots,options=market.read_day(day)
        daily=signals.loc[signals.trading_day==day]
        points=sorted(set(daily.time.tolist()+[pd.Timestamp(day+' 09:30',tz='Asia/Shanghai'),pd.Timestamp(day+' 13:00',tz='Asia/Shanghai')]))
        if day=='2025-10-17':
            for a in accounts:
                if a.underlying=='588080' and a.carrier=='spot' and a.quantity:
                    amount=.014*a.quantity;a.receivable+=amount;a.holding_dividend+=amount
        if day=='2025-10-22':
            for a in accounts:
                if a.underlying=='588080':a.cash+=a.receivable;a.receivable=0.
        for j,point in enumerate(points):
            t=int(point.value);row=signals.iloc[int(np.searchsorted(times,t,side='right'))-1]
            assert int(row.time.value) <= t, 'Future signal row selected'
            before=int(points[j+1].value) if j+1<len(points) else int(pd.Timestamp(day+' 15:01',tz='Asia/Shanghai').value)
            for a in accounts:
                books=options if a.carrier=='option' else {a.underlying:spots[a.underlying]}
                a.step(books,spots[a.underlying],int(row[a.policy]),t+1000000,before,day,point.strftime('%H:%M'),int(row.entry_signal_time.value))
                a.mark_to(books,before-1)
                a.marks.append({'time_ns':before-1,'day':day,'cash':a.cash,'receivable':a.receivable,
                    'holding':a.holding,'quantity':a.quantity,'bid':a.last_bid,'multiplier':a.multiplier,
                    'nav':a.nav,'running_mdd':a.mdd,'fees':a.fees,'bid_observed_ns':a.last_bid_ns})
        for a in accounts:
            books=options if a.carrier=='option' else {a.underlying:spots[a.underlying]}
            closing_ns=int(pd.Timestamp(day+' 15:01',tz='Asia/Shanghai').value)
            a.end_day(books,spots[a.underlying],day,closing_ns)
            if a.carrier=='option':
                a.marks.append({'time_ns':closing_ns,'day':day,'cash':a.cash,'receivable':a.receivable,
                    'holding':a.holding,'quantity':a.quantity,'bid':a.last_bid,'multiplier':a.multiplier,
                    'nav':a.nav,'running_mdd':a.mdd,'fees':a.fees,'bid_observed_ns':a.last_bid_ns})
        if n%30==0 or n==len(days)-1:
            print(mode,day,n+1,'/',len(days),flush=True)
    market.con.close()
    rows=write_accounts(folder,accounts)
    if mode=='baseline' and stop_day is None:
        parent=ROOT/'artifacts/conditional_bucket_accounts_v1p2/baseline'
        cached=pd.read_csv(parent/'summary.csv').query("carrier == 'spot'")
        for underlying in ['588000','588080']:
            key=f'{underlying}_spot_baseline'
            shutil.copytree(parent/key,folder/key)
        merged=pd.concat([pd.DataFrame(rows),cached],ignore_index=True)
        merged.to_csv(folder/'summary.csv',index=False)
        save(folder/'spot_baseline_reuse.json',{'source':str(parent),'reason':'only option expiry lifecycle changed; ETF baseline retained and will be independently replayed in family command',
            'summary_sha256':sha(parent/'summary.csv')})
    save(folder/'run_receipt.json',{'mode':mode,'start':days[0],'end':days[-1],
        'days':len(days),'accounts':len(accounts),'source_freeze_sha256':sha(OUT/'source_freeze.json'),
        'complete_2025':stop_day is None,'data_2026_used':False,'new_positions_search':False})
    print(pd.DataFrame(rows).to_string(index=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','baseline','family']);p.add_argument('--stop-day');a=p.parse_args()
    if a.action=='freeze':freeze()
    else:execute(a.action,a.stop_day)
