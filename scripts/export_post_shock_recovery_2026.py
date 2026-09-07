"""Slice the frozen DataHub parents into an independent 2026 research pack.

This is a row filter plus year partition. It does not resample, interpolate,
deduplicate same-second source rows, or mutate the sealed 2021-2025 packs.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT.parent / "unified_datahub"
SRC_1M = (
    HUB
    / ".runtime/live/exports/factorlab_unified_index_kline_v3_20260824/1m_official.parquet"
)
SRC_1M_MANIFEST = SRC_1M.with_name("manifest.json")
SRC_3S_PARENT = (
    HUB
    / ".runtime/live/lake/market_index_transactions"
    / "dataset_version=market_index_baidu_3s_20000714_20260821_cffex_underlyings_alias_repaired_v4_20260823"
)
SRC_3S = SRC_3S_PARENT / "observations.parquet"
OUT_1M = ROOT / "data/cross_index_risk_gate_2026_v1"
OUT_3S = ROOT / "data/cross_index_risk_gate_2026_3s_v1"
RECEIPT = ROOT / "docs/ops/evidence/post_shock_recovery_2026_export_v1/receipt.json"
SEALED = [
    ROOT / "data/cross_index_risk_gate_v1/manifest.json",
    ROOT / "data/cross_index_risk_gate_3s_v1/manifest.json",
]
SYMBOLS = ("000688.SH", "000852.SH")
START = "2026-01-01"
CAP = "2026-09-07"
PARENT_1M_SHA = "aeacff04b268c166faac333ec7ab9d840abcd347d82cb3bcee0218d058fc7423"
PARENT_3S_SHA = "a2abc93ef0975490aae73c606ca8157a15c44cd182626c7537a9a62494310540"
PARENT_1M_VERSION = (
    "bars_cn_index_1m_raw_canonical_market_index_baidu_3s_"
    "20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824"
)
TZ = (
    "source Z strings encode Shanghai wall clock; use first 19 characters "
    "localised Asia/Shanghai, not UTC conversion"
)


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def columns(con: duckdb.DuckDBPyConnection, path: Path) -> list[str]:
    return [
        row[0]
        for row in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]).fetchall()
    ]


def main() -> None:
    started = time.monotonic()
    if OUT_1M.exists() or OUT_3S.exists() or RECEIPT.exists():
        raise SystemExit("refuse to overwrite an existing 2026 export")

    sealed_before = {str(path.relative_to(ROOT)): sha(path) for path in SEALED}
    source_1m_sha = sha(SRC_1M)
    source_1m_manifest = json.loads(SRC_1M_MANIFEST.read_text())
    if source_1m_sha != PARENT_1M_SHA:
        raise SystemExit("1m parent hash drifted")
    if source_1m_manifest["artifacts"]["1m_official.parquet"]["sha256"] != PARENT_1M_SHA:
        raise SystemExit("1m export manifest hash drifted")
    if sha(SRC_3S) != PARENT_3S_SHA:
        raise SystemExit("3s parent hash drifted")
    parent_3s_manifest = json.loads((SRC_3S_PARENT / "manifest.json").read_text())
    if parent_3s_manifest["dataset_hash"] != PARENT_3S_SHA:
        raise SystemExit("3s parent manifest hash drifted")

    con = duckdb.connect()
    con.execute("SET threads=4")
    con.execute("SET memory_limit='2GB'")
    con.execute(f"CREATE VIEW src_1m AS SELECT * FROM read_parquet('{SRC_1M}')")
    con.execute(f"CREATE VIEW src_3s AS SELECT * FROM read_parquet('{SRC_3S}')")
    files: list[dict] = []

    for symbol in SYMBOLS:
        dest = OUT_1M / "1m" / symbol / "2026.parquet"
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Identifiers are frozen constants, not user input.
        con.execute(
            "COPY ("
            f"SELECT * FROM src_1m WHERE symbol = '{symbol}' "
            f"AND trading_day >= '{START}' AND trading_day <= '{CAP}' "
            "ORDER BY timestamp"
            f") TO '{dest}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        stats = con.execute(
            """
            SELECT count(*),
                   count(DISTINCT trading_day),
                   min(trading_day),
                   max(trading_day),
                   count(*) - count(DISTINCT (symbol, timestamp)),
                   count(*) FILTER (
                       WHERE open IS NULL OR high IS NULL OR low IS NULL
                          OR close IS NULL
                          OR NOT isfinite(open) OR NOT isfinite(high)
                          OR NOT isfinite(low) OR NOT isfinite(close)
                          OR high < low
                   ),
                   count(*) FILTER (WHERE trading_day < ? OR trading_day > ?),
                   count(*) FILTER (WHERE trading_day > ?)
            FROM read_parquet(?)
            """,
            [START, CAP, CAP, str(dest)],
        ).fetchone()
        if stats is None or stats[0] <= 0 or stats[4:8] != (0, 0, 0, 0):
            raise SystemExit(f"1m quality gate failed for {symbol}: {stats}")
        if not (START <= str(stats[2]) <= str(stats[3]) <= CAP):
            raise SystemExit(f"1m date gate failed for {symbol}: {stats}")
        files.append(
            {
                "path": str(dest.relative_to(ROOT)),
                "sha256": sha(dest),
                "bytes": dest.stat().st_size,
                "symbol": symbol,
                "frequency": "1m",
                "year": 2026,
                "rows": int(stats[0]),
                "days": int(stats[1]),
                "first_day": str(stats[2]),
                "last_day": str(stats[3]),
                "duplicates": int(stats[4]),
                "invalid": int(stats[5]),
                "source": str(SRC_1M),
                "source_sha256": PARENT_1M_SHA,
                "dataset_version": PARENT_1M_VERSION,
                "export_id": "factorlab_unified_index_kline_v3_20260824",
                "source_columns_preserved": columns(con, dest),
                "role": "held_out_validation_material",
            }
        )
        print(symbol, "1m", stats[0], stats[1], stats[2], stats[3], flush=True)

    for symbol in SYMBOLS:
        dest = OUT_3S / f"{symbol}_2026.parquet"
        dest.parent.mkdir(parents=True, exist_ok=True)
        con.execute(
            "COPY ("
            f"SELECT * FROM src_3s WHERE symbol = '{symbol}' "
            f"AND trading_day >= '{START}' AND trading_day <= '{CAP}' "
            "ORDER BY observation_datetime, row_index"
            f") TO '{dest}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        stats = con.execute(
            """
            SELECT count(*),
                   count(DISTINCT trading_day),
                   min(trading_day),
                   max(trading_day),
                   count(*) - count(DISTINCT (symbol, observation_datetime, row_index)),
                   count(*) FILTER (
                       WHERE price IS NULL OR amount IS NULL
                          OR price <= 0 OR amount < 0
                          OR NOT isfinite(price) OR NOT isfinite(amount)
                   ),
                   count(*) FILTER (WHERE volume IS NOT NULL),
                   count(*) - count(DISTINCT (symbol, observation_datetime)),
                   count(*) FILTER (WHERE trading_day < ? OR trading_day > ?),
                   count(*) FILTER (WHERE trading_day > ?)
            FROM read_parquet(?)
            """,
            [START, CAP, CAP, str(dest)],
        ).fetchone()
        if (
            stats is None
            or stats[0] <= 0
            or stats[4:7] != (0, 0, 0)
            or stats[8:10] != (0, 0)
        ):
            raise SystemExit(f"3s quality gate failed for {symbol}: {stats}")
        if not (START <= str(stats[2]) <= str(stats[3]) <= CAP):
            raise SystemExit(f"3s date gate failed for {symbol}: {stats}")
        files.append(
            {
                "path": dest.name,
                "repo_path": str(dest.relative_to(ROOT)),
                "sha256": sha(dest),
                "bytes": dest.stat().st_size,
                "symbol": symbol,
                "frequency": "3s",
                "year": 2026,
                "rows": int(stats[0]),
                "days": int(stats[1]),
                "first_day": str(stats[2]),
                "last_day": str(stats[3]),
                "duplicates": int(stats[4]),
                "invalid": int(stats[5]),
                "nonnull_volume": int(stats[6]),
                "same_timestamp_extra_rows": int(stats[7]),
                "source": str(SRC_3S),
                "source_sha256": PARENT_3S_SHA,
                "dataset_version": parent_3s_manifest["dataset_version"],
                "source_columns_preserved": columns(con, dest),
                "role": "held_out_validation_material",
            }
        )
        print(symbol, "3s", stats[0], stats[1], stats[2], stats[3], flush=True)

    last_days = {item["last_day"] for item in files}
    first_days = {item["first_day"] for item in files}
    day_counts = {item["days"] for item in files}
    if last_days != {"2026-08-21"} or first_days != {"2026-01-05"} or day_counts != {154}:
        raise SystemExit(f"unexpected coverage {first_days} {last_days} {day_counts}")

    sealed_after = {str(path.relative_to(ROOT)): sha(path) for path in SEALED}
    if sealed_before != sealed_after:
        raise SystemExit("sealed 2021-2025 manifests changed")

    common = {
        "requested_start": START,
        "requested_cap": CAP,
        "actual_first_day": "2026-01-05",
        "actual_last_day": "2026-08-21",
        "actual_days": 154,
        "timezone_policy": TZ,
        "new_ohlc_created": False,
        "interpolation": False,
        "same_second_rows_deduplicated": False,
        "tdx_reconstructed_days_stitched": False,
        "post_snapshot_rows": 0,
        "sealed_2021_2025_manifests_unchanged": sealed_after,
        "data_role": "held_out_validation_material",
        "fresh_oos": False,
        "production_authority": False,
        "online_serving_granted": False,
    }
    write_json(
        OUT_1M / "manifest.json",
        {
            "schema": "cross_index_market_archive_2026@1.0",
            "pack_id": "cross_index_risk_gate_2026_v1",
            **common,
            "parent_export_id": "factorlab_unified_index_kline_v3_20260824",
            "parent_dataset_version": PARENT_1M_VERSION,
            "parent_file_sha256": PARENT_1M_SHA,
            "datahub_export_manifest_sha256": sha(SRC_1M_MANIFEST),
            "known_repairs": (
                "preserve causal_flat_fill/source_minute_count/"
                "high_frequency_analysis_eligible; filter eligibility for "
                "high-frequency statistics"
            ),
            "files": [item for item in files if item["frequency"] == "1m"],
        },
    )
    write_json(
        OUT_3S / "manifest.json",
        {
            "schema": "factorlab_cross_index_risk_gate_3s_export_2026@1.0",
            "pack_id": "cross_index_risk_gate_2026_3s_v1",
            **common,
            "parent_dataset_version": parent_3s_manifest["dataset_version"],
            "parent_file_sha256": PARENT_3S_SHA,
            "parent_evidence": {
                name: sha(SRC_3S_PARENT / name)
                for name in (
                    "manifest.json",
                    "coverage_report.json",
                    "quality_report.json",
                    "source_receipt.json",
                )
            },
            "files": [item for item in files if item["frequency"] == "3s"],
        },
    )
    write_json(
        RECEIPT,
        {
            "schema": "post_shock_recovery_2026_export_receipt@1.0",
            "task": "CL-STAR-RISK-20260907 / POST-SHOCK-RECOVERY-2026",
            "executor": "local_datahub_slice",
            "consumer_repo": "staryocean0/factorlab-star50-filter-lab",
            "consumer_branch": "research/post-shock-recovery-2026-validation",
            "request": "docs/ops/post_shock_recovery_2026_data_request.md",
            **common,
            "coverage_note": (
                "Authoritative same-semantics parents end on 2026-08-21. "
                "Isolated TDX reconstructed days 2026-08-24/25 were not stitched."
            ),
            "files": [
                {
                    "path": item.get("repo_path", item["path"]),
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                    "symbol": item["symbol"],
                    "frequency": item["frequency"],
                    "rows": item["rows"],
                    "days": item["days"],
                    "first_day": item["first_day"],
                    "last_day": item["last_day"],
                    "dataset_version": item["dataset_version"],
                    "source_sha256": item["source_sha256"],
                }
                for item in files
            ],
            "elapsed_seconds": time.monotonic() - started,
        },
    )
    print("sealed manifests unchanged", sealed_after, flush=True)


if __name__ == "__main__":
    main()
