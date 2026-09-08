from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

MOD=Path(__file__).resolve().parent/"run_continuous_vol_regime.py"
spec=importlib.util.spec_from_file_location("cv",MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def make_native(returns_bp):
    day="2022-01-04";times=pd.date_range(day+" 09:30:00",periods=120,freq="1min")
    r=np.zeros(120);r[1:1+len(returns_bp)]=np.asarray(returns_bp,float)
    close=100*np.exp(np.cumsum(r)/1e4)
    rows=[]
    for i,t in enumerate(times):
        rows.append({"trading_day":day,"timestamp":t.strftime("%Y-%m-%d %H:%M:%S"),"close":close[i],"open":close[i],"high":close[i],"low":close[i],"high_frequency_analysis_eligible":True,"causal_flat_fill":False})
    return pd.DataFrame(rows)


def test_ratio_uses_nonoverlapping_30_plus_5_windows():
    # returns 1..30 = 1bp background; returns 31..35 = 2bp fast => ratio 2 at minute 36 close.
    native=make_native([1.0]*30+[2.0]*5+[1.0]*20)
    s=m.build_continuous_state(native,"X")
    q=s[(s.session=="2022-01-04/0")&(s.minute==36)].iloc[0]
    assert q.route_state=="HighVol"
    assert abs(q.vol_ratio-2.0)<1e-10


def test_prefix_causality_future_change_does_not_change_past_state():
    a=make_native([1.0]*30+[2.0]*5+[1.0]*40)
    b=a.copy()
    # Alter only a future close path after minute 60; earlier state must be identical.
    ix=np.arange(len(b))>=60
    factor=np.exp(np.linspace(0,0.05,ix.sum()))
    for c in ("open","high","low","close"):
        b.loc[ix,c]=b.loc[ix,c].to_numpy(float)*factor
    sa=m.build_continuous_state(a,"X");sb=m.build_continuous_state(b,"X")
    xa=sa[(sa.session=="2022-01-04/0")&(sa.minute<=60)].reset_index(drop=True)
    xb=sb[(sb.session=="2022-01-04/0")&(sb.minute<=60)].reset_index(drop=True)
    assert np.array_equal(xa.route_state.to_numpy(),xb.route_state.to_numpy())
    assert np.allclose(xa.vol_ratio.to_numpy(float),xb.vol_ratio.to_numpy(float),equal_nan=True)


def test_missing_minute_makes_crossing_returns_unknown_not_flat():
    native=make_native([1.0]*50)
    native.loc[20,"high_frequency_analysis_eligible"]=False
    s=m.build_continuous_state(native,"X")
    # windows depending on the invalid minute cannot immediately recover to a known low-vol state.
    z=s[(s.session=="2022-01-04/0")&(s.minute.between(21,55))]
    assert (z.route_state=="Unknown").any()


def test_nomination_uses_development_years_only():
    rows=[]
    for year in (2021,2022,2023,2024,2025,2026):
        for scale in (1,2):
            # Scale1 wins development. Scale2 is made huge only in validation and must not affect nomination.
            val=(1.0 if scale==1 else 0.5) if year<=2023 else (0.1 if scale==1 else 100.0)
            rows.append({"symbol":"000688.SH","year":year,"family":"fixed_physical","scale_min":scale,"gate":"HighVol","exposure_minutes":100,"net_bp_per_exposure_min_cost_1":val})
    annual=pd.DataFrame(rows)
    pooled=pd.DataFrame([
        {"symbol":"000688.SH","family":"fixed_physical","scale_min":1,"gate":"HighVol","net_bp_per_exposure_min_cost_1":1.0},
        {"symbol":"000688.SH","family":"fixed_physical","scale_min":2,"gate":"HighVol","net_bp_per_exposure_min_cost_1":0.5},
    ])
    # add CSI NONE-compatible placeholders so function can iterate both symbols
    for year in (2021,2022,2023):
        annual.loc[len(annual)]={"symbol":"000852.SH","year":year,"family":"fixed_physical","scale_min":1,"gate":"HighVol","exposure_minutes":100,"net_bp_per_exposure_min_cost_1":-1.0}
    pooled.loc[len(pooled)]={"symbol":"000852.SH","family":"fixed_physical","scale_min":1,"gate":"HighVol","net_bp_per_exposure_min_cost_1":-1.0}
    q=m.nominate(annual,pooled)
    x=q[q.symbol=="000688.SH"].iloc[0]
    assert x.scale_min==1
