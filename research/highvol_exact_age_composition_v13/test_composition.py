from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_composition.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v13", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_frozen_scope_and_horizons():
    m = load_runner()
    assert m.STATES == ("UNSAFE", "RECOVERING")
    assert m.HORIZONS == (15, 30, 60)
    assert m.DEV_YEARS == (2021, 2022, 2023)
    assert m.IN_WINDOW_AGES == tuple(range(1, 12))


def test_beta11_matches_v11_smoothing():
    m = load_runner()
    assert m.beta11(0, 1) == 1 / 3
    assert m.beta11(3, 8) == 4 / 10


def test_common_age_support_requires_both_states():
    m = load_runner()
    df = pd.DataFrame(
        {
            "recent_shock_age_bars": [1, 1, 2, 3, 3],
            "current_state": ["UNSAFE", "RECOVERING", "UNSAFE", "UNSAFE", "RECOVERING"],
            "normal_within_15m": [0, 1, 0, 1, 1],
            "normal_within_30m": [0, 1, 0, 1, 1],
            "normal_within_60m": [1, 1, 1, 1, 1],
        }
    )
    assert m.common_ages(df) == [1, 3]


def test_standardization_uses_common_age_weights():
    m = load_runner()
    rows = []
    # Same age distribution is imposed across states by standardization.
    for age, state, vals in [
        (1, "UNSAFE", [0, 0]),
        (1, "RECOVERING", [1, 1]),
        (2, "UNSAFE", [1, 1]),
        (2, "RECOVERING", [0, 0]),
    ]:
        for v in vals:
            rows.append(
                {
                    "recent_shock_age_bars": age,
                    "current_state": state,
                    "normal_within_15m": v,
                    "normal_within_30m": v,
                    "normal_within_60m": v,
                }
            )
    z = m.standardize_one(pd.DataFrame(rows), 60)
    assert z["common_exact_ages"] == [1, 2]
    assert abs(z["standardized"]["recovering_minus_unsafe_gap"]) < 1e-12
