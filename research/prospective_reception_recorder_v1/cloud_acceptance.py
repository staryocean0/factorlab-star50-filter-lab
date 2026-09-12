#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

EXPECTED_PACKAGE = "STAR50_DATAHUB_RAW_CALLBACK_SAMPLE_20260912"
EXPECTED_DAY = "2025-06-11"
EXPECTED_SOURCE = "baidu_netdisk_market_index_transaction_3s"
EXPECTED = {
    "000688.SH": (4746, "raw/000688.SH_2025-06-11.jsonl", "000688.csv"),
    "000852.SH": (4746, "raw/000852.SH_2025-06-11.jsonl", "000852.csv"),
}
FORBIDDEN_RECEPTION_FIELDS = {
    "received_at", "receive_time", "ingest_time", "local_received_at",
    "arrival_time", "recv_timestamp", "collector_timestamp",
    "receive_wallclock_utc_ns", "receive_monotonic_ns",
}
REALTIME_REL = "parser_source/src/datahub/adapters/tdx_remote/realtime.py"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def hms_seconds(text: str) -> int:
    dt = datetime.strptime(text, "%H:%M:%S")
    return dt.hour * 3600 + dt.minute * 60 + dt.second


def audit_manifest(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    require(manifest.get("package") == EXPECTED_PACKAGE, "unexpected package")
    require(manifest.get("level") == "NORMALIZED_SOURCE_ROWS", "unexpected handoff level")
    require(manifest.get("callback_raw") == "CALLBACK_RAW_NOT_PERSISTED", "callback verdict drift")
    require(manifest.get("vendor") == EXPECTED_SOURCE, "vendor/source drift")
    require(manifest.get("trading_day") == EXPECTED_DAY, "trading day drift")
    checked = []
    for item in manifest.get("files", []):
        rel = item["relative_path"]
        path = root / rel
        require(path.is_file(), f"manifest file missing: {rel}")
        require(path.stat().st_size == int(item["bytes"]), f"size mismatch: {rel}")
        require(sha256_file(path) == item["sha256"], f"sha256 mismatch: {rel}")
        checked.append(rel)
    return {"files_checked": len(checked), "all_manifest_hashes_match": True}


def audit_symbol(root: Path, symbol: str, rows_expected: int, rel: str, source_file: str):
    path = root / rel
    times: list[str] = []
    phases: Counter[str] = Counter()
    gaps: Counter[int] = Counter()
    archives: set[str] = set()
    versions: set[str] = set()
    prices: list[float] = []
    previous: int | None = None
    rows = 0
    with path.open("r", encoding="utf-8") as fh:
        for rows, line in enumerate(fh, start=1):
            row = json.loads(line)
            idx = rows - 1
            require(row.get("symbol") == symbol, f"{symbol}:{idx} symbol")
            require(row.get("trading_day") == EXPECTED_DAY, f"{symbol}:{idx} day")
            require(row.get("source_kind") == EXPECTED_SOURCE, f"{symbol}:{idx} source")
            require(row.get("source_file") == source_file, f"{symbol}:{idx} source_file")
            require(row.get("row_index") == idx, f"{symbol}:{idx} row_index")
            require(not (FORBIDDEN_RECEPTION_FIELDS & set(row)), f"{symbol}:{idx} false reception field")
            obs_time = str(row.get("observation_time"))
            obs_dt = str(row.get("observation_datetime"))
            require(len(obs_time) == 8 and len(obs_dt) >= 19, f"{symbol}:{idx} observation label")
            require(obs_dt[11:19] == obs_time, f"{symbol}:{idx} observation label mismatch")
            second = hms_seconds(obs_time)
            if previous is not None:
                require(second > previous, f"{symbol}:{idx} time not strictly increasing")
                gaps[second - previous] += 1
            previous = second
            times.append(obs_time)
            price = float(row["price"])
            require(math.isfinite(price) and price > 0, f"{symbol}:{idx} invalid price")
            prices.append(price)
            phases[str(row.get("session_phase"))] += 1
            archives.add(str(row.get("source_archive_sha256")))
            versions.add(str(row.get(".dataset_version")))
    require(rows == rows_expected, f"{symbol}: row count {rows} != {rows_expected}")
    require(len(set(times)) == rows, f"{symbol}: duplicate observation_time")
    require(len(archives) == 1, f"{symbol}: archive identity drift")
    require(len(versions) == 1, f"{symbol}: dataset version drift")
    return {
        "rows": rows,
        "first_observation_time": times[0],
        "last_observation_time": times[-1],
        "price_min": min(prices),
        "price_max": max(prices),
        "session_phase_counts": dict(sorted(phases.items())),
        "gap_seconds_counts": {str(k): v for k, v in sorted(gaps.items())},
        "source_archive_sha256": next(iter(archives)),
        "dataset_version": next(iter(versions)),
        "true_reception_fields_present": False,
    }, times


def audit_realtime_source(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TdxRemoteRealtimeAdapter"), None)
    require(cls is not None, "TdxRemoteRealtimeAdapter missing")
    init_fn = next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
    poll_fn = next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "poll_quotes"), None)
    require(init_fn is not None and poll_fn is not None, "DataHub integration methods missing")
    args = {a.arg for a in init_fn.args.args + init_fn.args.kwonlyargs}
    require({"hq_api", "quotes_parser"} <= args, "DataHub injection seam missing")
    calls = {"get_security_quotes": [], "parse_quotes": []}
    for node in ast.walk(poll_fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in calls:
            calls[node.func.attr].append(node.lineno)
    require(calls["get_security_quotes"] and calls["parse_quotes"], "required calls missing")
    hq_line = min(calls["get_security_quotes"])
    parser_line = min(calls["parse_quotes"])
    require(hq_line < parser_line, "HQ return/parser ordering drift")
    return {
        "sha256": sha256_file(path),
        "hq_api_injectable": True,
        "quotes_parser_injectable": True,
        "get_security_quotes_line": hq_line,
        "parse_quotes_line": parser_line,
        "hq_call_precedes_parser_call": True,
        "local_now_metadata_present": "datetime.now(timezone.utc)" in text,
        "capture_boundary": "tdx_python_sdk_return_before_datahub_parser",
        "wire_level_capture": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handoff-root", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    root = args.handoff_root.resolve()
    manifest_path = root / "MANIFEST.json"
    require(manifest_path.is_file(), "MANIFEST.json missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result: dict[str, Any] = {
        "schema": "star50_datahub_cloud_acceptance_v1",
        "decision": "PENDING",
        "historical_market_data_accepted": True,
        "historical_received_at_recovered": False,
        "measured_feed_latency_supported": False,
        "blackbox_queried": False,
        "production_authority": False,
    }
    result["manifest"] = audit_manifest(root, manifest)
    summaries, grids = {}, {}
    for symbol, (expected_rows, rel, source_file) in EXPECTED.items():
        summaries[symbol], grids[symbol] = audit_symbol(root, symbol, expected_rows, rel, source_file)
    result["symbols"] = summaries
    result["total_normalized_rows_verified"] = sum(x["rows"] for x in summaries.values())
    exact_grid = grids["000688.SH"] == grids["000852.SH"]
    require(exact_grid, "two-index observation grids differ")
    result["cross_symbol_observation_grid_exact_match"] = exact_grid
    result["cross_symbol_observation_grid_points"] = len(grids["000688.SH"])
    realtime = root / REALTIME_REL
    require(realtime.is_file(), "real DataHub realtime.py missing")
    result["datahub_source_contract"] = audit_realtime_source(realtime)
    result["decision"] = "DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
