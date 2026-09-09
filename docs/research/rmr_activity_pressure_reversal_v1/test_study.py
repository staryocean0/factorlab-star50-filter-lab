import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("study", HERE / "run_study.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_panel_return_sign():
    frame = pd.DataFrame({
        "symbol": ["X"]*120,
        "market_time_shanghai": pd.date_range("2023-01-03 09:30", periods=120, freq="min", tz="Asia/Shanghai"),
        "trading_day": ["2023-01-03"]*120,
        "close": np.exp(np.arange(120)*0.0001),
        "amount": np.ones(120)*100,
        "high_frequency_analysis_eligible": [True]*120,
    })
    q = study.make_panel(frame, "X")
    assert len(q) == 120
    assert np.nanmedian(q.return_bp) > 0


def test_synthetic_pressure_reversal_passes_gate():
    rows = []
    for symbol in study.SYMBOLS:
        for year in study.YEARS:
            for state in ("ElevatedActivity", "NormalActivity"):
                for sev in ("moderate", "extreme"):
                    for direction in ("UP", "DOWN"):
                        n = 30
                        signed = -2.0 if state == "ElevatedActivity" else 0.5
                        for i in range(n):
                            rows.append({
                                "symbol": symbol, "year": year, "activity_state": state,
                                "severity_view": sev, "direction": direction,
                                "signed_F5_bp": signed, "signed_F15_bp": signed,
                                "reversal5": bool(signed < 0), "severity": 2.5 if sev == "moderate" else 3.5,
                            })
    annual, views, decision = study.summarize(pd.DataFrame(rows))
    assert decision["verdict"] == "broad_signal_source_supported"
    assert len(annual) == 12
    assert len(views) == 16
