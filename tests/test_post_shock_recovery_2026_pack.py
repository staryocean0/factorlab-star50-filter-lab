"""Hash and coverage gates for the independent 2026 validation pack."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs/ops/evidence/post_shock_recovery_2026_export_v1/receipt.json"
SEALED = [
    ROOT / "data/cross_index_risk_gate_v1/manifest.json",
    ROOT / "data/cross_index_risk_gate_3s_v1/manifest.json",
]


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def test_receipt_files_match_and_stay_inside_2026_support() -> None:
    receipt = json.loads(RECEIPT.read_text())
    assert receipt["actual_first_day"] == "2026-01-05"
    assert receipt["actual_last_day"] == "2026-08-21"
    assert receipt["post_snapshot_rows"] == 0
    assert receipt["tdx_reconstructed_days_stitched"] is False
    assert len(receipt["files"]) == 4
    for item in receipt["files"]:
        path = ROOT / item["path"]
        assert path.is_file()
        assert sha(path) == item["sha256"]
        table = pq.read_table(path)
        days = table.column("trading_day").to_pylist()
        assert min(days) == item["first_day"] == "2026-01-05"
        assert max(days) == item["last_day"] == "2026-08-21"
        assert table.num_rows == item["rows"]
        assert set(table.column("symbol").to_pylist()) == {item["symbol"]}


def test_sealed_historical_manifests_unchanged() -> None:
    receipt = json.loads(RECEIPT.read_text())
    recorded = receipt["sealed_2021_2025_manifests_unchanged"]
    for path in SEALED:
        assert recorded[str(path.relative_to(ROOT))] == sha(path)
