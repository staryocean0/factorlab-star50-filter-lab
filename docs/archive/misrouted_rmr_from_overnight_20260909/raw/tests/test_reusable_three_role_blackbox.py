import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import certify_rmr_R1_reusable_blackbox as blackbox
import evaluate_rmr_R1_parent_integrity_v2_holdout as frozen_eval


def test_three_role_windows_and_reuse_semantics():
    policy = json.loads((ROOT / "docs/governance/reusable_three_role_data_policy_v1.json").read_text())
    assert policy["roles"]["DEV"]["window"] == {"start": "2015-01-05", "end": "2020-12-31"}
    assert policy["roles"]["VALIDATION"]["window"] == {"start": "2021-01-01", "end": "2025-12-31"}
    assert policy["roles"]["BLACKBOX"]["window"] == {"start": "2026-01-05", "end": "2026-08-21"}
    assert policy["roles"]["BLACKBOX"]["allowed_output"] == ["PASS", "FAIL", "INSUFFICIENT"]
    assert policy["reusability_and_multiplicity"]["same_blackbox_may_be_reused"] is True
    assert policy["reusability_and_multiplicity"]["repeated_queries_are_not_independent_new_OOS_samples"] is True
    assert policy["future_data"]["do_not_wait_for_or_assume_unannounced_new_data"] is True


def test_dev_validation_runner_cannot_read_blackbox_source_directly():
    source = (ROOT / "scripts/run_rmr_R1_reusable_dev_validation.py").read_text(encoding="utf-8")
    assert "archive/data/gap_fill_repeat_2026" not in source
    assert "filters=[(\"trading_day\", \"<=\", VAL_END)]" in source
    assert "DEV/VALIDATION runner read blackbox rows" in source


def test_blackbox_decision_is_three_state_only():
    assert blackbox.decide({"A": (True, True), "B": (True, True)}) == "PASS"
    assert blackbox.decide({"A": (True, True), "B": (True, False)}) == "FAIL"
    assert blackbox.decide({"A": (False, False), "B": (True, True)}) == "INSUFFICIENT"


def test_blackbox_receipt_source_does_not_emit_metrics_or_counts():
    source = (ROOT / "scripts/certify_rmr_R1_reusable_blackbox.py").read_text(encoding="utf-8")
    receipt_section = source.split("receipt = {", 1)[1].split("args.receipt.parent", 1)[0]
    for forbidden in ("brier", "logloss", "resolved", "n_events", "by_year", "by_month", "probabilities"):
        assert forbidden not in receipt_section.lower()
    assert '"decision": decision' in receipt_section
    assert '"counts_released": False' in receipt_section
    assert '"details_released": False' in receipt_section


def test_blackbox_pairing_internal_gate_works_without_releasing_detail():
    rows = []
    for _ in range(25):
        rows.append({"day": "2026-03-02", "severity": 1.0, "abs_drift": 3.0, "overlap": 0.0, "parent_eff": 0.0, "y": 1})
        rows.append({"day": "2026-03-03", "severity": 1.0, "abs_drift": 0.0, "overlap": 3.0, "parent_eff": 0.0, "y": 0})
    data = pd.DataFrame(rows)
    frozen_pair = {
        "parent_feature_scaler": {"mean": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
        "severity_baseline_model": {
            "scaler": {"mean": [0.0], "scale": [1.0]},
            "logistic": {"coef": [0.0], "intercept": 0.0},
        },
        "selected_candidate_model": {
            "scaler": {"mean": [0.0, 0.0], "scale": [1.0, 1.0]},
            "logistic": {"coef": [0.0, 2.0], "intercept": 0.0},
        },
    }
    sample_ok, metric_ok = blackbox.pairing_pass(data, frozen_pair, minimum=40)
    assert sample_ok is True
    assert metric_ok is True
    sample_ok, metric_ok = blackbox.pairing_pass(data.iloc[:10], frozen_pair, minimum=40)
    assert sample_ok is False
    assert metric_ok is False


def test_query_ledger_is_low_bandwidth_and_append_only():
    ledger = json.loads((ROOT / "docs/governance/reusable_blackbox_query_ledger_v1.json").read_text())
    assert ledger["query_count"] == len(ledger["queries"])
    assert ledger["query_count"] >= 1
    assert ledger["rules"]["append_only"] is True
    assert ledger["rules"]["no_exact_blackbox_metric_storage"] is True
    assert ledger["rules"]["no_subperiod_or_error_detail_storage"] is True
    for q in ledger["queries"]:
        assert q["decision"] in {"PASS", "FAIL", "INSUFFICIENT"}
        assert q["details_released"] is False
        assert q["independent_new_OOS_sample"] is False
        assert "candidate_fingerprint" in q
        assert "protocol_fingerprint" in q
        forbidden = {"brier", "logloss", "mean_return", "count", "year", "month", "event_rows"}
        assert not forbidden.intersection(q.keys())
