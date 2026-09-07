import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve()
sys.path.insert(0,str(HERE.parents[1]/'code'))
import precursor_existence_v32 as p


def test_percentile_rank_mid_ties():
    assert p.percentile_rank(2,np.array([1,2,2,3]))==0.5
    assert p.percentile_rank(4,np.array([1,2,3]))==1.0


def test_primary_score_is_fast_vs_slow_contrast():
    q=pd.DataFrame({'fine_log_e30':[4.0],'fine_log_e60':[3.0],
                    'fine_log_e120':[2.0],'fine_log_e240':[1.0],
                    'fine_log_rv5':[5.0],'fine_log_rv15':[3.0],
                    'fine_log_max1':[2.0],'fine_abs_net5':[7.0]})
    z=p.add_scores(q)
    assert z.primary_scale_score.iloc[0]==2.5
    assert z.short_vs_long_vol.iloc[0]==2.0


def test_event_feature_time_is_e_minus_2():
    rows=[]
    for m in range(1,121):
        rows.append({'session':'2024-01-02/0','day':'2024-01-02','year':2024,'minute':m,
                     'first':1.0 if m==50 else 0.0,'quiet_pre':True,
                     'primary_scale_score':float(m),'short_vs_long_vol':float(m),
                     'max_short_move':float(m),'net5':float(m),
                     'log_sigma_pre':1.0,'log_rv480':2.0})
    q=pd.DataFrame(rows)
    e=p.event_records(q,'000688.SH')
    assert len(e)==1 and e.event_minute.iloc[0]==50 and e.feature_minute.iloc[0]==48
    assert e.primary_scale_score.iloc[0]==48


def test_matching_uses_nearest_background_state_and_caps_100():
    event=pd.Series({'year':2024,'session':'x/0','event_minute':50,
                     'match_log_sigma_pre':0.0,'match_log_rv480':0.0})
    rows=[]
    for i in range(120):
        for m in (48,50):
            rows.append({'year':2024,'afternoon':0,'minute':m,'quiet_pre':True,
                         'near_first_tail_30m':False,'first':0.0,'session':f'd{i}/0','day':f'd{i}',
                         'primary_scale_score':float(i),'short_vs_long_vol':0.0,'max_short_move':0.0,'net5':0.0,
                         'log_sigma_pre':float(i)/100,'log_rv480':float(i)/100})
    q=pd.DataFrame(rows)
    c=p.match_event(q,event)
    assert len(c)==100
    assert c.distance.is_monotonic_increasing


def test_monte_carlo_no_events_is_explicit():
    r,t=p.monte_carlo(pd.DataFrame(columns=['status']),pd.DataFrame())
    assert r['status']=='no_eligible_events' and t.empty
