from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve()
MOD=HERE.parents[1]/"code"/"run_physical_scale_strategy.py"
spec=importlib.util.spec_from_file_location("v2",MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class DummyFilters:
    @staticmethod
    def butter_lowpass(log_close,period_bars,order=1):
        out=np.asarray(log_close,float).copy()
        out[:period_bars]=np.nan
        return out
    @staticmethod
    def hysteresis_positions(y,threshold):
        return np.where(np.isfinite(y),1.0,0.0)


def test_family_parameter_anchor_at_5m():
    bars=pd.DataFrame({"close":np.exp(np.arange(300)/1000),"valid":True})
    a=m.base_signal(DummyFilters,bars,"scaled_clock",5)
    b=m.base_signal(DummyFilters,bars,"fixed_physical",5)
    for x,y in zip(a,b):
        assert np.array_equal(x,y,equal_nan=True)


def test_fixed_physical_and_scaled_differ_at_1m():
    bars=pd.DataFrame({"close":np.exp(np.arange(400)/1000),"valid":True})
    _,low_a,sig_a=m.base_signal(DummyFilters,bars,"scaled_clock",1)
    _,low_b,sig_b=m.base_signal(DummyFilters,bars,"fixed_physical",1)
    assert np.flatnonzero(np.isfinite(low_a))[0]==12
    assert np.flatnonzero(np.isfinite(low_b))[0]==60
    assert np.flatnonzero(np.isfinite(sig_a))[0]==48
    assert np.flatnonzero(np.isfinite(sig_b))[0]==240


def test_simulation_two_bar_delay_and_forced_flat():
    bars=pd.DataFrame({
        "session":["d/0"]*5,
        "open":np.exp(np.arange(5)*0.001),
        "valid":[True]*5,
        "route_state":["Unsafe"]*5,
    })
    sig=np.ones(5)
    q=m.simulate_gate(bars,sig,"Unsafe")
    # signal[0] first becomes booked position at bar index 2, earning open1->open2, then indices 3,4.
    assert q["exposure_bars"]==3
    assert abs(q["gross_bp"]-30.0)<1e-8
    # 0->1 then forced 1->0 = two one-way turnover units.
    assert q["one_way_turnover"]==2.0


def test_gate_exit_flattens_and_charges_turnover():
    bars=pd.DataFrame({
        "session":["d/0"]*6,
        "open":np.exp(np.arange(6)*0.001),
        "valid":[True]*6,
        "route_state":["Unsafe","Unsafe","Unsafe","Recovering","Recovering","Recovering"],
    })
    sig=np.ones(6)
    q=m.simulate_gate(bars,sig,"Unsafe")
    assert q["one_way_turnover"]>=2.0
    assert q["exposure_bars"]>0


def test_separate_sessions_never_book_cross_boundary_return():
    bars=pd.DataFrame({
        "session":["d/0"]*3+["d/1"]*3,
        "open":[1.0,1.0,2.0,100.0,100.0,100.0],
        "valid":[True]*6,
        "route_state":["Unsafe"]*6,
    })
    sig=np.ones(6)
    q=m.simulate_gate(bars,sig,"Unsafe")
    # First session can book only bar 2 return 1->2; giant 2->100 lunch jump must never be booked.
    assert abs(q["gross_bp"]-np.log(2.0)*1e4)<1e-8


def test_pool_break_even_is_gross_over_turnover():
    df=pd.DataFrame([
        {"symbol":"X","year":2024,"family":"scaled_clock","scale_min":1,"gate":"Unsafe","gross_bp":12.,"one_way_turnover":4.,"exposure_bars":5,"exposure_minutes":5,"booked_returns":5,"winning_returns":3},
        {"symbol":"X","year":2025,"family":"scaled_clock","scale_min":1,"gate":"Unsafe","gross_bp":8.,"one_way_turnover":6.,"exposure_bars":5,"exposure_minutes":5,"booked_returns":5,"winning_returns":2},
    ])
    q=m.pool_years(df,(2024,2025)).iloc[0]
    assert abs(q.break_even_one_way_cost_bp-2.0)<1e-12
    assert abs(q["net_bp_cost_2"]-0.0)<1e-12
