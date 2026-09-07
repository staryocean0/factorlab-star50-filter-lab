#!/usr/bin/env python3
"""Fixed CLI for v0.6.17 results-blind DataHub replay.

The local executor may supply data paths and already-frozen identity hashes, but
may not alter support topology, metric, bound policy, or source authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from star50_filter.session_aware_information_bounds import (
    AUTHORITATIVE_SOURCE_ROWS,
    PROTOCOL_VERSION,
    IntakeError,
    adjudicate_source_identity,
    evaluate_information_set_bounds,
    file_sha256,
    summarize_bounds,
)

OHLC = ("open", "high", "low", "close")


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path)
    raise ValueError(f"unsupported table format: {path}")


def normalize_bool_column(frame: pd.DataFrame, column: str) -> None:
    if column not in frame.columns:
        return
    s = frame[column]
    if pd.api.types.is_bool_dtype(s):
        return
    mapping = {
        "true": True, "1": True, "yes": True, "y": True,
        "false": False, "0": False, "no": False, "n": False,
    }
    lowered = s.astype(str).str.strip().str.lower()
    bad = sorted(set(lowered).difference(mapping))
    if bad:
        raise IntakeError(f"{column} contains non-boolean values: {bad[:5]}")
    frame[column] = lowered.map(mapping).astype(bool)


def validate_support_against_source(
    source: pd.DataFrame,
    support: pd.DataFrame,
    *,
    source_key: str,
    tolerance: float = 1e-10,
) -> dict:
    """Prove every observed support row is copied from the accepted source.

    Unobserved placeholder rows are allowed to represent DataHub-dropped source
    support, but observed prices may not be invented or drawn from another
    surface.  Timestamp is the default key; callers must choose a stable row key
    when their source legitimately contains duplicate timestamps.
    """
    required_source = {source_key, *OHLC}
    required_support = {source_key, "observed", *OHLC}
    missing_source = sorted(required_source.difference(source.columns))
    missing_support = sorted(required_support.difference(support.columns))
    if missing_source:
        raise IntakeError(f"authoritative source missing columns: {missing_source}")
    if missing_support:
        raise IntakeError(f"support missing source-binding columns: {missing_support}")
    if source[source_key].isna().any():
        raise IntakeError(f"authoritative source has null {source_key}")
    if source[source_key].duplicated().any():
        raise IntakeError(
            f"authoritative source key {source_key!r} is not unique; use a stable row key"
        )

    observed = support.loc[support.observed.astype(bool), [source_key, *OHLC]].copy()
    if observed[source_key].isna().any():
        raise IntakeError(f"observed support has null {source_key}")
    left = observed.copy()
    right = source[[source_key, *OHLC]].copy()
    left[source_key] = left[source_key].astype(str)
    right[source_key] = right[source_key].astype(str)
    merged = left.merge(right, on=source_key, how="left", suffixes=("_support", "_source"), indicator=True)
    absent = int((merged._merge != "both").sum())
    if absent:
        raise IntakeError(f"{absent} observed support rows are absent from authoritative source")

    max_error = 0.0
    for col in OHLC:
        a = merged[f"{col}_support"].to_numpy(float)
        b = merged[f"{col}_source"].to_numpy(float)
        if not np.isfinite(a).all() or not np.isfinite(b).all():
            raise IntakeError(f"non-finite {col} in source/support binding")
        scale = np.maximum(1.0, np.abs(b))
        err = float(np.max(np.abs(a - b) / scale)) if len(a) else 0.0
        max_error = max(max_error, err)
    if max_error > tolerance:
        raise IntakeError(f"support/source OHLC mismatch: max relative error {max_error:g}")
    return {
        "source_key": source_key,
        "observed_support_rows": int(len(observed)),
        "missing_from_source": 0,
        "max_relative_ohlc_error": max_error,
        "status": "match",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authoritative-source", type=Path, required=True,
                        help="Exact DataHub authoritative 1m source surface.")
    parser.add_argument("--legs", type=Path, required=True,
                        help="Frozen published-leg universe with expected_step_count and overlays.")
    parser.add_argument("--support", type=Path, required=True,
                        help="DataHub-exported actual support membership/topology. Never inferred from adjacent closes.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-key", default="timestamp")
    parser.add_argument("--expected-source-sha256", default=None,
                        help="Required for authoritative replay; must come from the frozen DataHub identity receipt.")
    parser.add_argument("--expected-legs-sha256", default=None,
                        help="Required for authoritative replay; binds the frozen v0.6.15 leg universe/overlays.")
    parser.add_argument("--diagnostic-nonauthoritative", action="store_true",
                        help="Permit identity/hash mismatch only for diagnostics; output remains non-authoritative.")
    args = parser.parse_args()

    authoritative = not args.diagnostic_nonauthoritative
    if authoritative and not args.expected_source_sha256:
        raise IntakeError("authoritative replay requires --expected-source-sha256")
    if authoritative and not args.expected_legs_sha256:
        raise IntakeError("authoritative replay requires --expected-legs-sha256")

    source = read_table(args.authoritative_source)
    source_digest = file_sha256(args.authoritative_source)
    identity = adjudicate_source_identity(
        len(source), expected_rows=AUTHORITATIVE_SOURCE_ROWS,
        actual_sha256=source_digest, expected_sha256=args.expected_source_sha256,
        authoritative=authoritative,
    )

    legs_digest = file_sha256(args.legs)
    legs_hash_status = "accepted"
    if args.expected_legs_sha256 and legs_digest != args.expected_legs_sha256:
        legs_hash_status = "rejected_sha256_mismatch"
        if authoritative:
            raise IntakeError(
                f"frozen legs identity failed: actual={legs_digest} expected={args.expected_legs_sha256}"
            )

    legs = read_table(args.legs)
    support = read_table(args.support)
    normalize_bool_column(support, "observed")
    for col in ("published", "strict_pair", "qualified"):
        normalize_bool_column(legs, col)

    source_binding = validate_support_against_source(
        source, support, source_key=args.source_key
    )
    bounds = evaluate_information_set_bounds(legs, support, identity=identity)
    summary = summarize_bounds(bounds)
    summary["source_identity"] = {
        "rows": identity.rows,
        "expected_rows": identity.expected_rows,
        "status": identity.status,
        "sha256": identity.sha256,
        "expected_sha256": identity.expected_sha256,
    }
    summary["legs_identity"] = {
        "status": legs_hash_status,
        "sha256": legs_digest,
        "expected_sha256": args.expected_legs_sha256,
        "rows": int(len(legs)),
    }
    summary["source_binding"] = source_binding
    summary["authoritative_replay"] = bool(
        authoritative
        and identity.status == "accepted"
        and legs_hash_status == "accepted"
        and source_binding["status"] == "match"
    )

    args.out.mkdir(parents=True, exist_ok=True)
    bounds_path = args.out / "leg_information_bounds_v0617.csv"
    summary_path = args.out / "summary_v0617.json"
    receipt_path = args.out / "replay_receipt_v0617.json"
    bounds.to_csv(bounds_path, index=False)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt = {
        "protocol_version": PROTOCOL_VERSION,
        "status": "authoritative_replay_complete" if summary["authoritative_replay"] else "diagnostic_only",
        "inputs": {
            "authoritative_source": str(args.authoritative_source),
            "authoritative_source_sha256": source_digest,
            "authoritative_source_rows": int(len(source)),
            "source_key": args.source_key,
            "legs": str(args.legs),
            "legs_sha256": legs_digest,
            "support": str(args.support),
            "support_sha256": file_sha256(args.support),
        },
        "outputs": {
            "bounds": str(bounds_path),
            "bounds_sha256": file_sha256(bounds_path),
            "summary": str(summary_path),
            "summary_sha256": file_sha256(summary_path),
        },
        "gates": {
            "source_identity": identity.status,
            "legs_identity": legs_hash_status,
            "support_source_binding": source_binding["status"],
        },
        "results_blind": True,
        "trading_or_oos_evaluated": False,
    }
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"summary": summary, "receipt": str(receipt_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
