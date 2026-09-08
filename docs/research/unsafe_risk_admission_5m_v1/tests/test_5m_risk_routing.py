from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

MOD=Path(__file__).resolve().parents[1]/"code"/"run_5m_risk_routing.py"
spec=importlib.util.spec_from_file_location("r",MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_baseline_ignores_state_but_respects_validity():
    sig=np.array([1,-1,1,1],float);st=np.array(["Unsafe","Unknown","Recovering","NoEpisode"],object)
    q=m.decision_targets(sig,st,np.array([True,True,False,True]),"baseline_ungated")
    assert np.array_equal(q,[1,-1,0,1])


def test_hard_off_admits_only_noepisode_and_recovering():
    sig=np.ones(4);st=np.array(["NoEpisode","Recovering","Unsafe","Unknown"],object)
    q=m.decision_targets(sig,st,np.ones(4,bool),"unsafe_hard_off")
    assert np.array_equal(q,[1,1,0,0])


def test_entry_block_holds_same_direction_through_unsafe():
    sig=np.ones(5);st=np.array(["NoEpisode","Unsafe","Unsafe","Recovering","Unsafe"],object)
    q=m.decision_targets(sig,st,np.ones(5,bool),"unsafe_entry_block")
    assert np.array_equal(q,[1,1,1,1,1])


def test_entry_block_closes_flip_in_unsafe_and_waits_to_reenter():
    sig=np.array([1,1,-1,-1,-1],float);st=np.array(["NoEpisode","Unsafe","Unsafe","Unsafe","Recovering"],object)
    q=m.decision_targets(sig,st,np.ones(5,bool),"unsafe_entry_block")
    assert np.array_equal(q,[1,1,0,0,-1])


def test_unknown_forces_flat_even_entry_block():
    sig=np.ones(4);st=np.array(["NoEpisode","Unsafe","Unknown","Recovering"],object)
    q=m.decision_targets(sig,st,np.ones(4,bool),"unsafe_entry_block")
    assert np.array_equal(q,[1,1,0,1])


def test_two_bar_delay_and_forced_flat_turnover():
    op=np.exp(np.arange(5)*0.001);target=np.ones(5)
    q=m.simulate_valid_run(op,target)
    assert q["exposure_bars"]==3
    assert abs(q["gross_bp"]-30.0)<1e-8
    assert q["one_way_turnover"]==2.0


def test_session_rows_do_not_book_lunch_jump():
    bars=pd.DataFrame({
        "trading_day":["2025-01-02"]*8,
        "session":["2025-01-02/0"]*4+["2025-01-02/1"]*4,
        "year":[2025]*8,
        "open":[1.0,1.01,1.02,1.03,100.0,100.0,100.0,100.0],
        "valid":[True]*8,
        "route_state":["NoEpisode"]*8,
    })
    r=m.session_rows(bars,np.ones(8),"X")
    expected=np.log(1.03/1.01)*1e4
    for policy,z in r.groupby("policy"):
        assert abs(z.gross_bp.sum()-expected)<1e-8, policy
        assert abs(z.loc[z.session.str.endswith("/1"),"gross_bp"].iloc[0])<1e-12


def test_cost_is_symmetric_one_way_turnover():
    rows=pd.DataFrame([{"symbol":"X","year":2025,"policy":"baseline_ungated","gross_bp":10.,"one_way_turnover":4.,
                        "exposure_bars":2,"exposure_minutes":10,"booked_returns":2,"winning_returns":1,"session":"s"}])
    q=m.aggregate(rows,["symbol","policy"]).iloc[0]
    assert q["net_cost_0.5_bp"]==8.0
    assert q["net_cost_1_bp"]==6.0
    assert q["net_cost_2_bp"]==2.0
