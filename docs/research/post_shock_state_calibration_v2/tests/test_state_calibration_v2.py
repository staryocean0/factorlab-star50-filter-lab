from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "docs/research/post_shock_state_calibration_v2/code/state_calibration_v2.py"
SPEC = importlib.util.spec_from_file_location("state_calibration_v2_tested", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


def test_state_boundaries_are_frozen():
    assert m.state_from_ratio(0.0) == "LOW_CANDIDATE"
    assert m.state_from_ratio(0.999999) == "LOW_CANDIDATE"
    assert m.state_from_ratio(1.0) == "RECOVERING"
    assert m.state_from_ratio(1.499999) == "RECOVERING"
    assert m.state_from_ratio(1.5) == "UNSAFE"
    assert m.state_from_ratio(float("nan")) is None


def test_rms_window_is_session_local_and_requires_full_support():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    got = m.rms_window(x, 5)
    assert np.isclose(got, np.sqrt(np.mean(x[:5] ** 2)))
    assert np.isnan(m.rms_window(x, 4))
    y = x.copy(); y[2] = np.nan
    assert np.isnan(m.rms_window(y, 5))
    assert np.isnan(m.rms_window(x, 7))


def test_wilson_interval_contains_empirical_probability():
    lo, hi = m.wilson_interval(4, 10)
    assert 0 <= lo <= 0.4 <= hi <= 1
    lo0, hi0 = m.wilson_interval(0, 10)
    assert lo0 == 0.0
    assert 0 < hi0 < 0.5


def _synthetic_surface() -> pd.DataFrame:
    rows = []
    specs = {
        "LOW_CANDIDATE": (0.8, 1),
        "RECOVERING": (1.2, 6),
        "UNSAFE": (1.8, 11),
    }
    for state, (current_ratio, unsafe_count) in specs.items():
        for i in range(12):
            future_state = "UNSAFE" if i < unsafe_count else "LOW_CANDIDATE"
            future_ratio = 1.8 if future_state == "UNSAFE" else 0.8
            rows.append({
                "event_id": f"{state}-{i}",
                "symbol": "000688.SH",
                "year": 2025,
                "checkpoint_min": 5,
                "current_ratio": current_ratio,
                "current_state": state,
                "eligible_5": True,
                "eligible_10": True,
                "future_ratio_5": future_ratio,
                "future_ratio_10": future_ratio,
                "future_state_5": future_state,
                "future_state_10": future_state,
            })
    return pd.DataFrame(rows)


def test_monotone_synthetic_surface_is_supported_when_all_strata_sufficient():
    surface = _synthetic_surface()
    risk = m.state_risk_table(surface)
    elapsed = m.elapsed_time_table(surface)
    result = m.adjudicate(risk, elapsed)
    assert result["adjudication"] == "state_calibration_supported"
    assert all(item["monotone"] for item in result["pooled_monotonicity"])
    assert result["clean_transition_validated"] is False


def test_cluster_bootstrap_is_event_clustered_and_deterministic():
    surface = _synthetic_surface()
    a = m.cluster_bootstrap_contrasts(surface)
    b = m.cluster_bootstrap_contrasts(surface)
    pd.testing.assert_frame_equal(a, b)
    assert set(a.cluster_unit) == {"event_id"}
    assert (a.bootstrap_draws_valid > 0).all()
    assert (a.seed == m.SEED).all()
