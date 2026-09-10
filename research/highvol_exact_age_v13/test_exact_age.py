from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_exact_age.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v13_exact_age", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_exact_age_support_is_structural():
    m = load_runner()
    assert m.RV_WINDOW == 12
    assert m.EXACT_AGES == tuple(range(1, 12))


def test_fixed_development_years_and_states():
    m = load_runner()
    assert m.YEARS == (2021, 2022, 2023)
    assert m.STATES == ("UNSAFE", "RECOVERING")


def test_beta_smoothing_fixed():
    m = load_runner()
    assert m.beta_prob(0, 0) == 0.5
    assert m.beta_prob(4, 8) == 0.5


def test_v12_lineage_is_explicit():
    m = load_runner()
    assert m.V12_RUNNER.name == "run_expiry.py"
