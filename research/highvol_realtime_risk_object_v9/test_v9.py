from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_v9.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v9", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_upstream_state_constants_are_frozen():
    m = load_runner()
    assert m.RV_WINDOW == 12
    assert m.BG_WINDOW == 48
    assert m.HIGHVOL_RATIO == 1.50
    assert m.RECOVERY_NORMAL_RATIO == 1.10
    assert m.SHOCK_SIGMA == 3.00
    assert m.PRIMARY_LEAD_SECONDS == 3


def test_v6_probability_table_is_exactly_frozen():
    m = load_runner()
    assert m.PROB[("UNSAFE", "LT15")] == 0.007067137809187279
    assert m.PROB[("UNSAFE", "M15_25")] == 0.007751937984496124
    assert m.PROB[("UNSAFE", "M30_40")] == 0.01340033500837521
    assert m.PROB[("UNSAFE", "GE45")] == 0.5284210526315789
    assert m.PROB[("RECOVERING", "LT15")] == 0.05555555555555555
    assert m.PROB[("RECOVERING", "M15_25")] == 0.04879679144385027
    assert m.PROB[("RECOVERING", "M30_40")] == 0.08446215139442231
    assert m.PROB[("RECOVERING", "GE45")] == 0.7555919258046918


def test_age_buckets_match_v6():
    m = load_runner()
    assert m.age_bucket(1) == "LT15"
    assert m.age_bucket(2) == "LT15"
    assert m.age_bucket(3) == "M15_25"
    assert m.age_bucket(5) == "M15_25"
    assert m.age_bucket(6) == "M30_40"
    assert m.age_bucket(8) == "M30_40"
    assert m.age_bucket(9) == "GE45"


def test_development_and_support_screen_are_fixed():
    m = load_runner()
    assert m.DEV_YEARS == (2021, 2022, 2023)
    assert m.REF_YEARS == (2020, 2021, 2022, 2023)
    assert m.MIN_POOLED_COVERAGE == 0.98
    assert m.MIN_ANNUAL_COVERAGE == 0.95
    assert m.MAX_POOLED_PROB_MAE == 0.01
    assert m.MAX_POOLED_BRIER_DEGRADATION == 0.002
    assert m.MAX_ANNUAL_BRIER_DEGRADATION == 0.005
