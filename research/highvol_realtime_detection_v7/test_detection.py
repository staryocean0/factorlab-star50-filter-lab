from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_detection.py"


def load():
    spec = importlib.util.spec_from_file_location("v7", RUNNER)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def test_frozen_constants():
    m = load()
    assert m.OFFSETS == (1, 2, 3, 4)
    assert m.RV_WINDOW == 12
    assert m.BG_WINDOW == 48
    assert m.HIGHVOL_RATIO == 1.50
    assert m.RECOVERY_NORMAL_RATIO == 1.10
    assert m.SHOCK_SIGMA == 3.00
    assert m.POOLED_MIN_PRECISION == 0.90
    assert m.POOLED_MIN_RECALL == 0.90
    assert m.ANNUAL_MIN_PRECISION == 0.85
    assert m.ANNUAL_MIN_RECALL == 0.85


def test_state_transition_contract():
    m = load()
    assert m.transition("NORMAL", 1.0, False) == "NORMAL"
    assert m.transition("NORMAL", 1.0, True) == "UNSAFE"
    assert m.transition("UNSAFE", 1.6, False) == "UNSAFE"
    assert m.transition("UNSAFE", 1.3, False) == "RECOVERING"
    assert m.transition("UNSAFE", 1.1, False) == "NORMAL"
    assert m.transition("RECOVERING", 1.5, False) == "UNSAFE"
    assert m.transition("RECOVERING", 1.2, False) == "RECOVERING"
    assert m.transition("RECOVERING", 1.0, False) == "NORMAL"


def test_partial_offsets_are_not_parameter_menu():
    m = load()
    assert set(m.OFFSETS) == {1, 2, 3, 4}
    assert 5 not in m.OFFSETS
    assert 0 not in m.OFFSETS


def test_development_only_years():
    m = load()
    assert m.WARMUP_YEAR == 2020
    assert m.DEV_YEARS == (2021, 2022, 2023)
    assert m.ALL_YEARS == (2020, 2021, 2022, 2023)
