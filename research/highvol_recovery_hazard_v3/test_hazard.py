from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_hazard.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("highvol_recovery_hazard_v3", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_frozen_state_and_hazard_design():
    m = load_mod()
    assert m.SYMBOLS == ("000688.SH", "000852.SH")
    assert m.WARMUP_YEAR == 2020
    assert m.DEV_YEARS == (2021, 2022, 2023)
    assert m.RV_WINDOW == 12
    assert m.BG_WINDOW == 48
    assert m.HIGHVOL_RATIO == 1.50
    assert m.EXTREME_RATIO == 2.25
    assert m.RECOVERY_NORMAL_RATIO == 1.10
    assert m.SHOCK_SIGMA == 3.00
    assert m.LANDMARKS == (1, 3, 6, 9)
    assert m.FUTURE_BARS == 3


def test_future_outcome_recovery_without_recurrence():
    m = load_mod()
    day = pd.DataFrame(
        {
            "risk_state": ["UNSAFE", "RECOVERING", "NORMAL", "NORMAL", "NORMAL"],
            "shock": [False, False, False, False, False],
        }
    )
    got = m._future_outcome(day, 0)
    assert got["hazard_supported"] is True
    assert got["normal_within_next15"] is True
    assert got["shock_before_normal_next15"] is False
    assert got["non_normal_after15"] is False


def test_future_outcome_counts_recurrence_before_normal():
    m = load_mod()
    day = pd.DataFrame(
        {
            "risk_state": ["UNSAFE", "UNSAFE", "RECOVERING", "NORMAL", "NORMAL"],
            "shock": [False, True, False, False, False],
        }
    )
    got = m._future_outcome(day, 0)
    assert got["hazard_supported"] is True
    assert got["normal_within_next15"] is True
    assert got["shock_before_normal_next15"] is True


def test_future_outcome_censors_short_session_tail():
    m = load_mod()
    day = pd.DataFrame(
        {
            "risk_state": ["UNSAFE", "RECOVERING"],
            "shock": [False, False],
        }
    )
    got = m._future_outcome(day, 0)
    assert got["hazard_supported"] is False
    assert got["normal_within_next15"] is None
    assert got["shock_before_normal_next15"] is None
    assert got["non_normal_after15"] is None
