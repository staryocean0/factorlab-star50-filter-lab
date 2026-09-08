from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve()
MOD=HERE.parents[1]/"code"/"run_frequency_economics.py"
spec=importlib.util.spec_from_file_location("freq",MOD); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def test_state_initial_unsafe_then_ratio():
    r=np.ones(20,float)
    assert m.state_at_lag(r,5,0,1.0)[0]=="Unsafe"
    st,ratio=m.state_at_lag(r,5,5,1.0)
    assert st=="Recovering" and abs(ratio-1.0)<1e-12
    st,ratio=m.state_at_lag(r*2,5,5,1.0)
    assert st=="Unsafe" and ratio>=1.5


def test_signal_continuation_and_reversal():
    r=np.array([1.,2.,-1.,4.])
    assert m.signed_signal(r,3,2,"continuation")==1
    assert m.signed_signal(r,3,2,"reversal")==-1


def test_turnover_and_gate_accounting():
    z=pd.DataFrame({
        "lag":[0,1,2],"state":["Unsafe","Unsafe","Recovering"],
        "next_return_bp":[2.,-1.,5.],"sig_cont_1":[1,-1,1]
    })
    # Unsafe policy: 0->+1 (1), +1->-1 (2), -1->0 (1); gross=2+1
    q=m.simulate_event(z,1,"continuation","Unsafe")
    assert q["gross_bp"]==3.0
    assert q["one_way_turnover"]==4.0
    assert q["exposure_minutes"]==2


def test_reversal_is_opposite_gross_with_same_turnover():
    z=pd.DataFrame({
        "lag":[0,1],"state":["Unsafe","Unsafe"],
        "next_return_bp":[2.,3.],"sig_cont_1":[1,1]
    })
    a=m.simulate_event(z,1,"continuation","Unsafe")
    b=m.simulate_event(z,1,"reversal","Unsafe")
    assert a["gross_bp"]==-b["gross_bp"]
    assert a["one_way_turnover"]==b["one_way_turnover"]


def test_summary_break_even_and_cost():
    ev=pd.DataFrame([
        {"key":"a","symbol":"X","year":2025,"state":"Unsafe","rule":"continuation","lookback_min":1,"gross_bp":10.,"one_way_turnover":5.,"exposure_minutes":4,"active_returns":4,"winning_minutes":3},
    ])
    q=m.summarize_strategy(ev,["symbol","year","state","rule","lookback_min"]).iloc[0]
    assert abs(q.break_even_one_way_cost_bp-2.0)<1e-12
    assert abs(q["net_bp_cost_2"]-0.0)<1e-12
