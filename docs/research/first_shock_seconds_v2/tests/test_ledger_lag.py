import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import seconds_v2 as v
import ledger_lag_audit as a


def test_matching_state_is_before_event():
    p=v.g.synthetic_panel('null',sessions=15)
    p.loc[p.index>=1200,'year']=2024
    f=v.g.make_features(p)
    x=a.lagged_anchor_table(f,'000688.SH')
    assert len(x)>0 and (x.matching_state_minute==x.minute-2).all()


def test_event_current_volatility_not_used_for_matching():
    p=v.g.synthetic_panel('null',sessions=20)
    p.loc[p.index>=1200,'year']=2024
    f=v.g.make_features(p);q=f.copy()
    q.loc[(q.year==2024)&(q['first']==1),['log_rv30','log_rv480']]=9999
    x=a.lagged_anchor_table(f,'000688.SH');y=a.lagged_anchor_table(q,'000688.SH')
    pd.testing.assert_frame_equal(x,y)
