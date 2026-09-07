from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import structure as st


def strict_sample(price=None):
    seconds=np.arange(0,7201,15,dtype=float)
    if price is None:
        price=100*np.exp(np.arange(len(seconds))*1e-5)
    price=np.asarray(price,float)
    r=np.r_[np.nan,np.diff(np.log(price))*1e4]
    return {'second':seconds,'price':price,'return_bp':r}


def test_fine_measurement_complete_and_fixed_twenty_steps():
    sample=strict_sample()
    minute=np.r_[np.nan, np.repeat(0.4,119)]
    out=st.fine_measurements(sample,minute)
    row=out[out.minute==10].iloc[0]
    assert row.fine_complete5
    assert row.pre5m_range_bp > 0
    assert 1 <= row.M2 <= 20
    assert np.isfinite(row.M1) and np.isfinite(row.A5)


def test_missing_fine_step_fails_closed_not_zero_filled():
    sample=strict_sample(); sample['return_bp'][39]=np.nan
    minute=np.r_[np.nan, np.repeat(.4,119)]
    out=st.fine_measurements(sample,minute)
    row=out[out.minute==10].iloc[0]
    assert not row.fine_complete5
    assert np.isnan(row.M1) and np.isnan(row.M2) and np.isnan(row.A5)


def test_activity_surprise_uses_strictly_prior_same_clock_only():
    days=pd.date_range('2022-01-01',periods=62,freq='D').strftime('%Y-%m-%d')
    f=pd.DataFrame({'symbol':'000688.SH','day':days,'year':2022,'afternoon':0,'minute':60,
                    'A5':np.r_[np.linspace(1,2,60),10,1000], 'M1':0.0})
    a=st.attach_activity_surprise(f,min_history=60)
    assert a.M3.iloc[:60].isna().all()
    assert np.isfinite(a.M3.iloc[60])
    # Changing a future row cannot change the already-computed row 60 surprise.
    f2=f.copy();f2.loc[61,'A5']=1e12
    b=st.attach_activity_surprise(f2,min_history=60)
    assert a.M3.iloc[60] == b.M3.iloc[60]


def calibration_frame():
    rows=[]
    for symbol in ('000688.SH','000852.SH'):
        for year,n in ((2023,200),(2024,50),(2025,50)):
            for i in range(n):
                rows.append({'symbol':symbol,'year':year,'decision_ok':True,'fine_complete5':True,
                    'pre5m_range_bp':10.,'M1':i,'M2':i+1.,'M3':i+2.,'M4':i+3.})
    return pd.DataFrame(rows)


def test_2024_2025_values_cannot_change_frozen_2023_thresholds():
    f=calibration_frame(); a=st.freeze_thresholds(f)
    f.loc[f.year>=2024,['M1','M2','M3','M4']]=1e99
    b=st.freeze_thresholds(f)
    pd.testing.assert_frame_equal(a,b)


def test_event_recall_requires_at_least_two_minute_separation():
    q=pd.DataFrame({'session':'2024-01-02/0','minute':np.arange(1,121),
                    'analysis_ok':True,'alarm':False,'first':0.0})
    q.loc[q.minute==50,'first']=1.0
    q.loc[q.minute==49,'alarm']=True
    miss=st.event_metrics(q)
    assert miss['unique_first_events']==1 and miss['unique_first_events_hit']==0
    q.loc[q.minute==48,'alarm']=True
    hit=st.event_metrics(q)
    assert hit['unique_first_events_hit']==1
    assert hit['earliest_lead_minutes']==[2]


def test_forbidden_economic_columns_fail_results_blind_gate():
    with pytest.raises(st.StudyError):
        st.assert_results_blind(['symbol','future_return_15m'])


def test_holm_adjust_is_monotone_in_sorted_p_order():
    p=[.001,.02,.04,None]
    a=st.holm_adjust(p)
    assert a[0] <= a[1] <= a[2] <= 1
    assert a[3] is None
