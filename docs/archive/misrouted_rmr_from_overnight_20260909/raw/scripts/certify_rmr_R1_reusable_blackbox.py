#!/usr/bin/env python3
"""Low-bandwidth reusable blackbox certification for frozen R1.

The validator may read the current 2026 blackbox internally, but its only
scientific output is PASS / FAIL / INSUFFICIENT plus identity fingerprints.
It never writes counts, scores, subperiods, event rows, or probabilities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common
import evaluate_rmr_R1_parent_integrity_v2_holdout as frozen_eval

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json"
POLICY = ROOT / "docs/governance/reusable_three_role_data_policy_v1.json"
DEFAULT_HIST = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_BLACKBOX = ROOT / "archive/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R1_reusable_blackbox_parameter_freeze_v1.json"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R1_reusable_blackbox_certification_v1.json"
HIST_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
BLACKBOX_SHA = "307e48021ef4576c2b364a1309a8b0474d6ab783afee16be41edb975abaa6dcd"
BLACKBOX_START = "2026-01-05"
BLACKBOX_END = "2026-08-21"
SYMBOL = "000852.SH"
PAIRINGS = (("PAIR_A", "S1", "S2"), ("PAIR_B", "S2", "S3"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_freeze(path: Path) -> tuple[dict, dict]:
    protocol = load_json(PROTOCOL)
    policy = load_json(POLICY)
    freeze = load_json(path)
    if freeze["research_identity"] != "rmr_cross_scale_pullback_parent_integrity_v2":
        raise RuntimeError("blackbox candidate identity drifted")
    if freeze["selected_candidate_id"] != "R1_PARENT_COMPOSITE_1D":
        raise RuntimeError("blackbox candidate drifted")
    if freeze["blackbox_used_in_fit"] is not False:
        raise RuntimeError("blackbox contaminated final fit")
    expected = freeze["parameter_bundle_sha256"]
    check = dict(freeze)
    check.pop("parameter_bundle_sha256")
    if json_digest(check) != expected:
        raise RuntimeError("final parameter bundle digest mismatch")
    if policy["roles"]["BLACKBOX"]["allowed_output"] != ["PASS", "FAIL", "INSUFFICIENT"]:
        raise RuntimeError("blackbox output policy drifted")
    return protocol, freeze


def read_frame(path: Path, expected_sha: str, start: str, end: str) -> pd.DataFrame:
    actual = sha256(path)
    if actual != expected_sha:
        raise RuntimeError("input source identity mismatch")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", ">=", start), ("trading_day", "<=", end)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty or set(frame["symbol"].unique()) != {SYMBOL}:
        raise RuntimeError("input source empty or symbol drifted")
    if str(frame["trading_day"].min()) < start or str(frame["trading_day"].max()) > end:
        raise RuntimeError("input window boundary violated")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def combine(hist: pd.DataFrame, blackbox: pd.DataFrame) -> pd.DataFrame:
    if str(hist["trading_day"].max()) != "2025-12-31":
        raise RuntimeError("historical context end drifted")
    if str(blackbox["trading_day"].min()) != BLACKBOX_START or str(blackbox["trading_day"].max()) != BLACKBOX_END:
        raise RuntimeError("blackbox physical window incomplete")
    out = pd.concat([hist, blackbox], ignore_index=True).sort_values(["trading_day", "timestamp"], kind="mergesort")
    if out.duplicated(["symbol", "trading_day", "timestamp"]).any():
        raise RuntimeError("duplicate minute identity across historical and blackbox source")
    return out.reset_index(drop=True)


def resolved_blackbox(events: pd.DataFrame) -> pd.DataFrame:
    out = events.loc[
        events["outcome"].isin(["recovery", "failure"])
        & events["day"].between(BLACKBOX_START, BLACKBOX_END)
    ].copy()
    out["y"] = out["outcome"].eq("recovery").astype(int)
    cols = ["day", "severity", "abs_drift", "overlap", "parent_eff", "y"]
    return out[cols].replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


def pairing_pass(data: pd.DataFrame, frozen_pair: dict, minimum: int) -> tuple[bool, bool]:
    if len(data) < minimum:
        return False, False
    data = frozen_eval.add_frozen_integrity(data, frozen_pair["parent_feature_scaler"])
    y = data["y"].to_numpy(int)
    p_base = frozen_eval.frozen_predict(frozen_pair["severity_baseline_model"], data[["severity"]].to_numpy(float))
    p_cand = frozen_eval.frozen_predict(
        frozen_pair["selected_candidate_model"], data[["severity", "parent_integrity"]].to_numpy(float)
    )
    brier_ok = brier_score_loss(y, p_cand) < brier_score_loss(y, p_base)
    logloss_ok = log_loss(y, p_cand, labels=[0, 1]) < log_loss(y, p_base, labels=[0, 1])
    return True, bool(brier_ok and logloss_ok)


def decide(pair_results: dict[str, tuple[bool, bool]]) -> str:
    if not all(sample_ok for sample_ok, _ in pair_results.values()):
        return "INSUFFICIENT"
    if all(metric_ok for _, metric_ok in pair_results.values()):
        return "PASS"
    return "FAIL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--historical", type=Path, default=DEFAULT_HIST)
    ap.add_argument("--blackbox", type=Path, default=DEFAULT_BLACKBOX)
    ap.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    ap.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = ap.parse_args()

    protocol, freeze = validate_freeze(args.freeze.resolve())
    hist = read_frame(args.historical.resolve(), HIST_SHA, "2015-01-05", "2025-12-31")
    blackbox = read_frame(args.blackbox.resolve(), BLACKBOX_SHA, BLACKBOX_START, BLACKBOX_END)
    frame = combine(hist, blackbox)
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    thresholds = {k: float(v) for k, v in freeze["directional_change_thresholds"].items()}
    vol_ref = float(freeze["DEV_median_rvol20"])
    waves = {name: common.detect_waves(prices, thresholds[name]) for name in ("S1", "S2", "S3")}
    pair_results = {}
    for pair_id, lower, parent in PAIRINGS:
        events = common.r1_events(prices, days, waves[lower], waves[parent], vol_ref)
        data = resolved_blackbox(events)
        minimum = int(protocol["BLACKBOX"]["gate_each_pairing"]["minimum_resolved"][pair_id])
        pair_results[pair_id] = pairing_pass(data, freeze["pairings"][pair_id], minimum)
    decision = decide(pair_results)

    candidate_fingerprint = freeze["parameter_bundle_sha256"]
    protocol_fingerprint = sha256(PROTOCOL)
    query_id = hashlib.sha256(f"R1|{candidate_fingerprint}|{protocol_fingerprint}|{BLACKBOX_SHA}".encode()).hexdigest()[:20]
    receipt = {
        "schema_id": "factorlab_reusable_blackbox_certification_receipt@1.0",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "query_id": query_id,
        "candidate_fingerprint": candidate_fingerprint,
        "protocol_fingerprint": protocol_fingerprint,
        "blackbox_source_fingerprint": BLACKBOX_SHA,
        "blackbox_window": {"start": BLACKBOX_START, "end": BLACKBOX_END},
        "decision": decision,
        "details_released": False,
        "exact_metrics_released": False,
        "counts_released": False,
        "subperiods_released": False,
        "event_rows_released": False,
        "blackbox_remains_closed": True,
        "repeated_query_is_independent_OOS": False,
        "production_authority": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0 if decision == "PASS" else 2 if decision == "FAIL" else 3


if __name__ == "__main__":
    raise SystemExit(main())
