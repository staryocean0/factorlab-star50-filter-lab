from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

MOD=Path(__file__).resolve().parent/"run_validation.py"
spec=importlib.util.spec_from_file_location("v",MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_exact_thresholds_and_non_overlap():
    z=pd.DataFrame({
        "symbol":["000852.SH"]*4,"year":[2024]*4,"trading_day":["2024-01-02"]*4,"session":["2024-01-02/0"]*4,
        "onset_minute":[50,55,70,80],"onset_row":[49,54,69,79],"sign5":[1.,1.,-1.,1.],
        "tail1_share":[.59,.59,.60,.20],"tail2_share":[.80,.90,.90,.79],"eff5":[.5,.5,.5,.5],"vol_ratio":[1.6]*4,
        "cont_10m_bp":[4.,5.,6.,7.]})
    q=m.select_candidate(z)
    # first passes; second overlaps first; third fails tail1<.60; fourth fails tail2>=.80
    assert len(q)==1
    assert int(q.iloc[0].onset_minute)==50


def test_cost_is_two_legs():
    z=pd.DataFrame({"gross_bp":[4.,2.]})
    q=m.metrics(z)
    assert q["trades"]==2
    assert abs(q["mean_gross_bp"]-3.0)<1e-12
    assert abs(q["mean_net_bp_cost_1"]-1.0)<1e-12
    assert abs(q["one_way_break_even_bp"]-1.5)<1e-12


def test_empty_metrics_do_not_fake_pass():
    q=m.metrics(pd.DataFrame({"gross_bp":[]}))
    assert q["trades"]==0
    assert np.isnan(q["mean_gross_bp"])
