import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import seconds_v2 as v


def source():
    t=np.arange(0,7201,3,dtype=float)
    p=100*np.exp(np.cumsum(np.random.default_rng(1).normal(0,.0001,len(t))))
    return t,p,np.arange(len(t))


@pytest.mark.parametrize('step',[15,30,60])
def test_sampling_exact_endpoints(step):
    t,p,r=source();s=v.sample_session(t,p,r,step,3)
    np.testing.assert_allclose(s['price'],p[::step//3])
    np.testing.assert_allclose(s['return_bp'][1:],np.diff(np.log(p[::step//3]))*1e4,atol=1e-10)
    assert np.isnan(s['return_bp'][0])


def test_tie_policy_keeps_last_row_without_mutation():
    t,p,r=source();tt=np.r_[t,15];pp=np.r_[p,120];rr=np.r_[r,5000]
    s=v.sample_session(tt,pp,rr)
    assert s['price'][1]==120 and s['row_index'][1]==5000
    assert tt[-1]==15


def test_duplicate_composite_key_rejected():
    with pytest.raises(ValueError):v.sample_session([0,0],[100,101],[0,0])


def test_stale_endpoint_is_unknown():
    s=v.sample_session([0,3],[100,101],[0,1])
    assert np.isnan(s['price'][1:]).all()


def test_gap15_measurement_not_claimed_gap3_complete():
    t,p,r=source();mask=~np.isin(t,[3,6])
    a=v.sample_session(t[mask],p[mask],r[mask],15,15)
    b=v.sample_session(t[mask],p[mask],r[mask],15,3)
    assert np.isfinite(a['return_bp'][1]) and a['crossed_gap3'][1]==1
    assert np.isnan(b['return_bp'][1])


def test_large_gap_never_interpolated():
    t,p,r=source();mask=~np.isin(t,np.arange(3,30,3))
    a=v.sample_session(t[mask],p[mask],r[mask],15,15)
    assert np.isnan(a['return_bp'][1:3]).all()


def test_grid_prefix_invariant():
    t,p,r=source();a=v.sample_session(t,p,r)
    b=v.sample_session(t[t<=3600],p[t<=3600],r[t<=3600])
    for key in ('price','return_bp','age','crossed_gap3'):
        np.testing.assert_allclose(a[key][:241],b[key][:241],equal_nan=True)


def test_features_future_mutation():
    t,p,r=source();pp=p.copy();pp[t>3600]*=10
    a=v.fine_features(v.sample_session(t,p,r));b=v.fine_features(v.sample_session(t,pp,r))
    pd.testing.assert_frame_equal(a.iloc[:60],b.iloc[:60])


def test_grid_physical_5m_variance():
    t,p,r=source()
    for step in (15,30,60):
        s=v.sample_session(t,p,r,step,15);f=v.fine_features(s);n=300//step;j=60*20//step
        expected=np.log(np.mean(s['return_bp'][j-n+1:j+1]**2))
        assert f.fine_log_rv5.iloc[19]==pytest.approx(expected)


def test_no_native_scale_fabrication():
    t,p,r=source();f=v.fine_features(v.sample_session(t,p,r,60,15))
    assert f.fine_log_e30.isna().all() and f.fine_log_e60.isna().all()


def test_common_amplitude_energy_scale():
    t,p,r=source();q=100*np.exp(3*np.log(p/100))
    a=v.fine_features(v.sample_session(t,p,r));b=v.fine_features(v.sample_session(t,q,r))
    for col in v.SCALE:
        ok=np.isfinite(a[col])
        np.testing.assert_allclose(b.loc[ok,col]-a.loc[ok,col],np.log(9),atol=1e-8)


def test_targets_actionable_vs_imminent():
    f=pd.DataFrame({'session':['s']*120,'target':np.nan,'first':np.zeros(120),'decision_ok':True})
    f.loc[79,'first']=1
    q=v.aligned_targets(f)
    assert q.target.iloc[77]==1 and q.target_imminent.iloc[77]==0
    assert q.target.iloc[78]==0 and q.target_imminent.iloc[78]==1
    assert q.target.iloc[79]==0
    assert q.target.iloc[-15:].isna().all()


def test_unknown_future_is_not_zero():
    f=pd.DataFrame({'session':['s']*120,'target':np.nan,'first':np.zeros(120),'decision_ok':True})
    f.loc[79,'first']=np.nan;q=v.aligned_targets(f)
    assert np.isnan(q.target.iloc[77])


def test_targets_do_not_change_decision_eligibility():
    f=pd.DataFrame({'session':['s']*120,'target':0.,'first':np.zeros(120),'decision_ok':True})
    a=v.aligned_targets(f);f.loc[79:,'first']=np.nan;b=v.aligned_targets(f)
    pd.testing.assert_series_equal(a.decision_ok,b.decision_ok)


def test_paths_incomplete_not_labeled_concentrated():
    t,p,r=source();keep=~np.isin(t,[4743,4746])
    anchor={'minute':80,'anchor_id':'a','kind':'event','minute_return_bp':30.}
    s,_=v.path_summary(t[keep],p[keep],r[keep],anchor)
    assert not s['event_minute_complete_3s']
    assert s['path_reason']=='unknown_incomplete_or_same_second'


def test_paths_same_second_timing_unknown():
    t,p,r=source();anchor={'minute':80,'anchor_id':'a','kind':'event','minute_return_bp':30.}
    s,_=v.path_summary(np.r_[t,4743],np.r_[p,101],np.r_[r,5000],anchor)
    assert not s['event_minute_complete_3s'] and s['same_second_changes_in_event_minute']==1


def test_constant_path_zero_denominator():
    t,p,r=source();anchor={'minute':80,'anchor_id':'a','kind':'event','minute_return_bp':0.}
    s,_=v.path_summary(t,np.ones(len(t))*100,r,anchor)
    assert s['complete_path_efficiency'] is None


def modeling_frame():
    panel=v.g.synthetic_panel('null',sessions=80)
    panel.loc[panel.index>=30*120,'year']=2023
    panel.loc[panel.index>=50*120,'year']=2024
    rng=np.random.default_rng(42)
    fine=pd.DataFrame({k:rng.normal(size=len(panel)) for k in v.FINE+v.SCALE})
    return v.attach_support(panel,fine,np.ones(len(panel),bool))


def test_fit_never_uses_evaluation_labels():
    f=modeling_frame();a,ar=v.fit_models(f);q=f.copy();q.loc[q.year==2024,'target']=1-q.loc[q.year==2024,'target']
    b,br=v.fit_models(q);assert a is not None
    z=f[(f.year==2024)&f.decision_ok]
    for k,val in v.predict(a,z).items():np.testing.assert_allclose(val,v.predict(b,z)[k])
    assert ar==br


def test_thresholds_do_not_use_calibration_outcomes():
    f=modeling_frame();a,_=v.fit_models(f);f.loc[f.year==2023,'target']=999
    b,_=v.fit_models(f);assert a['thresholds']==b['thresholds']


def test_unknown_support_fails_closed():
    f=modeling_frame();f.loc[f.year.isin([2021,2022]),'metric_ok']=False
    pack,receipt=v.fit_models(f);assert pack is None and receipt['status']=='insufficient_support'


def test_all_models_same_rows_and_actionable_labels():
    f=modeling_frame();pack,_=v.fit_models(f);p=v.predict(pack,f[f.decision_ok])
    assert set(p)=={'B0','B1','B2'} and len({len(x) for x in p.values()})==1


def test_matched_surrogates_preserve_coverage_and_episode_count():
    f=modeling_frame();f=f[f.year==2024].reset_index(drop=True)
    alarm=f.decision_ok.to_numpy() & f.minute.between(70,80).to_numpy()
    info,table=v.matched_null(f,alarm,np.array([2.,4.]),repeats=5)
    assert table.episodes.nunique()==1 and table.risk_time.nunique()==1
    assert table.episodes.iloc[0]==info['observed_episodes']


def test_model_evaluation_smoke(tmp_path):
    f=modeling_frame();pack,_=v.fit_models(f)
    result=v.evaluate(pack,f[f.year==2024],tmp_path,'test',np.array([2.,4.]))
    for k in ('B0','B1','B2'):
        assert result['models'][k]['quota']['windows']['label_decomposition_error']==0
    assert (tmp_path/'test_events.csv').exists()
