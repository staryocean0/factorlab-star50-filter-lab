from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_adjudication.py"
PROTOCOL = HERE / "PROTOCOL.md"


def load_runner():
    spec = importlib.util.spec_from_file_location("v15_adjudication", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_frozen_dimensions_and_cohort():
    mod = load_runner()
    assert mod.DEV_YEARS == (2021, 2022, 2023)
    assert mod.HORIZONS == (15, 30, 60)
    assert mod.STATES == ("UNSAFE", "RECOVERING")
    assert mod.BUCKETS == ("LT15", "M15_25", "M30_40", "GE45")
    assert mod.EXPECTED_ROWS == 7327
    assert mod.MIN_TRAIN_CELL_N == 50


def test_bootstrap_contract_is_frozen():
    mod = load_runner()
    assert mod.BOOTSTRAP_REPS == 10_000
    assert mod.BOOTSTRAP_SEED == 20260910
    assert mod.V11_RUNNER_BLOB == "713f0dcc41e7f32f75934fc7709a406ff71579e6"


def test_protocol_preregisters_short_vs_long_horizon_adjudication():
    text = PROTOCOL.read_text()
    assert "15m, pooled Brier-improvement bootstrap 95% CI lower bound is `> 0`" in text
    assert "30m, pooled Brier-improvement bootstrap 95% CI lower bound is `> 0`" in text
    assert "60m, the pooled Brier-improvement bootstrap 95% CI **contains 0**" in text
    assert "10000" in text
    assert "20260910" in text


def test_no_strategy_or_validation_execution_is_authorized():
    text = PROTOCOL.read_text()
    assert "Validation is not queried in V15" in text
    assert "BlackBox is not queried" in text
    assert "no PnL or trading rule is created" in text
    assert "production_authority=false" in text
