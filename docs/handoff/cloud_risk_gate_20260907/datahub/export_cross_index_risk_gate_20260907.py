"""Immutable owner-authorized offline subset of the existing index 3s product."""
import hashlib
import json
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/reliability/consumer_contracts/factorlab_cross_index_risk_gate_offline_export_20260907.v1.json"
OUT = ROOT / ".runtime/live/exports/factorlab_cross_index_risk_gate_3s_20260907"


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def assert_scope(symbol, start, end, contract):
    if symbol not in contract["symbols"] or start < contract["start_by_symbol"].get(symbol, "9999") or end > contract["end"] or start > end:
        raise ValueError("scope outside owner-authorized offline export")


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def main():
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    parent = ROOT / ".runtime/live/lake/market_index_transactions" / ("dataset_version=" + contract["active_dataset_version"])
    source = parent / "observations.parquet"
    manifest = json.loads((parent / "manifest.json").read_text())
    coverage = json.loads((parent / "coverage_report.json").read_text())
    receipt = json.loads((parent / "source_receipt.json").read_text())
    old = ROOT / "config/reliability/consumer_contracts/fixed_version_market_index_transactions.v1.json"
    old_hash = sha(old)
    assert manifest["dataset_version"] == contract["active_dataset_version"]
    assert sha(source) == contract["source_sha256"] == manifest["dataset_hash"] == receipt["target_dataset_hash"]
    assert coverage["duplicate_count"] == coverage["invalid_row_count"] == 0
    assert not OUT.exists(), "preserve immutable prior export"
    OUT.mkdir(parents=True)
    con = duckdb.connect()
    con.execute("SET threads=4")
    con.execute("SET memory_limit='2GB'")
    con.read_parquet(str(source)).create_view("source")
    records = []
    for symbol in contract["symbols"]:
        for year in range(int(contract["start_by_symbol"][symbol][:4]), 2026):
            start = max(contract["start_by_symbol"][symbol], f"{year}-01-01")
            end = f"{year}-12-31"
            assert_scope(symbol, start, end, contract)
            path = OUT / f"{symbol}_{year}.parquet"
            # All identifiers/dates are fixed by the versioned owner contract.
            query = f"SELECT * FROM source WHERE symbol='{symbol}' AND trading_day BETWEEN '{start}' AND '{end}' ORDER BY observation_datetime, row_index"
            con.execute(f"COPY ({query}) TO '{path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            stats = con.execute("SELECT count(*), count(DISTINCT trading_day), min(trading_day), max(trading_day), count(*)-count(DISTINCT (symbol,observation_datetime,row_index)), count(*) FILTER(WHERE price<=0 OR NOT isfinite(price) OR amount<0 OR NOT isfinite(amount) OR price IS NULL OR amount IS NULL), count(*) FILTER(WHERE volume IS NOT NULL), count(*)-count(DISTINCT (symbol,observation_datetime)) FROM read_parquet(?)", [str(path)]).fetchone()
            assert stats[0] > 0 and stats[4:7] == (0, 0, 0), stats
            record = dict(path=path.name, symbol=symbol, year=year, rows=stats[0], days=stats[1], first_day=stats[2], last_day=stats[3], duplicates=stats[4], invalid=stats[5], nonnull_volume=stats[6], same_timestamp_extra_rows=stats[7], sha256=sha(path), bytes=path.stat().st_size)
            records.append(record)
            print(symbol, year, stats[0], stats[1], flush=True)
    gaps = [x for x in coverage["missing_expected_symbol_days"] if x["symbol"] in contract["symbols"] and x["trading_day"] <= contract["end"]]
    assert not gaps
    assert sha(old) == old_hash
    out_manifest = {"schema":"factorlab_cross_index_risk_gate_3s_export@1.0", "contract":contract,
                    "contract_sha256":sha(CONTRACT), "source_file_sha256":sha(source),
                    "parent_evidence":{name:sha(parent/name) for name in ["manifest.json","coverage_report.json","quality_report.json","source_receipt.json"]},
                    "old_consumer_contract_unchanged_sha256":old_hash, "files":records,
                    "original_columns_and_values_preserved":True, "new_2026_rows_exported":0, "interpolation":False,
                    "elapsed_seconds":time.monotonic()-started, "online_serving_granted":False, "production_granted":False}
    write(OUT/"manifest.json", out_manifest)
    write(OUT/"coverage_report.json", {"files":records,"rows":sum(r['rows'] for r in records),"gap_basis":"source archive symbol-days, not every 3-second wall-clock slot"})
    write(OUT/"gap_ledger.json", {"source_member_missing":gaps,"intraday_missing_observations":"preserved, never filled","not_requested":"2026, unrelated indices, ETF/options"})
    write(OUT/"quality_report.json", {"numeric_and_key_checks_passed":True,"units":"price=index points, amount=interval CNY turnover, volume=null", "timestamp":"source Z suffix represents Shanghai wall-clock labels; not true UTC conversion", "data_ready":True,"evidence_ready":True,"artifact_ready":True,"production_granted":False})
    write(OUT/"primary_acceptance.json", {"status":"passed_owner_authorized_offline_export_only","consumer_contract":contract["consumer_contract_id"],"manifest_sha256":sha(OUT/'manifest.json'),"fresh_oos":False,"online_serving_granted":False,"production_granted":False})


if __name__ == "__main__":
    main()
