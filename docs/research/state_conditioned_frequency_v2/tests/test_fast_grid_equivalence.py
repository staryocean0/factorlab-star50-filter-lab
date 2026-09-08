from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve()
CODE=HERE.parents[1]/"code"


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

ref=load(CODE/"run_physical_scale_strategy.py","ref_grid")
fg=load(CODE/"fast_grid.py","fast_grid")


def fixture():
    day="2024-01-02"
    times=list(pd.date_range(f"{day} 09:30:00",periods=120,freq="1min"))+list(pd.date_range(f"{day} 13:00:00",periods=120,freq="1min"))
    px=np.exp(np.arange(240)*0.0001)
    native=pd.DataFrame({
        "trading_day":[day]*240,"ts":times,
        "open":px,"high":px*1.0001,"low":px*0.9999,"close":px*1.00002,
        "high_frequency_analysis_eligible":[True]*240,"causal_flat_fill":[False]*240,
    })
    native.loc[17,"high_frequency_analysis_eligible"]=False
    rows=[]
    for half in (0,1):
        for minute in range(1,121):
            if minute<33:
                state="NoEpisode";ratio=np.nan
            elif minute<38:
                state="Unsafe";ratio=np.nan
            elif minute%11==0:
                state="Unsafe";ratio=1.7
            else:
                state="Recovering";ratio=.8
            rows.append({"session":f"{day}/{half}","minute":minute,"route_state":state,"recovery_ratio":ratio})
    return native,pd.DataFrame(rows)


def test_fast_grid_matches_reference_all_registered_scales():
    native,state=fixture()
    minute=fg.build_minute_grid(native,state,"X")
    for scale in ref.SCALES:
        a=ref.session_grid(native,state,"X",scale).reset_index(drop=True)
        b=fg.aggregate_scale(minute,scale).reset_index(drop=True)
        assert list(a.columns)==list(b.columns)
        for col in a.columns:
            if col in {"open","high","low","close","recovery_ratio"}:
                assert np.allclose(pd.to_numeric(a[col],errors="coerce"),pd.to_numeric(b[col],errors="coerce"),equal_nan=True,atol=0,rtol=0), (scale,col)
            else:
                av=a[col].astype(str).replace("NaT","nan").to_numpy()
                bv=b[col].astype(str).replace("NaT","nan").to_numpy()
                assert np.array_equal(av,bv), (scale,col)


def test_fast_grid_preserves_nan_ratio_at_exact_bar_close():
    native,state=fixture()
    minute=fg.build_minute_grid(native,state,"X")
    b=fg.aggregate_scale(minute,5)
    row=b[(b.session=="2024-01-02/0")&(b.bar_close_minute==35)].iloc[0]
    assert row.route_state=="Unsafe"
    assert pd.isna(row.recovery_ratio)
