#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/intrabar_temporal_reversal_utility_v1"
DECISION = "INTRABAR_TEMPORAL_REVERSAL_INCREMENTAL_UTILITY_NOT_SUPPORTED"
PROTOCOL_BLOB = "f801991737fb1dc043807cb5f3e4fd9fb17f1187"
RUNNER_BLOB = "b7d1f158883b6e2c30e2eaca59e3a010864d572b"
TEST_BLOB = "8faeaae8fe2764872748df01bee550863bef3092"
PARENT_BLOB = "0afc45e5061f45f544ecc7ee4519eae4e5204bca"
MODEL_SHA = "bd01e23def9300781c64a03f8377247ff30c67d0191c6cd213329d382ff8262c"
FIT_SHA = "39186882be4b257da3ee7ca74ee23daa9454e19d498fd21190d198e7e9c46dea"
MODEL_SHA_FILE_SHA = "e84298b5743a93306450d7789e020eb24434e9eb1eeb251bd457efdcc4873cb7"
COMPARISONS_SHA = "cc072efdfc215e15a11ba68c6e2ab694a9eb513941d2a99ca5b4f7460c174cf4"
VALIDATION_SHA = "67b267af11802562f4f576d151472b064323c82af2a34e4451e471beb99b2cdc"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def main() -> int:
    state = load("PROGRAM_STATE.json")
    execution = load("EXECUTION_RECEIPT.json")
    decisive = load("DECISIVE_RECEIPT.json")
    source = load("evidence/EVIDENCE_SOURCE.json")
    fit = load("evidence/FIT_RECEIPT.json")

    assert state["state"] == DECISION
    assert execution["decision"] == DECISION
    assert decisive["decision"] == DECISION

    assert git_blob(BASE / "PROTOCOL.md") == PROTOCOL_BLOB
    assert git_blob(BASE / "run_study.py") == RUNNER_BLOB
    assert git_blob(BASE / "test_study.py") == TEST_BLOB
    assert git_blob(ROOT / "research/degree_trajectory_utility_v1/run_study.py") == PARENT_BLOB

    assert sha256(BASE / "evidence/FIT_RECEIPT.json") == FIT_SHA
    assert sha256(BASE / "evidence/MODEL_SHA256.txt") == MODEL_SHA_FILE_SHA
    assert (BASE / "evidence/MODEL_SHA256.txt").read_text(encoding="utf-8").strip() == MODEL_SHA
    assert sha256(BASE / "evidence/comparisons.csv") == COMPARISONS_SHA

    assert source["decisive_run_id"] == 34685234360
    assert source["fit_job_id"] == 103530973458
    assert source["validation_job_id"] == 103531117262
    assert source["fit_artifact_id"] == 10295610761
    assert source["validation_artifact_id"] == 10294993214
    assert source["frozen_models_sha256"] == MODEL_SHA
    assert source["fit_receipt_sha256"] == FIT_SHA
    assert source["validation_results_sha256"] == VALIDATION_SHA
    assert source["comparisons_csv_sha256"] == COMPARISONS_SHA
    assert source["protocol_git_blob"] == PROTOCOL_BLOB
    assert source["runner_git_blob"] == RUNNER_BLOB
    assert source["test_git_blob"] == TEST_BLOB
    assert source["parent_runner_git_blob"] == PARENT_BLOB
    assert source["source_main_commit"] == "b9a6a47b2aca8ea9dddec1aab69c19ae0ae92311"

    fi = fit["feature_identity"]
    assert fi["base_columns"] == 84
    assert fi["temporal_columns"] == 104
    assert fi["order_invariant_columns"] == 104
    assert fi["T_O_complexity_matched"] is True
    assert fi["current_bar_returns"] == 19
    assert fi["E15_current_bar_only"] is True
    assert fi["global_sign_invariant"] is True
    assert fi["control_permutation_invariant"] is True
    assert fi["same_row_availability"] is True
    assert fit["validation_scored"] is False
    assert fit["model_sha256"] == MODEL_SHA

    with (BASE / "evidence/comparisons.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 12
    assert all(r["supported"] == "False" for r in rows)
    assert all(float(r["relative_gain"]) < 0 for r in rows)
    assert all(float(r["absolute_gain"]) < 0 for r in rows)

    keys = {(int(r["horizon"]), r["endpoint"], r["comparison"]): r for r in rows}
    expected_o_rms = {
        15: -0.0339167205460284,
        30: -0.04877370521125941,
        60: -0.06135704873708821,
    }
    for h, expected in expected_o_rms.items():
        row = keys[(h, "log_future_sigma", "T_vs_O")]
        assert float(row["relative_gain"]) == expected
        assert float(row["development_forward_gain"]) < 0

    for h in (15, 30, 60):
        for endpoint in ("log_future_sigma", "future_tail"):
            assert (h, endpoint, "T_vs_C") in keys
            assert (h, endpoint, "T_vs_O") in keys

    assert int(keys[(60, "log_future_sigma", "T_vs_C")]["development_n"]) == 17549
    assert int(keys[(60, "future_tail", "T_vs_O")]["development_n"]) == 17549

    assert state["formal_comparison_count"] == 12
    assert state["formal_comparison_support_count"] == 0
    assert state["all_validation_point_estimates_negative"] is True
    assert state["60m_development_n_below_20000"] is True
    assert state["temporal_reversal_practical_increment_supported"] is False
    assert state["temporal_reversal_consumer_promotion"] is False
    assert state["single_index_rescue_authorized"] is False
    assert state["posthoc_order_feature_rescue_authorized"] is False
    assert state["intrabar_temporal_reversal_spec_closed"] is True
    assert state["signed_asymmetry_remains_closed"] is True
    assert state["multiscale_volatility_remains_closed"] is True
    assert state["d4_decision_unchanged"] is True
    assert state["d5_contract_unchanged"] is True
    assert state["v19_frozen"] is True

    for obj in (state, execution, source):
        assert obj["validation_reused"] is True
        assert obj["fresh_oos"] is False
        assert obj["read_2026"] is False
        assert obj["synthetic_2026_used"] is False
        assert obj["blackbox_queried"] is False
        assert obj["pnl_computed"] is False
        assert obj["production_authority"] is False

    results = (BASE / "RESULTS.md").read_text(encoding="utf-8")
    assert DECISION in results
    assert "all 12 pooled Validation point estimates are negative" in results
    assert "-6.13570%" in results
    assert "0.0005" in results
    assert "No temporal-reversal field or decision gate is added to D5" in results
    assert "synthetic_2026_used=false" in results

    sums = (BASE / "evidence/ARTIFACT_SHA256SUMS.txt").read_text(encoding="utf-8")
    assert f"{MODEL_SHA}  ./FROZEN_MODELS.json" in sums
    assert f"{VALIDATION_SHA}  ./VALIDATION_RESULTS.json" in sums
    assert f"{COMPARISONS_SHA}  ./comparisons.csv" in sums

    print("intrabar temporal reversal utility V1 authority: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
