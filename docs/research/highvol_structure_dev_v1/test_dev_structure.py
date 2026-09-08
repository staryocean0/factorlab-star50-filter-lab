from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

MOD=Path(__file__).resolve().parent/"run_dev_structure.py"
spec=importlib.util.spec_from_file_location("s",MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(future_shift=0.0):
    n=25
    r=np.array([0,.0002,-.0001,.0001,.0002,.0003,.0001,.0002,.0001,.0002,.0004,.0005,.0006,.0007,.0008]+[.0002]*10,float)
    close=100*np.exp(np.cumsum(r))
    op=close.copy()
    if future_shift:
        op[16:]+=future_shift
    states=["NormalVol"]*14+["HighVol"]*11
    return pd.DataFrame({"symbol":["X"]*n,"year":[2022]*n,"trading_day":["2022-01-04"]*n,"session":["2022-01-04/0"]*n,
        "minute":np.arange(1,n+1),"open":op,"close":close,"valid":[True]*n,"route_state":states,"recovery_ratio":[1.0]*14+[1.6]*11})


def test_only_normal_to_high_event():
    q=m.build_event_rows(fixture())
    assert len(q)==1
    assert int(q.iloc[0].onset_minute)==15


def test_features_are_prefix_causal():
    a=m.build_event_rows(fixture(0.0)).iloc[0]
    b=m.build_event_rows(fixture(10.0)).iloc[0]
    keys=["vol_ratio","net5_bp","sign5","eff5","sign_agreement5","tail1_share","tail2_share","accel_abs_2v3","prior5_net_bp","prior5_eff","prior5_same_direction"]
    for k in keys:
        assert a[k]==b[k]


def test_future_outcome_uses_next_open():
    q=m.build_event_rows(fixture()).iloc[0]
    z=fixture()
    # onset row 14 (zero based); next open row 15, 1m exit row 16
    expected=np.log(z.open.iloc[16]/z.open.iloc[15])*1e4
    assert abs(q["cont_1m_bp"]-expected)<1e-10


def test_invalid_future_path_stays_missing():
    z=fixture();z.loc[16,"valid"]=False
    q=m.build_event_rows(z).iloc[0]
    assert np.isnan(q["cont_1m_bp"])


def test_no_validation_year_is_needed_for_event_builder():
    z=fixture();q=m.build_event_rows(z)
    assert set(q.year)=={2022}
