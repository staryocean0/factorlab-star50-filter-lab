from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

MOD=Path(__file__).resolve().parent/"run_context_diag.py"
spec=importlib.util.spec_from_file_location("c",MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_eff_is_bounded():
    assert abs(m.eff(np.array([1.,1.,-1.]))-1/3)<1e-12
    assert np.isnan(m.eff(np.zeros(3)))


def test_summary_preserves_role_and_alignment():
    z=pd.DataFrame({"year":[2022,2024],"sign5":[1.,-1.],"same_direction_30":[True,False],"gross_bp":[4.,-2.]})
    q=m.summarize(z)
    assert set(q.role.dropna())=={"Development","Validation"}
    assert ((q.get('mean_net_1bp_per_leg',pd.Series(dtype=float))==2.0).any())
