"""Offline package acceptance; no DataHub connection or strategy execution."""

import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs/handoff/cloud_risk_gate_20260907"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    package = json.loads((HANDOFF / "package_manifest.json").read_text())
    assert (
        package["private_repository_required"] and not package["production_authority"]
    )
    for item in package["files"]:
        path = (ROOT / item["path"]).resolve()
        assert path.is_relative_to(ROOT) and path.is_file(), item["path"]
        assert sha(path) == item["sha256"], item["path"]
    total_rows = {}
    for directory, seconds in [
        ("cross_index_risk_gate_v1", False),
        ("cross_index_risk_gate_3s_v1", True),
    ]:
        folder = ROOT / "data" / directory
        manifest = json.loads((folder / "manifest.json").read_text())
        if seconds:
            acceptance = json.loads((folder / "primary_acceptance.json").read_text())
            assert acceptance["manifest_sha256"] == sha(folder / "manifest.json")
            assert (
                not acceptance["online_serving_granted"]
                and not acceptance["production_granted"]
            )
            assert json.loads((folder / "independent_export_audit.json").read_text())[
                "row_multiset_fingerprint_matches_all_columns"
            ]
        for item in manifest["files"]:
            path = folder / item["path"] if seconds else ROOT / item["path"]
            assert sha(path) == item["sha256"]
            f = pq.ParquetFile(path)
            assert f.metadata.num_rows == item["rows"]
            frame = f.read(columns=["symbol", "trading_day"]).to_pandas()
            assert set(frame.symbol) == {item["symbol"]} <= {"000688.SH", "000852.SH"}
            assert frame.trading_day.max() <= "2025-12-31"
            assert (
                frame.trading_day.min() == item["first_day"]
                and frame.trading_day.max() == item["last_day"]
            )
            key = f"{item['symbol']}:{'3s' if seconds else item['frequency']}"
            total_rows[key] = total_rows.get(key, 0) + len(frame)
    topic = (
        ROOT
        / "research_materials/10_regime_dynamics_investment_frameworks/causal_cross_scale_risk_gate_20260907"
    )
    sources = json.loads((topic / "sources.json").read_text())
    assert len(sources) == 14
    for item in sources:
        path = topic / item.get("existing", item["file"])
        assert path.read_bytes().startswith(b"%PDF-"), item["id"]
    assert (
        (topic / "page_1954_continuous_inspection_schemes.pdf")
        .read_bytes()
        .startswith(b"%PDF-")
    )
    assert not json.loads((topic / "user_delivery_receipt.json").read_text())[
        "missing_fulltexts"
    ]
    print(
        json.dumps(
            {
                "status": "passed",
                "package_files": len(package["files"]),
                "active_data_rows": total_rows,
                "identified_fulltext_works": 15,
                "fresh_oos": False,
                "production_authority": False,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
