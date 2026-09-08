from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

MOD=Path(__file__).resolve().parent/"run_onset_path.py"
spec=importlib.util.spec_from_file_location("o",MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def minute_fixture(states, closes=None):
    n=len(states)
    if closes is None: closes=100*np.exp(np.arange(n)*0.001)
    return pd.DataFrame({"symbol":["X"]*n,"year":[2022]*n,"trading_day":["2022-01-04"]*n,"session":["2022-01-04/0"]*n,
        "minute":np.arange(1,n+1),"open":np.asarray(closes,float),"close":np.asarray(closes,float),"valid":[True]*n,"route_state":states})


def test_only_normal_to_high_is_onset():
    states=["Unknown"]*6+["HighVol","HighVol","NormalVol","HighVol","HighVol"]
    z=minute_fixture(states)
    q=m.build_onsets(z)
    assert len(q)==1
    assert int(q.iloc[0].onset_minute)==10


def test_efficiency_is_bounded_and_direction_matches_net():
    # enough history followed by Normal->High at final row
    closes=100*np.exp(np.cumsum([0,.001,.001,-.001,.002,.001,.001,.001,.001,.001])/1.0)
    states=["NormalVol"]*9+["HighVol"]
    z=minute_fixture(states,closes)
    q=m.build_onsets(z)
    assert len(q)==1
    e=q.iloc[0]
    assert 0<=e.eff5<=1
    assert e.sign5==1


def test_trade_enters_next_open_and_exits_after_hold():
    n=15;states=["NormalVol"]*9+["HighVol"]*6
    z=minute_fixture(states)
    on=m.build_onsets(z)
    tr=m.candidate_trade_rows(z,on,"momentum",0.0,2)
    assert len(tr)==1
    x=tr.iloc[0]
    assert x.entry_minute==11 and x.exit_minute==13
    assert abs(x.gross_bp-20.0)<1e-8


def test_efficiency_gate_filters_candidate():
    # zigzag path gives low efficiency
    r=[0,0.001,-0.001,0.001,-0.001,0.0002,0.001,0.001,0.001,0.001]
    closes=100*np.exp(np.cumsum(r))
    states=["NormalVol"]*9+["HighVol"]+["HighVol"]*4
    z=minute_fixture(states,closes)
    on=m.build_onsets(z)
    assert len(on)==1
    assert len(m.candidate_trade_rows(z,on,"momentum",0.8,1))==0
    assert len(m.candidate_trade_rows(z,on,"reversal",0.6,1))==1


def test_invalid_future_path_rejects_trade():
    n=15;states=["NormalVol"]*9+["HighVol"]*6
    z=minute_fixture(states);z.loc[11,"valid"]=False
    on=m.build_onsets(z)
    tr=m.candidate_trade_rows(z,on,"momentum",0.0,3)
    assert len(tr)==0


def test_cost_is_two_legs_per_completed_trade():
    tr=pd.DataFrame({"year":[2022,2022],"gross_bp":[5.,7.]})
    q=m.summarize(tr,"X",2022,"momentum",0.0,3)
    assert q["trades"]==2 and q["one_way_turnover"]==4
    assert abs(q["net_bp_cost_1"]-8.0)<1e-12
    assert abs(q["break_even_one_way_cost_bp"]-3.0)<1e-12
