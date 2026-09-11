from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_v18.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v18", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_frozen_design_constants():
    mod = load_runner()
    assert mod.SYMBOLS == ("000688.SH", "000852.SH")
    assert mod.REF_YEARS == (2020, 2021, 2022, 2023)
    assert mod.DEV_YEARS == (2021, 2022, 2023)
    assert mod.SOURCE_STATES == ("NORMAL", "RECOVERING")
    assert mod.LEADS == (60, 30, 15, 6, 3)
    assert mod.PRIMARY_LEAD == 15
    assert mod.FROZEN_V9_BLOB == "ae2a7e095df58692ef9df0dfee5856cac727ca44"


def test_confusion_metrics_include_missing_targets_as_not_detected():
    mod = load_runner()
    x = pd.DataFrame({
        "final_switch_on": [True, True, False, False],
        "switch_on_signal": [True, False, True, False],
        "checkpoint_available": [True, False, True, True],
        "partial_shock": [True, False, False, False],
        "partial_vol_ratio": [2.0, None, 1.6, 1.0],
    })
    s = mod.summarize(x, "x", "x")
    assert (s["tp"], s["fp"], s["fn"], s["tn"]) == (1, 1, 1, 1)
    assert s["precision"] == 0.5
    assert s["recall"] == 0.5
    assert s["false_positive_rate"] == 0.5
    assert s["checkpoint_coverage"] == 0.75


def test_evidence_curve_uses_fixed_checkpoint_order():
    mod = load_runner()
    candidates = pd.DataFrame({
        "candidate_id": ["a", "b", "c"],
        "final_switch_on": [True, True, False],
    })
    rows = []
    for cid in ["a", "b", "c"]:
        for lead in mod.LEADS:
            signal = (cid == "a" and lead in [30, 15, 6, 3]) or (cid == "b" and lead in [6, 3])
            rows.append({"candidate_id": cid, "lead_seconds": lead, "switch_on_signal": signal})
    curve = mod.evidence_curve(pd.DataFrame(rows), candidates)
    assert curve["earliest_detection_counts"]["30"] == 1
    assert curve["earliest_detection_counts"]["6"] == 1
    assert curve["late_forming_first_after_e15_count"] == 1
    assert curve["persistent_after_first_detection_rate"] == 1.0
