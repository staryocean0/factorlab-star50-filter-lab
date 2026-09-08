from __future__ import annotations
import importlib.util
from pathlib import Path
import pandas as pd
MOD=Path(__file__).resolve().parent/'run_validation.py';s=importlib.util.spec_from_file_location('v',MOD);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)

def test_cost_math_two_legs():
    q=v.metrics(pd.DataFrame({'gross_bp':[4.,2.]}));assert abs(q['mean_net_1bp_per_leg']-1)<1e-12

def test_acceptance_shape_is_fixed():
    assert v.START=='2024-01-01' and v.END=='2026-08-21' and v.YEARS==(2024,2025,2026)
