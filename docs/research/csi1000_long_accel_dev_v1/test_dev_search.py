from __future__ import annotations
import importlib.util
from pathlib import Path
import pandas as pd

MOD=Path(__file__).resolve().parent/'run_dev_search.py'
s=importlib.util.spec_from_file_location('m',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def test_stats_two_leg_cost():
    z=pd.DataFrame({'gross_5m_bp':[5.,3.]})
    q=m.stats(z,5)
    assert q['trades']==2
    assert abs(q['mean_gross_bp']-4)<1e-12
    assert abs(q['mean_net1_bp']-2)<1e-12
    assert abs(q['one_way_break_even_bp']-2)<1e-12

def test_select_requires_positive_slow_and_long_trigger_is_prebuilt():
    z=pd.DataFrame({'session':['s']*3,'onset_row':[40,50,60],'slow30_net_bp':[1.,-1.,2.],'tail2_share':[.6,.9,.3],'tail1_share':[.2,.2,.2],'gross_5m_bp':[4.,4.,4.]})
    q=m.select(z,30,.4,None,5)
    assert list(q.onset_row)==[40]

def test_cap_is_strict():
    z=pd.DataFrame({'session':['s']*2,'onset_row':[40,50],'slow15_net_bp':[1.,1.],'tail2_share':[.8,.8],'tail1_share':[.59,.60],'gross_3m_bp':[4.,4.]})
    q=m.select(z,15,.8,.60,3)
    assert list(q.onset_row)==[40]
