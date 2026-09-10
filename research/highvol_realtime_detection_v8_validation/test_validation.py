from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_validation.py"
FROZEN = HERE / "FROZEN_DETECTOR_V8.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("v8_validation", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_validation_boundary_is_fixed_available_subset():
    mod = load_runner()
    assert mod.VAL_YEARS == (2024, 2025)
    assert mod.REF_YEARS == (2020, 2021, 2022, 2023, 2024, 2025)
    assert mod.SYMBOLS == ("000688.SH", "000852.SH")


def test_primary_checkpoint_and_leads_are_frozen():
    mod = load_runner()
    assert mod.LEADS == (60, 30, 15, 6, 3)
    assert mod.PRIMARY_LEAD == 3


def test_frozen_detector_records_development_authority():
    frozen = json.loads(FROZEN.read_text())
    assert frozen["source_commit"] == "07bfa63018fe4d1a1afa4f108a14d9be5ae86777"
    assert frozen["development_run_id"] == 34426934097
    assert frozen["development_artifact_id"] == 10133063809
    assert frozen["source_runner_blob_sha"] == "9e1828a8e7ff6b45eba0b4d1e31e79c1f9c1568a"
    assert frozen["source_protocol_blob_sha"] == "a23728a029c17c28384d8ce372e73dac0d312944"


def test_no_tuning_or_trading_authority_in_frozen_contract():
    frozen = json.loads(FROZEN.read_text())
    assert frozen["threshold_search_performed"] is False
    assert frozen["state_thresholds_unchanged"] is True
    assert frozen["pnl_computed"] is False
    assert frozen["trading_rule_created"] is False
    assert frozen["production_authority"] is False
    assert frozen["development_acceptance"] == {
        "pooled_coverage_min": 0.95,
        "annual_coverage_min": 0.95,
        "pooled_unsafe_precision_min": 0.9,
        "pooled_unsafe_recall_min": 0.9,
        "annual_unsafe_precision_min": 0.85,
        "annual_unsafe_recall_min": 0.85,
    }
