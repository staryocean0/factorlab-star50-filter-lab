from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

MOD = Path(__file__).resolve().parent / 'run_validation.py'
SPEC = importlib.util.spec_from_file_location('star50_v2_validation', MOD)
VAL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VAL)


def test_validation_horizon_is_frozen():
    assert VAL.START == '2024-01-01'
    assert VAL.END == '2026-08-21'
    assert VAL.YEARS == (2024, 2025, 2026)


def test_bootstrap_is_report_only_and_net_cost_is_two_legs():
    z = pd.DataFrame({
        'trading_day': ['2024-01-02', '2024-01-03'],
        'gross_bp': [4.0, 2.0],
    })
    q = VAL.day_block_bootstrap_net1(z)
    assert abs(q['mean_net_bp'] - 1.0) < 1e-12
    assert q['draws'] == 10_000
    assert q['seed'] == 20260908


def test_no_blackbox_or_threshold_menu_constants():
    source = MOD.read_text()
    assert "END = '2026-08-21'" in source
    assert "tail2_share_min': 0.50" in source
    assert "efficiency5_min': 0.60" in source
    assert "hold_min': 3" in source
    assert 'threshold_grid' not in source
