"""Deterministic engine tests. These are not two-index empirical acceptance."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"code"))
import first_shock_gate as g


@pytest.mark.parametrize("n",[1,2,5,30])
def test_trailing_mean_matches_direct(n):
    x=np.arange(50,dtype=float)
    got=g.roll_mean(x,n)
    for t in range(n-1,len(x)):
        assert got[t]==pytest.approx(x[t-n+1:t+1].mean())
    assert np.isnan(got[:n-1]).all()


def test_unknown_is_not_zero():
    assert np.isnan(g.roll_mean(np.array([1.,np.nan,2.]),3)[-1])
    assert g.roll_mean(np.array([1.,np.nan,2.]),3,2)[-1]==1.5
    assert np.isnan(g.roll_mean(np.ones(3),5)).all()


@pytest.mark.parametrize("length",[2,4,8,16])
def test_common_amplitude_scales_energy_quadratically(length):
    r=np.random.default_rng(3).normal(size=200)
    np.testing.assert_allclose(g.haar_energy(3*r,length),9*g.haar_energy(r,length),equal_nan=True)


def test_common_amplitude_cancels_energy_ratio():
    r=np.random.default_rng(4).normal(size=500)
    def ratio(r):return g.haar_energy(r,2)/g.haar_energy(r,16)
    np.testing.assert_allclose(ratio(r),ratio(7*r),equal_nan=True)


def test_haar_is_not_centered():
    r=np.random.default_rng(5).normal(size=200);new=r.copy();new[100:]+=100
    np.testing.assert_allclose(g.haar_energy(r,16)[:100],g.haar_energy(new,16)[:100],equal_nan=True)


def test_bad_haar_length():
    with pytest.raises(ValueError):g.haar_energy(np.ones(20),3)


def test_events_require_both_thresholds():
    r=np.array([25.,35.,45.,np.nan,50.]);s=np.array([1.,10.,10.,1.,np.nan])
    np.testing.assert_allclose(g.event_flags(r,s),[0,0,1,np.nan,np.nan],equal_nan=True)


def test_sigma_unknown_small_return_is_known_non_event():
    np.testing.assert_allclose(g.event_flags(np.array([1.,31.]),np.array([np.nan,np.nan])),[0,np.nan],equal_nan=True)


def test_first_and_followup_split():
    e=np.zeros(120);e[[40,45,90]]=1
    y=g.event_labels(e)
    assert y['first'][40]==1 and y['first'][45]==0 and y['first'][90]==1
    assert y['target'][39]==1 and not y['quiet_now'][45]


def test_unknown_quiet_interval_cannot_be_first():
    e=np.zeros(100);e[20]=np.nan;e[40]=1
    y=g.event_labels(e)
    assert np.isnan(y['first'][40])
    assert not y['quiet_now'][30]


def test_label_starts_strictly_after_decision():
    e=np.zeros(120);e[50]=1
    y=g.event_labels(e)
    assert y['target'][49]==1
    assert y['target'][50]==0
    assert np.isnan(y['target'][-15:]).all()


def test_no_cross_session_label():
    first=g.event_labels(np.zeros(120));second=g.event_labels(np.r_[1.,np.zeros(119)])
    assert np.isnan(first['target'][-1])
    assert np.isnan(second['first'][0])


def panel(n=8):return g.synthetic_panel('null',sessions=n)


def test_feature_prefix_replay():
    p=panel();f=g.make_features(p);cut=750;prefix=g.make_features(p.iloc[:cut])
    cols=g.BASE+['log_fast_energy','sigma_pre','decision_ok','event','first']
    pd.testing.assert_frame_equal(f[cols].iloc[:cut].reset_index(drop=True),prefix[cols],check_exact=False,rtol=1e-12,atol=1e-12)


def test_future_mutation_does_not_change_old_features():
    p=panel();q=p.copy();q.loc[750:,'return_bp']=999
    a,b=g.make_features(p),g.make_features(q)
    cols=g.BASE+['log_fast_energy','decision_ok','sigma_pre']
    pd.testing.assert_frame_equal(a[cols].iloc[:750],b[cols].iloc[:750])


def test_event_standardization_excludes_event_itself():
    p=panel();p.loc[700,'return_bp']=10000
    q=p.copy();q.loc[700,'return_bp']=0
    a,b=g.make_features(p),g.make_features(q)
    assert a.loc[700,'sigma_pre']==b.loc[700,'sigma_pre']


def test_gap_does_not_become_quiet():
    p=panel();p.loc[660,'return_bp']=np.nan;f=g.make_features(p)
    assert not f.loc[660:689,'decision_ok'].any()


@pytest.mark.parametrize('year',[2020,2026])
def test_year_boundary_rejected(year):
    p=panel(1);p.year=year
    with pytest.raises(ValueError):g.make_features(p)


def test_grid_hole_rejected_not_silently_compressed():
    p=panel(1).drop(index=20)
    with pytest.raises(ValueError):g.make_features(p)


def native():
    ts=pd.date_range('2024-01-02 09:31:00',periods=120,freq='min')
    return pd.DataFrame({'symbol':'000688.SH','timestamp':ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'trading_day':'2024-01-02','close':1000+np.arange(120),
        'causal_flat_fill':False,'high_frequency_analysis_eligible':True})


def test_source_Z_is_wall_clock_and_first_return_unknown():
    p=g.minute_panel(native(),'000688.SH')
    assert np.isnan(p.return_bp.iloc[0]) and p.return_bp.iloc[1]>0
    assert p.source_valid.sum()==120
    assert np.isnan(p.return_bp.iloc[120:]).all()


def test_repaired_price_is_not_analysis_price():
    x=native();x.loc[10,'causal_flat_fill']=True
    p=g.minute_panel(x,'000688.SH')
    assert np.isnan(p.return_bp.iloc[10:12]).all()


def test_missing_quality_flag_fails_closed():
    with pytest.raises(ValueError):g.minute_panel(native().drop(columns='causal_flat_fill'),'000688.SH')


def snapshots():
    t=pd.date_range('2024-01-02 09:30:00',periods=21,freq='3s')
    return pd.DataFrame({'observation_datetime':t.strftime('%Y-%m-%dT%H:%M:%SZ'),
                         'row_index':np.arange(len(t)),'price':100.+np.arange(len(t))})


def test_snapshot_no_future_quote():
    s=snapshots();grid=pd.date_range('2024-01-02 09:30:00',periods=5,freq='15s')
    a=g.snapshot_grid(s,grid)
    q=s.copy();q.loc[16:,'price']=999
    b=g.snapshot_grid(q,grid)
    pd.testing.assert_series_equal(a.price.iloc[:4],b.price.iloc[:4])


def test_snapshot_same_second_row_order_explicit():
    s=snapshots();extra=s.iloc[[5]].copy();extra.row_index=100;extra.price=1234
    combined=pd.concat([s,extra],ignore_index=True)
    before=combined.copy(deep=True)
    grid=pd.date_range('2024-01-02 09:30:00',periods=5,freq='15s')
    a=g.snapshot_grid(combined,grid)
    assert a.price.iloc[1]==1234 and a.chosen_row_index.iloc[1]==100
    pd.testing.assert_frame_equal(combined,before)


def test_snapshot_crossed_gap_rejected_even_with_fresh_endpoints():
    s=snapshots().drop(index=[2,3]);grid=pd.date_range('2024-01-02 09:30:00',periods=5,freq='15s')
    a=g.snapshot_grid(s,grid)
    assert np.isfinite(a.price.iloc[:2]).all() and np.isnan(a.return_bp.iloc[1])


def test_stale_snapshot_unknown():
    s=snapshots().iloc[:2];grid=pd.date_range('2024-01-02 09:30:00',periods=5,freq='15s')
    a=g.snapshot_grid(s,grid)
    assert np.isnan(a.price.iloc[1:]).all()


def test_lunch_grid_rejected():
    with pytest.raises(ValueError):
        g.snapshot_grid(snapshots(),pd.date_range('2024-01-02 11:30:00',periods=2,freq='90min'))


def match_frame():
    f=panel(1);f['first']=0.;f.loc[79,'first']=1.;f.loc[79,'return_bp']=60
    f['decision_ok']=f.minute.between(31,105)
    return f


def test_one_minute_before_close_is_not_pre_onset_warning():
    f=match_frame();a=np.zeros(len(f),bool);a[78]=True  # minute79 for minute80 event
    score,_=g.match_events(f,a)
    assert score['warned_events']==0


def test_two_minutes_before_close_is_one_minute_pre_onset():
    f=match_frame();a=np.zeros(len(f),bool);a[77]=True
    score,_=g.match_events(f,a)
    assert score['warned_events']==1 and score['median_latest_lead_minutes']==1


def test_duplicate_alarms_do_not_duplicate_event_count():
    f=match_frame();a=np.zeros(len(f),bool);a[65:78]=True
    score,_=g.match_events(f,a)
    assert score['warned_events']==1 and score['unique_first_events']==1


def test_unavailable_event_kept_in_denominator():
    f=match_frame();f['decision_ok']=False
    score,_=g.match_events(f,np.zeros(len(f),bool))
    assert score['unique_first_events']==1 and score['unknown_or_no_eligible_warning_share']==1
    assert score['recall_eligible_events'] is None


def test_precision_episodes_one_to_one():
    f=match_frame();a=np.zeros(len(f),bool);a[66]=a[70]=True
    score,_=g.match_events(f,a)
    assert score['alarm_episodes']==2 and score['matched_episodes_one_to_one']==1
    assert score['episode_precision_one_to_one']==.5


def test_empty_denominators_not_zero_success():
    s=g.metrics(np.zeros(5),np.ones(5)*.01,np.zeros(5,bool))
    assert s['window_precision'] is None and s['event_window_miss_share'] is None


def test_exact_quota_ties_stable():
    a=g.budget_alarm(np.ones(10),.2)
    np.testing.assert_equal(a,np.r_[True,True,np.zeros(8,bool)])


def test_bootstrap_paired_identity():
    v=np.tile([1,10,1,10],(30,1))
    c=g.moving_block_ci(v,repeats=50)
    assert c['delta_enhanced_minus_baseline_ci95']==[0.,0.]


def test_single_class_fit_rejected():
    f=g.make_features(panel());f.target=0
    with pytest.raises(ValueError):g.fit_pair(f,f)


def test_synthetic_precursor_changes_signs_not_return_amplitudes():
    a=g.synthetic_panel('null',sessions=8)
    b=g.synthetic_panel('precursor',sessions=8)
    np.testing.assert_allclose(np.abs(a.return_bp),np.abs(b.return_bp),equal_nan=True)


def test_split_components_prefix():
    import diagnose_measurement as d
    p=panel();full=d.add_components(g.make_features(p))
    prefix=d.add_components(g.make_features(p.iloc[:750]))
    pd.testing.assert_frame_equal(full[['log_e2','log_e4']].iloc[:750],prefix[['log_e2','log_e4']])


def test_split_models_do_not_fit_evaluation_labels():
    import diagnose_measurement as d
    p=g.synthetic_panel('precursor',sessions=18)
    p.loc[p.index>=1200,'year']=2023;p.loc[p.index>=1680,'year']=2024
    f=d.add_components(g.make_features(p));q=f.copy()
    q.loc[q.year==2024,'target']=1-q.loc[q.year==2024,'target']
    a,b=d.fit_split(f),d.fit_split(q)
    c=f[(f.year==2023)&f.metric_ok]
    for x,y in zip(a.scores(c),b.scores(c)):np.testing.assert_allclose(x,y)


def test_averaging_can_hide_a_single_scale_increase():
    r=np.tile([-1.,1.],100)
    e2=g.haar_energy(r,2);e4=g.haar_energy(r,4)
    assert np.nanmean(e2)==pytest.approx(2.)
    assert np.nanmean(e4)==pytest.approx(0.)
    assert np.nanmean((e2+e4)/2)==pytest.approx(1.)
