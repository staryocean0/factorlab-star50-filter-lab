import importlib.util
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("v6full", HERE / "run_full_validation.py")
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(M)


def test_synthesize_5m_uses_fifth_close_in_each_session_block():
    day = "2023-01-03"
    am = pd.date_range(day + " 09:30:00", periods=120, freq="1min")
    pm = pd.date_range(day + " 13:00:00", periods=120, freq="1min")
    ts = am.append(pm)
    x = pd.DataFrame({"symbol":"000688.SH","trading_day":day,"timestamp":ts,"close":range(1,241)})
    y = M.synthesize_5m(x)
    assert len(y) == 48
    assert y.close.tolist()[:3] == [5.0, 10.0, 15.0]
    assert y.close.tolist()[24:27] == [125.0, 130.0, 135.0]
    assert y.close.iloc[-1] == 240.0


def test_age_bucket_frozen_boundaries():
    assert M.age_bucket(1) == "LT15"
    assert M.age_bucket(2) == "LT15"
    assert M.age_bucket(3) == "M15_25"
    assert M.age_bucket(5) == "M15_25"
    assert M.age_bucket(6) == "M30_40"
    assert M.age_bucket(8) == "M30_40"
    assert M.age_bucket(9) == "GE45"


def test_frozen_baseline_is_exact_development_event_rate():
    assert abs(M.BASELINE_P - 0.24650920005219887) < 1e-15
