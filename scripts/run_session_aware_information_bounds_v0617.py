#!/usr/bin/env python3
"""Fixed CLI for v0.6.17 results-blind DataHub replay.

The local executor may supply data paths, but may not alter support topology,
metric, bound policy, or source-identity requirements without a new protocol.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from star50_filter.session_aware_information_bounds import (
    AUTHORITATIVE_SOURCE_ROWS,
    PROTOCOL_VERSION,
    adjudicate_source_identity,
    evaluate_information_set_bounds,
    file_sha256,
    summarize_bounds,
)


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
        raise ValueError(f"{column} contains non-boolean values: {bad[:5]}")
    frame[column] = lowered.map(mapping).astype(bool)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authoritative-source", type=Path, required=True,
                        help="Exact DataHub authoritative 1m source surface; identity gate only.")
    parser.add_argument("--legs", type=Path, required=True,
                        help="Frozen published-leg universe with expected_step_count and overlays.")
    parser.add_argument("--support", type=Path, required=True,
                        help="DataHub-exported actual support membership/topology. Never inferred from adjacent closes.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-source-rows", type=int, default=AUTHORITATIVE_SOURCE_ROWS)
    parser.add_argument("--expected-source-sha256", default=None)
    parser.add_argument("--diagnostic-nonauthoritative", action="store_true",
                        help="Permit identity mismatch only for diagnostics; output remains non-authoritative.")
    args = parser.parse_args()

    source = read_table(args.authoritative_source)
    source_digest = file_sha256(args.authoritative_source)
    identity = adjudicate_source_identity(
        len(source), expected_rows=args.expected_source_rows,
        actual_sha256=source_digest, expected_sha256=args.expected_source_sha256,
        authoritative=not args.diagnostic_nonauthoritative,
    )

    legs = read_table(args.legs)
    support = read_table(args.support)
    normalize_bool_column(support, "observed")
    for col in ("published", "strict_pair", "qualified"):
        normalize_bool_column(legs, col)

    bounds = evaluate_information_set_bounds(legs, support, identity=identity)
    summary = summarize_bounds(bounds)
    summary["source_identity"] = {
        "rows": identity.rows,
        "expected_rows": identity.expected_rows,
        "status": identity.status,
        "sha256": identity.sha256,
        "expected_sha256": identity.expected_sha256,
    }
    summary["authoritative_replay"] = bool(
        identity.status == "accepted" and not args.diagnostic_nonauthoritative
    )

    args.out.mkdir(parents=True, exist_ok=True)
    bounds_path = args.out / "leg_information_bounds_v0617.csv"
    summary_path = args.out / "summary_v0617.json"
    receipt_path = args.out / "replay_receipt_v0617.json"
    bounds.to_csv(bounds_path, index=False)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt = {
        "protocol_version": PROTOCOL_VERSION,
        "status": "authoritative_replay_complete" if summary["authoritative_replay"] else "diagnostic_only",
        "inputs": {
            "authoritative_source": str(args.authoritative_source),
            "authoritative_source_sha256": source_digest,
            "legs": str(args.legs),
            "legs_sha256": file_sha256(args.legs),
            "support": str(args.support),
            "support_sha256": file_sha256(args.support),
        },
        "outputs": {
            "bounds": str(bounds_path),
            "bounds_sha256": file_sha256(bounds_path),
            "summary": str(summary_path),
            "summary_sha256": file_sha256(summary_path),
        },
        "results_blind": True,
        "trading_or_oos_evaluated": False,
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary, "receipt": str(receipt_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
