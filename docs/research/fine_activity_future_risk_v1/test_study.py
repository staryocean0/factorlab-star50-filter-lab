import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("study", HERE / "run_study.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_sample_session_requires_strict_gap():
    t = np.arange(0, 721, 3, dtype=float)
    p = 100 * np.exp(0.00001 * np.arange(len(t)))
    r = np.arange(len(t))
    x = study.sample_session(t, p, r)
    assert np.isfinite(x["return_bp"][1:49]).all()
    keep = t != 360
    y = study.sample_session(t[keep], p[keep], r[keep])
    assert np.isnan(y["return_bp"]).sum() > np.isnan(x["return_bp"]).sum()


def test_clock_z_is_strictly_past_only():
    rows = []
    for d in range(1, 5):
        rows.append({"symbol": "X", "afternoon": 0, "minute": 35,
                     "day": f"2023-01-0{d}", "A5": float(d)})
    f = pd.DataFrame(rows)
    z = study.attach_clock_z(f, "A5", "M3", min_history=2)
    assert np.isnan(z.loc[0, "M3"]) and np.isnan(z.loc[1, "M3"])
    prior = np.log(np.array([1.0, 2.0]))
    med = np.median(prior)
    mad = np.median(np.abs(prior - med))
    expected = (np.log(3.0) - med) / max(1.4826 * mad, 1e-8)
    assert abs(z.loc[2, "M3"] - expected) < 1e-12


def synthetic_panel(symbols=("X",), sessions=("2023-01-03/0", "2023-01-03/1")):
    rows = []
    for symbol in symbols:
        for session in sessions:
            for m in range(1, 121):
                rows.append({"symbol": symbol, "session": session, "day": "2023-01-03",
                             "afternoon": int(session[-1]), "minute": m,
                             "return_bp": 2.0 if m > 1 else np.nan, "eligible": True})
    return pd.DataFrame(rows)


def test_future_target_does_not_cross_session():
    q = study.attach_future_targets(synthetic_panel())
    assert np.isfinite(q.loc[(q.session == "2023-01-03/0") & (q.minute == 105), "future_rms15_bp"]).all()
    assert np.isnan(q.loc[(q.session == "2023-01-03/0") & (q.minute == 106), "future_rms15_bp"]).all()


def test_future_target_separates_symbols_with_same_session_name():
    q = study.attach_future_targets(synthetic_panel(symbols=("X", "Y"), sessions=("2023-01-03/0",)))
    assert len(q) == 240
    for symbol in ("X", "Y"):
        z = q[(q.symbol == symbol) & (q.session == "2023-01-03/0")]
        assert len(z) == 120
        assert np.isfinite(z.loc[z.minute == 105, "future_rms15_bp"]).all()


def test_fixed_band_edges():
    assert study.band_label(-1.0) == "<=0"
    assert study.band_label(0.5) == "(0,1]"
    assert study.band_label(1.5) == "(1,2]"
    assert study.band_label(3.0) == ">2"
