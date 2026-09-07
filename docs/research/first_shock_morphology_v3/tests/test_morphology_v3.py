import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / 'code'))
import morphology_v3 as m


def sample():
    second = np.arange(0, 7201, 15)
    price = np.ones(len(second)) * 100.0
    ret = np.zeros(len(second)); ret[0] = np.nan
    return {'second': second, 'price': price, 'return_bp': ret}


def test_quiet_precondition_is_strictly_pre_event():
    s = sample(); z = m.minute_morphology(s, 40)
    assert z['quiet_pre'] is True and z['active_pre'] is False
    assert z['pre5_abs_net_bp'] == 0 and z['pre5_range_bp'] == 0


def test_active_precondition_from_short_return():
    s = sample(); start = (40-1)*4
    s['return_bp'][start] = 16.0
    z = m.minute_morphology(s, 40)
    assert z['quiet_pre'] is False and z['active_pre'] is True


def test_intermediate_precondition():
    s = sample(); start = (40-1)*4
    s['return_bp'][start] = 10.0
    z = m.minute_morphology(s, 40)
    assert z['quiet_pre'] is False and z['active_pre'] is False


def test_roundtrip_requires_range_low_net_and_low_efficiency():
    s = sample(); minute = 40; a=(minute-1)*4; b=minute*4
    s['price'][a:b+1] = [100, 100.40, 100.00, 100.35, 100.00]
    s['return_bp'][a+1:b+1] = np.diff(np.log(s['price'][a:b+1]))*1e4
    z = m.minute_morphology(s, minute)
    assert z['roundtrip'] is True
    assert z['minute_range_bp'] >= 30 and z['minute_abs_net_bp'] <= 10 and z['minute_efficiency'] <= .25


def test_directional_move_is_not_roundtrip():
    s = sample(); minute=40; a=(minute-1)*4; b=minute*4
    s['price'][a:b+1] = np.linspace(100,100.5,5)
    s['return_bp'][a+1:b+1] = np.diff(np.log(s['price'][a:b+1]))*1e4
    assert m.minute_morphology(s, minute)['roundtrip'] is False


def test_unknown_pre_support_never_becomes_quiet():
    s=sample(); minute=40; a=(minute-1)*4
    s['return_bp'][a-5]=np.nan
    z=m.minute_morphology(s,minute)
    assert z['pre_support'] is False and z['quiet_pre'] is None and z['active_pre'] is None


def test_first_roundtrip_requires_thirty_known_prior_minutes():
    flags=[False]*40
    flags[35]=True
    out=m.first_roundtrip(flags)
    assert out[35]==1
    flags=[False]*40; flags[10]=None; flags[35]=True
    out=m.first_roundtrip(flags)
    assert np.isnan(out[35])


def test_roundtrip_cluster_second_event_not_first():
    flags=[False]*50; flags[35]=True; flags[40]=True
    out=m.first_roundtrip(flags)
    assert out[35]==1 and out[40]==0
