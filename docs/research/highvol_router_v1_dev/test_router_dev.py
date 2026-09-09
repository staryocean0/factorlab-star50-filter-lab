from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("router_v1", HERE / "run_router_dev.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_frozen_identity_is_not_a_menu():
    assert mod.FROZEN == {
        "highvol_ratio_min": 1.5,
        "highvol_fast_window_min": 5,
        "highvol_background_window_min": 30,
        "highvol_background_floor_bp": 1.0,
        "slow_window_min": 30,
        "tail2_share_min": 0.60,
        "tail1_share_max_exclusive": 0.60,
        "hold_min": 3,
        "cost_bp_per_leg": 1.0,
    }
    assert mod.DEV_YEARS == (2021, 2022, 2023)
    assert mod.SYMBOL == "000852.SH"


def test_nonoverlap_matches_frozen_selector_semantics():
    q = pd.DataFrame({
        "session": ["s", "s", "s", "t"],
        "onset_row": [10, 12, 14, 5],
        "entry_minute": [12, 14, 16, 7],
        "exit_minute": [15, 17, 19, 10],
        "gross_3m_bp": [1.0, 2.0, 3.0, 4.0],
    })
    out = mod.apply_nonoverlap(q, 3)
    assert out.onset_row.tolist() == [10, 14, 5]


def test_drawdown_is_cumulative_net_path():
    assert mod.max_drawdown_bp(np.array([3.0, -2.0, -4.0, 5.0])) == 6.0


def test_router_contract_star50_is_explicit_no_trade():
    contract = json.loads((HERE / "router_contract.json").read_text())
    assert contract["routes"]["000852.SH"]["route"] == "ACTIVE_LONG_3M"
    assert contract["routes"]["000688.SH"]["route"] == "NO_TRADE"
    assert contract["routes"]["other_highvol_contexts"]["route"] == "NO_TRADE"
    assert contract["production_authority"] is False
    assert contract["data_roles"]["blackbox_queried"] is False
