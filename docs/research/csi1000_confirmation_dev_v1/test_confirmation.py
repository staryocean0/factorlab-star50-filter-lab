from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
MOD=Path(__file__).resolve().parent/'run_confirmation.py';s=importlib.util.spec_from_file_location('m',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture():
 n=20;cl=100*np.exp(np.arange(n)*.001);z=pd.DataFrame({'symbol':['000852.SH']*n,'year':[2022]*n,'trading_day':['2022-01-04']*n,'session':['2022-01-04/0']*n,'minute':np.arange(1,n+1),'open':cl,'close':cl,'valid':[True]*n,'route_state':['NormalVol']*5+['HighVol']*(n-5),'recovery_ratio':[1.8]*n});e=pd.DataFrame([{'year':2022,'trading_day':'2022-01-04','session':'2022-01-04/0','onset_row':5,'onset_minute':6,'slow30_net_bp':1.,'tail2_share':.7,'tail1_share':.4}]);return z,e

def test_wait1_requires_persistent_highvol():
 z,e=fixture();q=m.policy_trades(z,e,'wait1_persist');assert len(q)==1
 z.loc[6,'route_state']='NormalVol';assert len(m.policy_trades(z,e,'wait1_persist'))==0

def test_positive_confirmation_rejects_retrace():
 z,e=fixture();z.loc[6,'close']=z.loc[5,'close']*.999;assert len(m.policy_trades(z,e,'wait1_persist_positive'))==0

def test_two_leg_cost_math():
 q=m.metrics(pd.DataFrame({'gross_bp':[4.,2.]}));assert q['trades']==2 and abs(q['mean_net1_bp']-1)<1e-12 and abs(q['one_way_break_even_bp']-1.5)<1e-12
