import numpy as np
import pandas as pd
import pytest
from star50_filter.execution_audit import (schedule_sources, minute_account,
    endpoint_audit, reprice, publication_clock, coarse_open_clock)


def carriers():
    # Index labels are right-closed; availability is a separate aware clock.
    t=pd.date_range('2021-01-04 09:31', periods=30, freq='min')
    m=pd.DataFrame({'timestamp':t,'trading_day':'2021-01-04',
        'open':100*np.exp(np.arange(30)*.001),
        'close':100*np.exp((np.arange(30)+.9)*.001),
        'source_kind':'observed'})
    b=pd.DataFrame({'timestamp':t[4::5],'trading_day':'2021-01-04',
        'open':m.open.iloc[::5].to_numpy(),'close':m.close.iloc[4::5].to_numpy(),
        'available_at':[x.isoformat()+'+08:00' for x in t[4::5]]})
    return b,m


def test_known_minute_entry_and_full_cost_identity():
    b,m=carriers();target=np.array([1.,-1.,1.,1.,-1.,1.])
    a=minute_account(b,m,target,'legacy_on_minute')
    # first source cannot exist until 09:35; its first earned interval ends09:36
    assert a.loc[a.timestamp==pd.Timestamp('2021-01-04 09:35'),'q_before'].iloc[0]==0
    assert a.loc[a.timestamp==pd.Timestamp('2021-01-04 09:36'),'q_before'].iloc[0]==1
    assert a.q_after.iloc[-1]==0
    net,fee=reprice(a,3)
    np.testing.assert_allclose(net+fee,a.gross_log_pnl,atol=1e-15)
    assert a.turnover.sum()==6 # enter1, reverse2, reverse2, terminal exit1


def test_delay_and_synthetic_skip_cannot_fill_early():
    b,m=carriers();m.loc[6,'source_kind']='causal_flat_missing_minute'
    x=schedule_sources(b,m,'delay_1m')
    y=schedule_sources(b,m,'delay_1m_observed')
    assert x[6]==0 and y[6]==-1 and y[7]==0
    assert np.all(x[:6]==-1)


def test_publication_is_offset_aware_and_fail_closed():
    b,m=carriers();b['available_at']='2021-01-04T15:30:00+08:00'
    assert pd.Timestamp(publication_clock(b)[0]).hour==15
    assert np.all(schedule_sources(b,m,'literal_publication')==-1)
    # A late older input delays a recursively computed later signal too.
    b,m=carriers();b.loc[0,'available_at']='2021-01-04T15:30:00+08:00'
    assert np.all(schedule_sources(b,m,'literal_publication')==-1)


def test_no_local_resampling_endpoint_validation():
    b,m=carriers();assert endpoint_audit(b,m)['open_mismatches']==0
    b.loc[0,'open']+=1
    assert endpoint_audit(b,m)['open_mismatches']==1


def test_prefix_stability_and_unregistered_scenario():
    b,m=carriers()
    for name in ['legacy_on_minute','delay_1m','delay_1m_observed','literal_publication']:
        full=schedule_sources(b,m,name)
        short=schedule_sources(b.iloc[:4],m.iloc[:20],name)
        np.testing.assert_array_equal(full[:20],short)
    with pytest.raises(ValueError):schedule_sources(b,m,'best_backtest')


def test_offset_first_session_bar_has_six_source_minutes():
    b=pd.DataFrame({'timestamp':pd.to_datetime(['2021-01-04 09:39','2021-01-04 09:44',
        '2021-01-04 13:09','2021-01-04 13:14']), 'trading_day':'2021-01-04',
        'export_view_id':'5m_offset_4'})
    assert [pd.Timestamp(x).strftime('%H:%M') for x in coarse_open_clock(b)]==[
        '09:33','09:39','13:03','13:09']


def test_repaired_open_endpoint_uses_first_observed_quote_without_price_search():
    b,m=carriers();m.loc[5,'source_kind']='causal_flat_missing_minute'
    b.loc[1,'open']=m.open.iloc[6]
    assert coarse_open_clock(b,m)[1]==np.datetime64('2021-01-04T09:36')
    assert endpoint_audit(b,m)['open_mismatches']==0
    b.loc[1,'open']=999
    assert endpoint_audit(b,m)['open_mismatches']==1
