from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

MOD=Path(__file__).resolve().parents[1]/"code"/"run_fee_admission.py"
spec=importlib.util.spec_from_file_location("fee",MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_admission_does_not_exit_on_recovering_if_signal_same():
    sig=np.ones(5);st=np.array(["Unsafe","Recovering","Recovering","Recovering","Recovering"],object);v=np.ones(5,bool)
    hard=m.decision_targets(sig,st,v,"hard_gate")
    adm=m.decision_targets(sig,st,v,"admission_gate")
    assert np.array_equal(hard,[1,0,0,0,0])
    assert np.array_equal(adm,[1,1,1,1,1])


def test_admission_closes_flip_outside_unsafe_and_waits_to_reenter():
    sig=np.array([1,1,-1,-1,-1],float)
    st=np.array(["Unsafe","Recovering","Recovering","Recovering","Unsafe"],object)
    q=m.decision_targets(sig,st,np.ones(5,bool),"admission_gate")
    assert np.array_equal(q,[1,1,0,0,-1])


def test_two_bar_delay_and_open_close_fee_floor():
    op=np.exp(np.arange(5)*0.001)
    q=m.simulate_valid_run(op,np.ones(5),np.array(["Unsafe"]*5,object),"hard_gate")
    assert q["exposure_bars"]==3
    assert abs(q["gross_bp"]-30.0)<1e-8
    assert q["open_legs"]==1 and q["close_legs"]==1 and q["execution_legs"]==2
    assert abs(q["exchange_fee_bp"]-(m.OPEN_FEE_BP+m.SAME_DAY_CLOSE_FEE_BP))<1e-12
    assert q["one_way_turnover"]==2.0


def test_reversal_charges_close_plus_new_open_and_final_close():
    ep=np.array([0,0,1,1,-1,-1],float)
    q=m.transition_fees(ep)
    assert q["open_legs"]==2
    assert q["close_legs"]==2
    assert q["reversal_execs"]==1
    assert q["execution_legs"]==4
    assert abs(q["exchange_fee_bp"]-(2*m.OPEN_FEE_BP+2*m.SAME_DAY_CLOSE_FEE_BP))<1e-12
    assert q["one_way_turnover"]==4.0


def test_invalid_strategy_input_flattens_admission_target():
    sig=np.array([1,1,1,1],float);st=np.array(["Unsafe","Recovering","Recovering","Recovering"],object)
    v=np.array([True,True,False,True])
    q=m.decision_targets(sig,st,v,"admission_gate")
    assert np.array_equal(q,[1,1,0,0])


def test_no_cross_lunch_return_is_booked():
    bars=pd.DataFrame({
        "session":["2025-01-02/0"]*4+["2025-01-02/1"]*4,
        "year":[2025]*8,
        "open":[1.0,1.01,1.02,1.03,100.0,100.0,100.0,100.0],
        "valid":[True]*8,
        "route_state":["Unsafe"]*8,
    })
    r=m.session_policy_rows(bars,np.ones(8))
    expected=np.log(1.03/1.01)*1e4
    # Morning books only its two post-latency returns; afternoon is flat-price.
    # For each policy the two half-sessions together must exclude the 1.03 -> 100 lunch jump.
    for policy,z in r.groupby("policy"):
        assert abs(z.gross_bp.sum()-expected)<1e-8, policy
        assert abs(z.loc[z.session.str.endswith("/1"),"gross_bp"].iloc[0])<1e-12


def test_extra_friction_is_per_execution_leg():
    op=np.exp(np.arange(5)*0.001)
    q=m.simulate_valid_run(op,np.ones(5),np.array(["Unsafe"]*5,object),"hard_gate")
    assert abs(q["net_extra_0.25_bp"]-(q["net_exchange_bp"]-.25*q["execution_legs"]))<1e-12
