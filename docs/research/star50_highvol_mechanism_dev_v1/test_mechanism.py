from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
MOD=Path(__file__).resolve().parent/'run_mechanism.py';s=importlib.util.spec_from_file_location('m',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture():
    n=55;px=100*np.exp(np.arange(n)*0.0002);st=['NormalVol']*n;st[35:]=['HighVol']*(n-35)
    return pd.DataFrame({'session':['s']*n,'minute':np.arange(1,n+1),'year':[2022]*n,'trading_day':['2022-01-04']*n,
                         'open':px,'close':px,'valid':[True]*n,'route_state':st,'recovery_ratio':[1.6]*n})

def test_event_is_causal_transition_and_up_aligned():
    q=m.build_events(fixture());assert len(q)==1
    r=q.iloc[0];assert r.onset_row==35 and r.direction=='up' and r.slow_aligned and r.efficient_high
    assert r.signed_3m_bp>0

def test_tail_shares_bounded():
    r=m.build_events(fixture()).iloc[0]
    assert 0<=r.tail1_share<=1 and 0<=r.tail2_share<=1 and 0<=r.efficiency5<=1+1e-12

def test_agg_count_and_sign():
    q=m.build_events(fixture());rows=m.agg(q,['direction'],'direction')
    r=[x for x in rows if x['horizon_min']==3][0];assert r['n']==1 and r['mean_signed_bp']>0

def test_bootstrap_small_cell_does_not_invent_ci():
    q=m.build_events(fixture());b=m.bootstrap(q,np.ones(len(q),dtype=bool),3,draws=100,seed=7)
    assert b['n']==1 and np.isnan(b['ci_low'])
