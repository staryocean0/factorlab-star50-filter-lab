from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

MOD=Path(__file__).resolve().parent/"run_direction.py"
spec=importlib.util.spec_from_file_location("d",MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_momentum_and_reversal_are_opposites_on_valid_path():
    x=pd.DataFrame({"session":["d/0"]*6,"close":[100,101,102,101,100,99],"valid":[True]*6})
    mom=m.signals_for_lookback(x,1,"momentum")
    rev=m.signals_for_lookback(x,1,"reversal")
    assert np.array_equal(mom,-rev)
    assert mom.tolist()==[0,1,1,-1,-1,-1]


def test_lookback_does_not_cross_invalid_gap():
    x=pd.DataFrame({"session":["d/0"]*5,"close":[100,101,102,103,104],"valid":[True,True,False,True,True]})
    s=m.signals_for_lookback(x,2,"momentum")
    assert s.tolist()==[0,0,0,0,0]


def test_delay_one_books_only_future_open_to_open_return():
    minute=pd.DataFrame({"session":["d/0"]*5,"open":np.exp(np.arange(5)*0.001),"valid":[True]*5,"route_state":["HighVol"]*5})
    sig=np.ones(5)
    q=m.simulate(minute,sig,"HighVol",1)
    # Decisions 0,1,2 become positions on intervals 1->2, 2->3, 3->4: 3 * 10bp.
    assert q["exposure_minutes"]==3
    assert abs(q["gross_bp"]-30.0)<1e-8
    assert q["one_way_turnover"]==2.0


def test_delay_two_books_two_future_intervals():
    minute=pd.DataFrame({"session":["d/0"]*5,"open":np.exp(np.arange(5)*0.001),"valid":[True]*5,"route_state":["HighVol"]*5})
    q=m.simulate(minute,np.ones(5),"HighVol",2)
    assert q["exposure_minutes"]==2
    assert abs(q["gross_bp"]-20.0)<1e-8


def test_gate_uses_decision_state_not_future_state():
    minute=pd.DataFrame({"session":["d/0"]*5,"open":np.exp(np.arange(5)*0.001),"valid":[True]*5,"route_state":["HighVol","NormalVol","NormalVol","NormalVol","NormalVol"]})
    q=m.simulate(minute,np.ones(5),"HighVol",1)
    # Only decision 0 is admitted, then appears on interval starting at open1.
    assert q["exposure_minutes"]==1
    assert abs(q["gross_bp"]-10.0)<1e-8


def test_session_boundary_never_books_lunch_gap():
    minute=pd.DataFrame({"session":["d/0"]*4+["d/1"]*4,"open":[1,1.01,1.02,1.03,100,100,100,100],"valid":[True]*8,"route_state":["HighVol"]*8})
    q=m.simulate(minute,np.ones(8),"HighVol",1)
    assert q["gross_bp"] < 1000  # giant lunch gap is not booked
