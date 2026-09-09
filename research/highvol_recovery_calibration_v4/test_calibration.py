from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_calibration.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("recovery_calibration_v4", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_frozen_model_class():
    m = load_mod()
    assert m.STATES == ("UNSAFE", "RECOVERING")
    assert m.LANDMARKS == (1, 3, 6, 9)
    assert m.MIN_CELL_N == 100


def test_laplace_probability():
    m = load_mod()
    assert m.smooth(0, 100) == 1 / 102
    assert m.smooth(100, 100) == 101 / 102
    assert m.smooth(4, 8) == 0.5
