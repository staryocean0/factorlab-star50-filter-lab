import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("study", HERE / "run_study.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_band_edges():
    assert study.band(0.5) == "low"
    assert study.band(1.0) == "low"
    assert study.band(1.5) == "mid"
    assert study.band(2.0) == "mid"
    assert study.band(2.1) == "high"


def test_ols_recovers_linear_relation():
    x = np.linspace(-2, 2, 100)
    y = 1.25 + 1.8 * x
    alpha, beta, resid = study.ols_alpha_beta(x, y)
    assert abs(alpha - 1.25) < 1e-12
    assert abs(beta - 1.8) < 1e-12
    assert np.max(np.abs(resid)) < 1e-12


def test_summarize_requires_both_directions_and_years():
    rows = []
    for year in study.YEARS:
        for direction, sign in (("STAR50_rich", 1), ("STAR50_cheap", -1)):
            for _ in range(120):
                rows.append({"year": year, "band": "high", "direction": direction,
                             "signed_F15_bp": -2.0, "recovery50": True})
            for _ in range(200):
                rows.append({"year": year, "band": "low", "direction": direction,
                             "signed_F15_bp": 0.2, "recovery50": False})
            for _ in range(150):
                rows.append({"year": year, "band": "mid", "direction": direction,
                             "signed_F15_bp": -0.2, "recovery50": False})
    annual, pooled, decision = study.summarize(pd.DataFrame(rows))
    assert decision["verdict"] == "broad_signal_source_supported"
    assert len(annual) == 9
    assert len(pooled) == 9
