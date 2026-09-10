from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_survival.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v11_survival", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixed_horizons_and_full_support():
    m = load_runner()
    assert m.HORIZONS == (15, 30, 60)
    assert m.HORIZON_BARS == {15: 3, 30: 6, 60: 12}


def test_inherited_state_thresholds_are_frozen():
    m = load_runner()
    assert m.RV_WINDOW == 12
    assert m.BG_WINDOW == 48
    assert m.HIGHVOL_RATIO == 1.50
    assert m.RECOVERY_NORMAL_RATIO == 1.10
    assert m.SHOCK_SIGMA == 3.00


def test_recent_shock_age_buckets_are_frozen():
    m = load_runner()
    assert m.BUCKETS == ("LT15", "M15_25", "M30_40", "GE45")
    assert m.age_bucket(1) == "LT15"
    assert m.age_bucket(2) == "LT15"
    assert m.age_bucket(3) == "M15_25"
    assert m.age_bucket(5) == "M15_25"
    assert m.age_bucket(6) == "M30_40"
    assert m.age_bucket(8) == "M30_40"
    assert m.age_bucket(9) == "GE45"


def test_development_boundary_and_role_are_fixed():
    m = load_runner()
    assert m.WARMUP_YEAR == 2020
    assert m.DEV_YEARS == (2021, 2022, 2023)
    assert m.REF_YEARS == (2020, 2021, 2022, 2023)
    assert m.STATES == ("UNSAFE", "RECOVERING")
    assert m.MIN_CELL_N == 100
