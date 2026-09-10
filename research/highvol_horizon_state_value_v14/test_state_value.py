from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

HERE=Path(__file__).resolve().parent
RUNNER=HERE/'run_state_value.py'


def load_runner():
    spec=importlib.util.spec_from_file_location('v14',RUNNER)
    assert spec is not None and spec.loader is not None
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def test_frozen_dimensions():
    m=load_runner()
    assert m.DEV_YEARS==(2021,2022,2023)
    assert m.HORIZONS==(15,30,60)
    assert m.STATES==('UNSAFE','RECOVERING')
    assert m.BUCKETS==('LT15','M15_25','M30_40','GE45')
    assert m.MIN_TRAIN_CELL_N==50


def test_smoothing_beta11():
    m=load_runner()
    assert m.smooth_prob(pd.Series([0,0,0]))==1/5
    assert m.smooth_prob(pd.Series([1,1,0]))==3/5


def test_state_age_model_is_strict_refinement_of_age_model_keys():
    m=load_runner()
    rows=[]
    for state in m.STATES:
        for bucket in m.BUCKETS:
            for y in [0,1,0,1]:
                rows.append({'current_state':state,'age_bucket':bucket,'normal_within_15m':y})
    df=pd.DataFrame(rows)
    age,_=m.fit_age_only(df,15)
    sa,ns=m.fit_state_age(df,15)
    assert set(age)==set(m.BUCKETS)
    assert set(sa)=={(s,b) for s in m.STATES for b in m.BUCKETS}
    assert min(ns.values())==4
