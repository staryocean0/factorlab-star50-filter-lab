from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd
MOD=Path(__file__).resolve().parent/'run_delay_decay.py';s=importlib.util.spec_from_file_location('m',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture():
    n=20
    z=pd.DataFrame({'symbol':['000852.SH']*n,'year':[2022]*n,'trading_day':['2022-01-04']*n,'session':['2022-01-04/0']*n,'minute':np.arange(1,n+1),'open':100*np.exp(np.arange(n)*.001),'valid':[True]*n,'route_state':['HighVol']*n,'recovery_ratio':[1.8]*n})
    e=pd.DataFrame([{'trading_day':'2022-01-04','year':2022,'session':'2022-01-04/0','onset_row':5,'onset_minute':6,'gross_3m_bp':30.0}])
    return z,e

def test_delay_entry_clock_and_same_hold():
    z,e=fixture();q=m.build_delay_rows(z,e)
    assert list(q.delay_min)==[0,1,2,3,5]
    assert int(q[q.delay_min==0].entry_minute.iloc[0])==7
    assert int(q[q.delay_min==0].exit_minute.iloc[0])==10
    assert int(q[q.delay_min==5].entry_minute.iloc[0])==12
    assert int(q[q.delay_min==5].exit_minute.iloc[0])==15
    assert np.allclose(q.gross_bp.dropna(),30.0)

def test_invalid_delayed_path_is_missing_not_candidate_drop():
    z,e=fixture();z.loc[12,'valid']=False
    q=m.build_delay_rows(z,e)
    assert len(q)==5
    assert np.isfinite(q[q.delay_min==0].gross_bp.iloc[0])
    assert np.isnan(q[q.delay_min==3].gross_bp.iloc[0])

def test_pair_difference_sign():
    rows=pd.DataFrame({'candidate_id':[0,0,1,1],'trading_day':['2022-01-04','2022-01-04','2022-01-05','2022-01-05'],'year':[2022]*4,'role':['Development']*4,'delay_min':[0,1,0,1],'gross_bp':[4.,1.,2.,3.]})
    p,w=m.paired(rows);x=p[(p.role=='Development')&(p.delay_min==1)].iloc[0]
    assert x['pairs']==2 and abs(x['mean_delay_minus_immediate_bp']+1.0)<1e-12

def test_bootstrap_deterministic():
    w=pd.DataFrame({'candidate_id':[0,1],'trading_day':['2022-01-04','2022-01-05'],'year':[2022,2022],'role':['Development','Development'],0:[2.,4.],1:[1.,5.]})
    a=m.bootstrap(w,'Development',1,draws=100,seed=7);b=m.bootstrap(w,'Development',1,draws=100,seed=7)
    assert a==b and a['candidate_days']==2
