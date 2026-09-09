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
    # A missing 3-second source row creates a >3s crossed gap and invalidates
    # at least one sampled return; it is never filled as zero.
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


def test_future_target_does_not_cross_session():
    rows = []
    for session in ("2023-01-03/0", "2023-01-03/1"):
        for m in range(1, 121):
            rows.append({"symbol": "X", "session": session, "day": "2023-01-03",
                         "afternoon": int(session[-1]), "minute": m,
                         "return_bp": 2.0 if m > 1 else np.nan, "eligible": True})
    q = study.attach_future_targets(pd.DataFrame(rows))
    # Protocol evaluates t<=105; exactly 15 future rows are available there.
    assert np.isfinite(q.loc[(q.session == "2023-01-03/0") & (q.minute == 105), "future_rms15_bp"]).all()
    assert np.isnan(q.loc[(q.session == "2023-01-03/0") & (q.minute == 106), "future_rms15_bp"]).all()


def test_fixed_band_edges():
    assert study.band_label(-1.0) == "<=0"
    assert study.band_label(0.5) == "(0,1]"
    assert study.band_label(1.5) == "(1,2]"
    assert study.band_label(3.0) == ">2"
