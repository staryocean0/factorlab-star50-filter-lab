from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
MOD=Path(__file__).resolve().parent/'run_hold_path.py';s=importlib.util.spec_from_file_location('m',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture():
    n=12
    op=100*np.exp(np.arange(n)*0.001)
    z=pd.DataFrame({'session':['s']*n,'minute':np.arange(1,n+1),'open':op,'high':op*1.001,'low':op*.999,'valid':[True]*n,'route_state':['HighVol']*n})
    e=pd.DataFrame([{'role':'Development','year':2022,'trading_day':'2022-01-04','session':'s','onset_row':4,'onset_minute':5,'gross_3m_bp':30.0}])
    return z,e

def test_decomposition_reproduces_three_minute_gross():
    z,e=fixture();q=m.path_rows(z,e).iloc[0]
    assert abs(q.minute1_bp-10)<1e-10 and abs(q.minute2_bp-10)<1e-10 and abs(q.minute3_bp-10)<1e-10
    assert abs(q.cum3_bp-30)<1e-10
    assert q.entry_minute==6 and q.exit_minute==9

def test_mfe_mae_use_held_bars_only():
    z,e=fixture();q=m.path_rows(z,e).iloc[0]
    en=5
    exp_mfe=np.log(z.high.iloc[en:en+3].max()/z.open.iloc[en])*1e4
    exp_mae=np.log(z.low.iloc[en:en+3].min()/z.open.iloc[en])*1e4
    assert abs(q.mfe_bp-exp_mfe)<1e-10 and abs(q.mae_bp-exp_mae)<1e-10

def test_summary_exit_cost_is_two_legs():
    z,e=fixture();q=m.path_rows(z,e);s=m.summarize(q,'Development','pooled')
    assert abs(s['mean_net1bp_1m_exit']-(10-2))<1e-10
    assert abs(s['mean_net1bp_3m_exit']-(30-2))<1e-10

def test_bootstrap_deterministic():
    q=pd.DataFrame({'role':['Development']*4,'trading_day':['a','a','b','b'],'minute2_bp':[1.,2.,3.,4.]})
    a=m.bootstrap_contribution(q,'Development','minute2_bp',draws=200,seed=7);b=m.bootstrap_contribution(q,'Development','minute2_bp',draws=200,seed=7)
    assert a==b and a['days']==2
