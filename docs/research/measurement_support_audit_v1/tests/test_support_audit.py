from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from support_audit import consecutive_true, state_from_returns, snapshot_prefix, eligible_pre_event_rows, first_loss

@pytest.mark.parametrize('x,y',[([],[]),([0,0],[0,0]),([1,1,0,1],[1,2,0,1]),([1]*60,list(range(1,61)))])
def test_valid_runs(x,y):
    np.testing.assert_array_equal(consecutive_true(x),y)

def test_run_requires_vector():
    with pytest.raises(ValueError):consecutive_true([[True]])

@pytest.mark.parametrize('r,state',[
 ([1,1,1,1,1],'low_observed_range_below30bp'),
 ([7,7,7,7,7],'already_displaced_30bp'),
 ([-7,-7,-7,-7,-7],'already_displaced_30bp'),
 ([20,20,-20,-20,0],'wide_returning_30bp'),
 ([30,0,0,0,0],'already_displaced_30bp'),
 ([30,-30,0,0,0],'wide_returning_30bp'),
 ([0,0,np.nan,0,0],'unknown'),
 ([1,2],'unknown')])
def test_prefix_states(r,state):
    assert state_from_returns(r)['state']==state

def test_range_includes_first_price():
    x=state_from_returns([10,10,10,10,10]);assert x['net_bp']==50 and x['range_bp']==50

def data():
    t=np.arange(0,1000,3,dtype=float);return t,100*np.exp(t*.000001),np.arange(len(t))

def test_snapshot_prefix_forward_invariance():
    t,p,row=data();a=snapshot_prefix(t,p,row,600);p[t>600]*=3;b=snapshot_prefix(t,p,row,600)
    assert a==b and a['complete_3s']

def test_snapshot_bad_gap_not_quiet():
    t,p,row=data();keep=t!=450;x=snapshot_prefix(t[keep],p[keep],row[keep],600)
    assert x['state']=='unknown' and x['max_gap_seconds']==6

def test_snapshot_same_second_is_unknown():
    t,p,row=data();t=np.r_[t,450];p=np.r_[p,100];row=np.r_[row,9999]
    assert snapshot_prefix(t,p,row,600)['state']=='unknown'

def test_snapshot_stale_endpoint_is_unknown():
    t,p,row=data();keep=t<590;x=snapshot_prefix(t[keep],p[keep],row[keep],600)
    assert not x['complete_3s']

def test_snapshot_empty_is_unknown():
    assert snapshot_prefix([],[],[],600)['state']=='unknown'

def test_latest_lead_correct():
    mins=np.arange(1,121);ok=np.ones(120,bool);m=eligible_pre_event_rows(mins,ok,80)
    assert mins[m].tolist()==list(range(65,79))

def test_label_knowledge_does_not_create_eligibility():
    assert not eligible_pre_event_rows(np.arange(1,121),np.zeros(120,bool),80).any()

def test_shape_rejection():
    with pytest.raises(ValueError):eligible_pre_event_rows([1,2],[1],3)

def test_waterfall_exclusive():
    ones=np.ones(6,bool)
    x=first_loss([0,1,1,1,1,1],[0,0,1,1,1,1],[0,0,0,1,1,1],ones,ones,[0,0,0,0,1,1])
    assert list(x)==['base_ineligible','short5m','long15m','partner_support','retained','retained']

def test_no_15minute_window_from_repeating_half_minute_gap():
    # Availability-only synthetic schedule. No price/forecast claim.
    v=np.tile([1,1,0,0],120);assert consecutive_true(v).max()==2
    assert v.sum()==240 and not (consecutive_true(v)>=60).any()
