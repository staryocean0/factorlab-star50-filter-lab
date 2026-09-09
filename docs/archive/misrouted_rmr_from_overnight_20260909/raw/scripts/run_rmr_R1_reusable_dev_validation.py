#!/usr/bin/env python3
"""R1 migration to reusable DEV / VALIDATION / BLACKBOX governance.

This runner reads only 2015-2025. It fits on DEV 2015-2020, reports detailed
VALIDATION 2021-2025 evidence, and only if both pairings pass performs the
predeclared final refit on DEV+VALIDATION. It never reads the 2026 blackbox.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common
import run_rmr_R1_parent_integrity_v2_selection as old

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json"
POLICY = ROOT / "docs/governance/reusable_three_role_data_policy_v1.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R1_reusable_validation_receipt_v1.json"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R1_reusable_blackbox_parameter_freeze_v1.json"
EXPECTED_SOURCE_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2020-12-31"
VAL_START = "2021-01-01"
VAL_END = "2025-12-31"
PAIRINGS = (("PAIR_A", "S1", "S2"), ("PAIR_B", "S2", "S3"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def json_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return None


def validate_contracts() -> dict:
    p = load_json(PROTOCOL)
    policy = load_json(POLICY)
    if p["research_identity"] != "rmr_cross_scale_pullback_parent_integrity_v2":
        raise RuntimeError("R1 identity drifted")
    if p["candidate"]["id"] != "R1_PARENT_COMPOSITE_1D":
        raise RuntimeError("R1 candidate drifted")
    if policy["roles"]["DEV"]["window"]["end"] != DEV_END:
        raise RuntimeError("DEV boundary drifted")
    if policy["roles"]["VALIDATION"]["window"] != {"start": VAL_START, "end": VAL_END}:
        raise RuntimeError("VALIDATION boundary drifted")
    if policy["roles"]["BLACKBOX"]["window"] != {"start": "2026-01-05", "end": "2026-08-21"}:
        raise RuntimeError("BLACKBOX boundary drifted")
    return p


def read_source(path: Path) -> pd.DataFrame:
    actual = sha256(path)
    if actual != EXPECTED_SOURCE_SHA:
        raise RuntimeError(f"historical source SHA mismatch: {actual}")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("trading_day", "<=", VAL_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame = frame.loc[frame["symbol"].eq(SYMBOL)].copy()
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty or str(frame["trading_day"].max()) != VAL_END:
        raise RuntimeError("historical source does not end exactly at validation boundary")
    if (frame["trading_day"] >= "2026-01-01").any():
        raise RuntimeError("DEV/VALIDATION runner read blackbox rows")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def resolved_binary(events: pd.DataFrame) -> pd.DataFrame:
    out = events.loc[events["outcome"].isin(["recovery", "failure"])].copy()
    out["y"] = out["outcome"].eq("recovery").astype(int)
    cols = ["day", "severity", "abs_drift", "overlap", "parent_eff", "y"]
    return out[cols].replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


def validate_pair(data: pd.DataFrame, pair_id: str, protocol: dict) -> tuple[dict, dict]:
    dev = data.loc[data["day"] <= DEV_END].copy()
    val = data.loc[(data["day"] >= VAL_START) & (data["day"] <= VAL_END)].copy()
    parent_sc = old.fit_parent_scaler(dev)
    dev_c = old.add_composite(dev, parent_sc)
    val_c = old.add_composite(val, parent_sc)
    baseline = old.fit_probability(dev, ["severity"])
    candidate = old.fit_probability(dev_c, ["severity", "parent_integrity"])
    pooled_base = old.score(baseline, val, ["severity"])
    pooled_cand = old.score(candidate, val_c, ["severity", "parent_integrity"])
    annual = {}
    positive_years = 0
    for year in range(2021, 2026):
        mask = val["day"].str.startswith(str(year))
        b = old.score(baseline, val.loc[mask], ["severity"])
        c = old.score(candidate, val_c.loc[mask], ["severity", "parent_integrity"])
        delta = float(b["brier"] - c["brier"]) if b.get("status") == "scored" and c.get("status") == "scored" else None
        if delta is not None and delta > 0:
            positive_years += 1
        annual[str(year)] = {"baseline": b, "candidate": c, "baseline_minus_candidate_brier": delta}
    min_required = int(protocol["VALIDATION"]["gate_each_pairing"]["minimum_pooled_resolved"][pair_id])
    gates = {
        "minimum_pooled_resolved": int(len(val)) >= min_required,
        "pooled_brier_better": pooled_cand["brier"] < pooled_base["brier"],
        "pooled_logloss_better": pooled_cand["log_loss"] < pooled_base["log_loss"],
        "annual_brier_improvement_positive_ge_4_of_5": positive_years >= 4,
    }
    result = {
        "inventory": {"DEV_resolved": int(len(dev)), "VALIDATION_resolved": int(len(val))},
        "baseline": pooled_base,
        "candidate": pooled_cand,
        "baseline_minus_candidate_brier": float(pooled_base["brier"] - pooled_cand["brier"]),
        "baseline_minus_candidate_logloss": float(pooled_base["log_loss"] - pooled_cand["log_loss"]),
        "annual": annual,
        "gates": gates,
        "passed": bool(all(gates.values())),
    }
    fit_meta = {
        "DEV_parent_feature_scaler": old.parent_scaler_snapshot(parent_sc),
        "DEV_baseline_model": old.model_snapshot(baseline, ["severity"]),
        "DEV_candidate_model": old.model_snapshot(candidate, ["severity", "parent_integrity"]),
    }
    return result, fit_meta


def final_refit(pair_data: dict[str, pd.DataFrame], protocol: dict) -> dict:
    bundle = {
        "schema_id": "factorlab_rmr_R1_reusable_blackbox_parameter_freeze@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "selected_candidate_id": "R1_PARENT_COMPOSITE_1D",
        "data_policy": "docs/governance/reusable_three_role_data_policy_v1.json",
        "protocol": "docs/governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json",
        "historical_source_sha256": EXPECTED_SOURCE_SHA,
        "final_refit_window": {"start": "2015-01-05", "end": VAL_END},
        "blackbox_window": {"start": "2026-01-05", "end": "2026-08-21"},
        "blackbox_used_in_fit": False,
        "DEV_median_rvol20": float(protocol["scale_identity"]["DEV_median_rvol20"]),
        "directional_change_thresholds": protocol["scale_identity"]["thresholds"],
        "pairings": {},
        "blackbox_gate": protocol["BLACKBOX"]["gate_each_pairing"],
        "public_blackbox_output_only": ["PASS", "FAIL", "INSUFFICIENT"],
        "production_authority": False,
    }
    for pair_id, data in pair_data.items():
        pool = data.loc[data["day"] <= VAL_END].copy()
        parent_sc = old.fit_parent_scaler(pool)
        pool_c = old.add_composite(pool, parent_sc)
        baseline = old.fit_probability(pool, ["severity"])
        candidate = old.fit_probability(pool_c, ["severity", "parent_integrity"])
        bundle["pairings"][pair_id] = {
            "n_final_refit_resolved": int(len(pool)),
            "parent_feature_scaler": old.parent_scaler_snapshot(parent_sc),
            "severity_baseline_model": old.model_snapshot(baseline, ["severity"]),
            "selected_candidate_model": old.model_snapshot(candidate, ["severity", "parent_integrity"]),
        }
    check = dict(bundle)
    bundle["parameter_bundle_sha256"] = json_digest(check)
    return bundle


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    ap.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    args = ap.parse_args()

    protocol = validate_contracts()
    frame = read_source(args.source.resolve())
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    thresholds = {k: float(v) for k, v in protocol["scale_identity"]["thresholds"].items()}
    vol_ref = float(protocol["scale_identity"]["DEV_median_rvol20"])
    waves = {name: common.detect_waves(prices, thresholds[name]) for name in ("S1", "S2", "S3")}
    pair_data = {}
    validation = {}
    dev_fit_meta = {}
    for pair_id, lower, parent in PAIRINGS:
        events = common.r1_events(prices, days, waves[lower], waves[parent], vol_ref)
        data = resolved_binary(events)
        pair_data[pair_id] = data
        validation[pair_id], dev_fit_meta[pair_id] = validate_pair(data, pair_id, protocol)

    validation_passed = bool(all(v["passed"] for v in validation.values()))
    receipt = {
        "schema_id": "factorlab_rmr_R1_reusable_DEV_VALIDATION_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "data_policy": "docs/governance/reusable_three_role_data_policy_v1.json",
        "protocol": "docs/governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json",
        "DEV_window": {"start": "2015-01-05", "end": DEV_END},
        "VALIDATION_window": {"start": VAL_START, "end": VAL_END},
        "BLACKBOX_window": {"start": "2026-01-05", "end": "2026-08-21", "opened": False},
        "validation": validation,
        "DEV_fit_metadata": dev_fit_meta,
        "validation_passed": validation_passed,
        "final_refit_performed": validation_passed,
        "blackbox_rows_read": False,
        "production_authority": False,
    }
    dump_json(args.receipt.resolve(), receipt)
    if not validation_passed:
        print("R1_REUSABLE_VALIDATION_FAIL")
        return 2
    bundle = final_refit(pair_data, protocol)
    dump_json(args.freeze.resolve(), bundle)
    print("R1_REUSABLE_VALIDATION_PASS_FINAL_REFIT_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
