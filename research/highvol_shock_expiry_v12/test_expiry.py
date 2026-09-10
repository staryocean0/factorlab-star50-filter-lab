from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_expiry.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v12_expiry", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_structural_window_cutoff_is_not_a_free_parameter():
    m = load_runner()
    assert m.RV_WINDOW == 12
    assert m.P60_BARS == 12
    assert m.FUTURE_BARS == 13
    assert m.POST_EXPIRY_BARS == 3


def test_development_boundary_is_fixed():
    m = load_runner()
    assert m.YEARS == (2021, 2022, 2023)
    assert m.STATES == ("UNSAFE", "RECOVERING")


def test_beta_smoothing_is_fixed():
    m = load_runner()
    assert m.beta_prob(0, 0) == 0.5
    assert m.beta_prob(1, 2) == 0.5
    assert m.beta_prob(9, 10) == 10 / 12


def test_v11_reference_is_inherited_not_redefined():
    m = load_runner()
    assert m.V11_RUNNER.name == "run_survival.py"
    assert m.MIN_STRATUM_STATE_N == 100
