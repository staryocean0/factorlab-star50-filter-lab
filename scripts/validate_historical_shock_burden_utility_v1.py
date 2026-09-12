#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/historical_shock_burden_utility_v1"
DECISION = "HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED"
MODEL_SHA = "65f9403e3aae00873432403f833c1d8772429c5172fc7f3fd76581a19a4222d3"
VALIDATION_SHA = "8fa3f332a033e8f57ebf3240e3891295444dd9b48a8e2f699e2244928eb2f8bd"
PROTOCOL_BLOB = "3f093d702d069ffd4488fec222dded3f80bcedd1"
RUNNER_BLOB = "3607f4f56ece54b745741611e8e9d7fe236dc4ec"


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
    assert validation["decision"] == DECISION
    assert receipt["decision"] == DECISION
    assert decisive["decision"] == DECISION

    assert git_blob(BASE / "PROTOCOL.md") == PROTOCOL_BLOB
    assert git_blob(BASE / "run_study.py") == RUNNER_BLOB
    assert sha256(BASE / "evidence/FROZEN_MODELS.json") == MODEL_SHA
    assert (BASE / "evidence/MODEL_SHA256.txt").read_text(encoding="utf-8").strip() == MODEL_SHA
    assert sha256(BASE / "evidence/VALIDATION_RESULTS.json") == VALIDATION_SHA

    assert source["validation_results_sha256"] == VALIDATION_SHA
    assert source["frozen_models_sha256"] == MODEL_SHA
    assert source["decisive_run_id"] == 34679293167
    assert source["validation_artifact_id"] == 10294046103

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

    assert state["shock_specific_memory_practical_increment_supported"] is False
    assert state["consumer_promotion"] is False
    assert state["memory_spec_closed"] is True
    assert state["posthoc_rescue_authorized"] is False
    assert decisive["posthoc_rescue_forbidden"] is True
    assert decisive["consumer_promotion"] is False

    results = (BASE / "RESULTS.md").read_text(encoding="utf-8")
    assert DECISION in results
    assert "1%" in results
    assert "D5" in results and ("No D5 field is added" in results or "不进入 D5" in results)

    print("historical shock-burden utility V1 authority: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
