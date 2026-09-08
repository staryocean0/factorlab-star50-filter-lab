from __future__ import annotations
import importlib.util
from pathlib import Path
import pandas as pd
MOD=Path(__file__).resolve().parent/'run_dev.py';s=importlib.util.spec_from_file_location('m',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture():
    return pd.DataFrame([
      {'session':'s','onset_row':10,'direction':'down','slow_aligned':False,'accel_high':False,'efficient_high':True,'signed_5m_bp':4.,'year':2022},
      {'session':'s','onset_row':12,'direction':'down','slow_aligned':False,'accel_high':False,'efficient_high':True,'signed_5m_bp':5.,'year':2022},
      {'session':'s','onset_row':17,'direction':'down','slow_aligned':False,'accel_high':False,'efficient_high':True,'signed_5m_bp':3.,'year':2022},
      {'session':'s','onset_row':30,'direction':'up','slow_aligned':False,'accel_high':False,'efficient_high':True,'signed_5m_bp':9.,'year':2022},
      {'session':'s','onset_row':40,'direction':'down','slow_aligned':True,'accel_high':False,'efficient_high':True,'signed_5m_bp':9.,'year':2022},
    ])

def test_candidate_filters_and_nonoverlap():
    q=m.select(fixture())
    assert list(q.onset_row)==[10,17]

def test_short_signed_return_is_gross():
    q=m.select(fixture());assert list(q.gross_bp)==[4.,3.]

def test_cost_math_two_legs():
    q=m.metrics(pd.DataFrame({'gross_bp':[4.,2.]}));assert abs(q['mean_net_1bp_per_leg']-1)<1e-12
