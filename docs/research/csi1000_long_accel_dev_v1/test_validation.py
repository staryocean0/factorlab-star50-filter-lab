from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
MOD=Path(__file__).resolve().parent/'run_validation.py';s=importlib.util.spec_from_file_location('v',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def test_cost_math():
    z=pd.DataFrame({'gross_bp':[4.,2.]});q=m.metrics(z)
    assert q['trades']==2 and abs(q['mean_gross_bp']-3)<1e-12
    assert abs(q['mean_net_1bp_per_leg']-1)<1e-12 and abs(q['one_way_break_even_bp']-1.5)<1e-12

def test_empty_does_not_pass_economics():
    q=m.metrics(pd.DataFrame({'gross_bp':[]})); assert q['trades']==0 and np.isnan(q['mean_gross_bp'])
