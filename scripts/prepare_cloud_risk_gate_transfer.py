"""Local controller: export bounded existing bars and copy declared literature.

This is a transport operation, not a bar factory or a research experiment.
"""

from pathlib import Path
import hashlib
import json
import shutil

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT.parent / "baylum terminal 0.4.1/factor_lab"
HUB = ROOT.parent / "unified_datahub"
SOURCE = HUB / ".runtime/live/exports/factorlab_unified_index_kline_v3_20260824"
OUT = ROOT / "data/cross_index_risk_gate_v1"
DOC = ROOT / "docs/handoff/cloud_risk_gate_20260907"
TOPIC = "10_regime_dynamics_investment_frameworks/causal_cross_scale_risk_gate_20260907"
METHODS = "10_regime_dynamics_investment_frameworks/volatility_three_state_router_methods_20260828"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def main():
    assert not OUT.exists(), "immutable transfer output already exists"
    usage = ROOT / "docs/governance/cloud_risk_gate_data_usage_20260907.json"
    assert usage.is_file()
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    records = []
    for name, frequency in [
        ("1m_official.parquet", "1m"),
        ("5m_offset_0.parquet", "5m"),
    ]:
        source = SOURCE / name
        assert sha(source) == manifest["artifacts"][name]["sha256"]
        for symbol, start in [("000688.SH", "2020-07-23"), ("000852.SH", "2015-01-05")]:
            frame = pq.read_table(
                source,
                filters=[
                    ("symbol", "=", symbol),
                    ("trading_day", ">=", start),
                    ("trading_day", "<=", "2025-12-31"),
                ],
            ).to_pandas()
            assert not frame.duplicated(["symbol", "timestamp"]).any()
            for year, part in frame.groupby(frame.trading_day.str[:4], sort=True):
                path = OUT / frequency / symbol / f"{year}.parquet"
                path.parent.mkdir(parents=True, exist_ok=True)
                part.to_parquet(path, index=False, compression="zstd")
                records.append(
                    {
                        "path": str(path.relative_to(ROOT)),
                        "sha256": sha(path),
                        "bytes": path.stat().st_size,
                        "symbol": symbol,
                        "frequency": frequency,
                        "year": int(year),
                        "rows": len(part),
                        "first_day": str(part.trading_day.min()),
                        "last_day": str(part.trading_day.max()),
                        "days": int(part.trading_day.nunique()),
                        "source": str(source),
                        "source_sha256": manifest["artifacts"][name]["sha256"],
                        "source_columns_preserved": list(part.columns),
                        "role": "consumed_development_material",
                    }
                )
            print(
                symbol,
                frequency,
                len(frame),
                frame.trading_day.min(),
                frame.trading_day.max(),
                flush=True,
            )
    save(
        OUT / "manifest.json",
        {
            "schema": "cross_index_market_archive@1.0",
            "data_usage_sha256": sha(usage),
            "datahub_export_manifest_sha256": sha(SOURCE / "manifest.json"),
            "new_ohlc_created": False,
            "timezone_policy": "source Z strings encode Shanghai wall clock; use first19 characters localised Asia/Shanghai, not UTC conversion",
            "known_repairs": "preserve causal_flat_fill/source_minute_count/high_frequency_analysis_eligible; filter eligibility for high-frequency statistics",
            "files": records,
            "fresh_oos": False,
            "production_authority": False,
        },
    )
    copied = []
    for folder in [TOPIC, METHODS]:
        for source in sorted((LOCAL / "research_materials" / folder).iterdir()):
            if not source.is_file() or source.suffix not in {
                ".pdf",
                ".md",
                ".json",
                ".py",
                ".csv",
            }:
                continue
            dest = ROOT / "research_materials" / folder / source.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            assert not dest.exists()
            shutil.copy2(source, dest)
            assert sha(source) == sha(dest)
            copied.append(
                {
                    "local_source": str(source),
                    "path": str(dest.relative_to(ROOT)),
                    "sha256": sha(dest),
                    "bytes": dest.stat().st_size,
                }
            )
    save(
        DOC / "literature_transfer_receipt.json",
        {
            "files": copied,
            "main_papers": 14,
            "supplementary_page_paper": 1,
            "additional_files": "existing methodology package dependencies; do not count these as new references from the owner markdown",
            "all_identified_fulltexts_available": True,
            "private_internal_research_only": True,
        },
    )
    print("copied literature", len(copied), "files", flush=True)


if __name__ == "__main__":
    main()
