from __future__ import annotations
import importlib.util
from pathlib import Path
import pandas as pd
MOD=Path(__file__).resolve().parent/'run_ablation.py';s=importlib.util.spec_from_file_location('m',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture():
    # onset 43 overlaps the trade opened after onset 40 and must be skipped;
    # onset 45 is after the first trade has exited and is therefore eligible.
    return pd.DataFrame({'session':['s']*5,'onset_row':[40,43,45,50,60],'slow30_net_bp':[1.,1.,1.,-1.,1.],'tail2_share':[.7,.7,.7,.7,.5],'tail1_share':[.4,.4,.4,.4,.4],'gross_3m_bp':[4.,4.5,5.,6.,7.],'year':[2024]*5})

def test_full_candidate_filters_and_nonoverlap():
    q=m.select(fixture(),'full_candidate')
    assert list(q.onset_row)==[40,45]

def test_component_variants_differ():
    z=fixture()
    assert len(m.select(z,'base_long_highvol'))>=len(m.select(z,'full_candidate'))
    assert len(m.select(z,'slow30_only'))>=len(m.select(z,'full_candidate'))
    assert len(m.select(z,'accel_only'))>=len(m.select(z,'full_candidate'))

def test_cost_math():
    q=m.metrics(pd.DataFrame({'gross_bp':[4.,2.]}));assert abs(q['mean_net1_bp']-1)<1e-12
