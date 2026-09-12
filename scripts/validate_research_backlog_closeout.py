#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

EXPECTED = {
    "research/first-shock-actions-20260907",
    "research/highvol-realtime-detection-v7-20260910",
    "research/highvol-realtime-detection-v8-3s-20260910",
    "research/highvol-realtime-risk-object-v9-20260910",
    "research/highvol-realtime-probability-lead-v10-20260910",
    "research/highvol-realtime-probability-lead-v10-validation-20260910",
    "research/rmr-activity-pressure-reversal-v1-20260909",
    "research/rmr-lunch-boundary-normalization-v1-20260909",
    "research/session-aware-information-set-bounds-v0617-20260907",
    "research/highvol-recovery-survival-v11-20260911",
    "research/risk-gate-takeover-20260907",
    "research/highvol-router-v1-dev-20260909",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    p = root / "docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json"
    x = json.loads(p.read_text(encoding="utf-8"))
    assert x["schema"] == "research_backlog_closeout_20260912@1.0"
    assert x["current_scientific_breakpoint_unchanged"] == "CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED"
    assert x["closed_count"] == 12
    assert x["remaining_executable_backlog_count"] == 0
    rows = x["branches"]
    assert len(rows) == 12
    got = {r["branch"] for r in rows}
    assert got == EXPECTED, {"missing": sorted(EXPECTED-got), "extra": sorted(got-EXPECTED)}
    assert all(r.get("rerun_required") is False for r in rows)
    assert all(r.get("closeout_state") for r in rows)
    program = x["program_conclusion"]
    assert program["historical_backlog_closed"] is True
    assert program["remote_historical_branches_preserved"] is True
    assert program["historical_verdicts_rewritten"] is False
    assert program["new_scientific_candidate_created"] is False
    assert program["blackbox_queried"] is False
    assert program["pnl_newly_computed"] is False
    assert program["production_authority"] is False

    v0617 = next(r for r in rows if r["branch"].startswith("research/session-aware-information"))
    assert v0617["closeout_state"] == "V0617_PRIOR_IDENTITY_IRRECOVERABLE_REPLAY_PERMANENTLY_BLOCKED_UNDER_FROZEN_PROTOCOL"
    assert v0617["strict_identity_audit"]["required_precommit_identity_recovered"] is False
    assert v0617["scientific_replay_executed"] is False
    assert v0617["scientific_result_inferred"] is False

    router = next(r for r in rows if r["branch"] == "research/highvol-router-v1-dev-20260909")
    assert "RETIRED_OUT_OF_CURRENT_SCOPE" in router["closeout_state"]
    assert router["production_authority"] is False

    current = (root / "CURRENT_RESEARCH.md").read_text(encoding="utf-8")
    assert "CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED" in current
    assert "production_authority=false" in current

    receipt = json.loads((root / "docs/research/session_aware_information_set_bounds_v0617/CLOSEOUT_RECEIPT_20260912.json").read_text(encoding="utf-8"))
    assert receipt["decision"] == v0617["closeout_state"]
    assert receipt["audit"]["required_precommit_identity_recovered"] is False
    assert receipt["production_authority"] is False

    print("research backlog closeout: OK")
    print(f"closed={len(rows)} remaining={x['remaining_executable_backlog_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
