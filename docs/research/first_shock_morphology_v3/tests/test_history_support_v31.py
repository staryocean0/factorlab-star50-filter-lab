import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve()
sys.path.insert(0,str(HERE.parents[1]/'code'))
import history_support_v31 as h


def test_generalized_first_features_allows_pre2021_history():
    r=np.zeros(120);r[0]=np.nan;r[40]=50.0
    p=pd.DataFrame({'session':'2018-01-02/0','day':'2018-01-02','year':2018,
                    'minute':np.arange(1,121),'afternoon':0,'return_bp':r,'source_valid':True})
    f=h.generalized_first_features(p)
    assert f.year.iloc[0]==2018
    assert f.loc[40,'event']==1 and f.loc[40,'first']==1


def test_readiness_uses_independent_anchor_counts():
    t=pd.DataFrame([
        {'symbol':'000852.SH','year':2015,'quiet_first_tail':8,'roundtrip_first':0,'quiet_roundtrip':0},
        {'symbol':'000852.SH','year':2016,'quiet_first_tail':12,'roundtrip_first':1,'quiet_roundtrip':0},
    ])
    # Include the other symbol so the helper's fixed symbol loop has a valid empty slice.
    t=pd.concat([t,pd.DataFrame([{'symbol':'000688.SH','year':2020,'quiet_first_tail':0,'roundtrip_first':0,'quiet_roundtrip':0}])],ignore_index=True)
    r=h.readiness(t)
    z=r[(r.symbol=='000852.SH')&(r.event_family=='quiet_first_tail')].sort_values('through_year')
    assert z.iloc[-1].cumulative_independent_anchors==20 and bool(z.iloc[-1].ready)
