from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("router_val", HERE / "run_router_validation.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_freeze_receipt_binds_development_identity():
    freeze = json.loads((HERE / "FROZEN_ROUTER_V1.json").read_text())
    assert freeze["development"]["code_commit_sha"] == "33b2654e31ea8ac09711aeb77248ddfe68d9dea5"
    assert freeze["development"]["runner_blob_sha"] == "52aa0db330b3489c4196b6e718f8c7f6f8628d13"
    assert freeze["development"]["accepted_nonoverlap_trades"] == 104
    assert freeze["routes"]["000688.SH"] == "NO_TRADE"
    assert freeze["blackbox_queried"] is False


def test_validation_acceptance_is_existing_candidate_gate_plus_mechanics():
    freeze = json.loads((HERE / "FROZEN_ROUTER_V1.json").read_text())
    a = freeze["validation"]["acceptance"]
    assert a["pooled_completed_trades_min"] == 30
    assert a["positive_net_year_slices_min_of_3"] == 2
    assert a["pooled_one_way_break_even_gt_bp"] == 1.0
    assert a["star50_route_trade_count_equals"] == 0
    assert a["max_concurrent_positions_lte"] == 1
    assert freeze["validation"]["parameter_change_allowed"] is False


def test_validation_runner_reuses_frozen_dev_functions():
    dev = mod.load_dev()
    assert dev.FROZEN["tail2_share_min"] == 0.60
    assert dev.FROZEN["tail1_share_max_exclusive"] == 0.60
    assert dev.FROZEN["hold_min"] == 3
    assert dev.FROZEN["cost_bp_per_leg"] == 1.0
