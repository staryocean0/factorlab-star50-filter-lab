#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/degree_trajectory_utility_v1"
DECISION = "ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED"
MODEL_SHA = "04b49e8613cad5b24822f8e827f8d6513f6fef74da5c2df0851e03473b4db188"
VALIDATION_SHA = "16e7db8b780f64cfa0fcc5091d3ab1feed4c63658465697381b2ae9dda390763"
PROTOCOL_BLOB = "fe2eebaa6b15c3f9a57ce05b3295b015acba7ea7"
RUNNER_BLOB = "0afc45e5061f45f544ecc7ee4519eae4e5204bca"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def main() -> int:
    state = load("PROGRAM_STATE.json")
    receipt = load("EXECUTION_RECEIPT.json")
    decisive = load("DECISIVE_RECEIPT.json")
    validation = load("evidence/VALIDATION_RESULTS.json")
    source = load("evidence/EVIDENCE_SOURCE.json")

    assert state["state"] == DECISION
    assert receipt["decision"] == DECISION
    assert decisive["decision"] == DECISION
    assert validation["decision"] == DECISION

    assert git_blob(BASE / "PROTOCOL.md") == PROTOCOL_BLOB
    assert git_blob(BASE / "run_study.py") == RUNNER_BLOB
    assert sha256(BASE / "evidence/FROZEN_MODELS.json") == MODEL_SHA
    assert (BASE / "evidence/MODEL_SHA256.txt").read_text(encoding="utf-8").strip() == MODEL_SHA
    assert sha256(BASE / "evidence/VALIDATION_RESULTS.json") == VALIDATION_SHA

    assert source["decisive_run_id"] == 34680352701
    assert source["fit_job_id"] == 103517762036
    assert source["validation_job_id"] == 103517878447
    assert source["fit_artifact_id"] == 10293132822
    assert source["validation_artifact_id"] == 10294052627
    assert source["frozen_models_sha256"] == MODEL_SHA
    assert source["validation_results_sha256"] == VALIDATION_SHA
    assert source["source_artifact_copied_byte_for_byte"] is True

    assert validation["model_sha256"] == MODEL_SHA
    assert validation["validation_years"] == [2024, 2025]
    assert validation["validation_reused"] is True
    assert validation["fresh_oos"] is False
    assert validation["read_2026"] is False
    assert validation["blackbox_queried"] is False
    assert validation["pnl_computed"] is False
    assert validation["candidate_nominated"] is False
    assert validation["production_authority"] is False
    assert validation["v20_started"] is False
    assert validation["d6_started"] is False

    assert len(validation["comparisons"]) == 12
    assert len(validation["joint_endpoint_support"]) == 6
    assert not any(validation["joint_endpoint_support"].values())
    for row in validation["comparisons"]:
        assert row["relative_gain"] < 0.01
        assert row["supported"] is False
        if row["endpoint"] == "future_tail":
            assert row["absolute_gain"] < 0.0005

    for h in ("15", "30", "60"):
        assert validation["coverage"][h]["development"]["coverage"] >= 0.95
        assert validation["coverage"][h]["validation"]["coverage"] >= 0.95

    assert state["base_columns"] == 84
    assert state["trajectory_columns"] == 104
    assert state["lag2_control_columns"] == 104
    assert state["trajectory_control_complexity_matched"] is True
    assert state["lag1_delta_raw_information_bijective"] is True
    assert state["trajectory_practical_increment_supported"] is False
    assert state["trajectory_advantage_vs_lag2_supported"] is False
    assert state["delta_independent_predictive_promotion"] is False
    assert state["d5_contract_unchanged"] is True
    assert state["trajectory_spec_closed"] is True
    assert state["posthoc_rescue_authorized"] is False
    assert decisive["posthoc_rescue_forbidden"] is True
    assert decisive["consumer_logic_change"] is False

    results = (BASE / "RESULTS.md").read_text(encoding="utf-8")
    assert DECISION in results
    assert "1%" in results
    assert "D4/D5" in results
    assert "delta" in results.lower()
    assert "independent predictive promotion" in results

    print("degree trajectory utility V1 authority: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
