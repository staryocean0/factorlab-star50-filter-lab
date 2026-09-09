import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("study", HERE / "run_study.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def synthetic_session(prices):
    n=len(prices)
    return pd.DataFrame({
        "day":["2023-01-03"]*n,
        "session":["2023-01-03/0"]*n,
        "minute":np.arange(1,n+1),
        "eligible":[True]*n,
        "close":np.asarray(prices,float),
    })


def test_move_bp_inverse_sign():
    assert study.move_bp(100,101) > 0
    assert study.move_bp(101,100) < 0


def test_causal_engine_finds_confirmation_and_overshoot():
    # 120-minute path: quiet, then >20bp rise, another >20bp extension, then decline.
    p=np.ones(120)*100.0
    for i in range(10,30): p[i]=100*np.exp((i-9)*0.00012)
    p[30:]=p[29]
    e=study.dc_events_for_session(synthetic_session(p),"X",20.0)
    kinds=[x["event_type"] for x in e]
    assert "confirmation" in kinds
    assert "overshoot" in kinds


def test_synthetic_summary_can_pass_common_scale():
    rows=[]
    for symbol in study.SYMBOLS:
        for scale in study.SCALES_BP:
            for year in study.YEARS:
                for _ in range(40):
                    rows.append({"symbol":symbol,"scale_bp":scale,"year":year,
                        "event_type":"overshoot","direction":"UP",
                        "signed_F5_bp":-4.0,"signed_F15_bp":-5.0,"reversal5":True})
                    rows.append({"symbol":symbol,"scale_bp":scale,"year":year,
                        "event_type":"overshoot","direction":"DOWN",
                        "signed_F5_bp":-4.0,"signed_F15_bp":-5.0,"reversal5":True})
                    rows.append({"symbol":symbol,"scale_bp":scale,"year":year,
                        "event_type":"confirmation","direction":"UP",
                        "signed_F5_bp":1.0,"signed_F15_bp":2.0,"reversal5":False})
    _,_,d=study.summarize(pd.DataFrame(rows))
    assert d["verdict"]=="broad_signal_source_supported"
