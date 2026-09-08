from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
MOD=Path(__file__).resolve().parent/'run_stop_dev.py';s=importlib.util.spec_from_file_location('m',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture(closes):
    n=12;op=np.full(n,100.0);op[6]=99.;op[7]=98.;op[8]=97.
    z=pd.DataFrame({'session':['s']*n,'minute':np.arange(1,n+1),'open':op,'close':np.array([100.]*n),'valid':[True]*n})
    z.loc[5,'open']=100.;z.loc[5,'close']=closes[0];z.loc[6,'close']=closes[1]
    e=pd.DataFrame([{'year':2022,'trading_day':'2022-01-04','session':'s','onset_row':4}])
    return z,e

def test_first_minute_stop_exits_next_open():
    z,e=fixture([99.95,99.0]);q=m.simulate(z,e,2).iloc[0]
    assert q.stopped and q.stop_after_min==1 and q.holding_min==1
    assert abs(q.gross_bp-np.log(99/100)*1e4)<1e-10

def test_second_minute_stop_exits_second_next_open():
    z,e=fixture([100.0,99.95]);q=m.simulate(z,e,2).iloc[0]
    assert q.stopped and q.stop_after_min==2 and q.holding_min==2
    assert abs(q.gross_bp-np.log(98/100)*1e4)<1e-10

def test_no_stop_keeps_three_minutes():
    z,e=fixture([100.,100.]);q=m.simulate(z,e,None).iloc[0]
    assert not q.stopped and q.holding_min==3
    assert abs(q.gross_bp-np.log(97/100)*1e4)<1e-10

def test_metrics_cost_two_legs():
    z=pd.DataFrame({'gross_bp':[4.,2.],'stopped':[False,True],'holding_min':[3,1]})
    q=m.metrics(z);assert abs(q['mean_net1_bp']-1)<1e-12 and q['stops']==1
