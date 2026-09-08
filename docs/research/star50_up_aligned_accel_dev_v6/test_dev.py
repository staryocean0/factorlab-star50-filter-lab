from __future__ import annotations
import importlib.util
from pathlib import Path
MOD=Path(__file__).resolve().parent/'run_dev.py';s=importlib.util.spec_from_file_location('u',MOD);u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
def test_bounds_and_candidate_identity():
 assert u.START=='2021-01-01' and u.END=='2023-12-31' and u.YEARS==(2021,2022,2023)
 assert u.CANDIDATE=={'direction':'long','slow30_sign':'positive','net5_sign':'positive','efficiency5_min':0.6,'tail2_share_min':0.6,'tail1_condition':None,'hold_min':3}
def test_cost_math():
 import pandas as pd
 q=u.metrics(pd.DataFrame({'gross_bp':[4.,2.]}));assert abs(q['mean_net_1bp_per_leg']-1)<1e-12
