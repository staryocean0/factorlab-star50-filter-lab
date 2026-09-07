import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("risk_export", ROOT / "scripts/export_cross_index_risk_gate_20260907.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
contract = json.loads(module.CONTRACT.read_text())


def test_exact_scope():
    module.assert_scope("000688.SH", "2020-07-23", "2025-12-31", contract)
    module.assert_scope("000852.SH", "2014-10-17", "2025-12-31", contract)


@pytest.mark.parametrize("symbol,start,end", [("000688.SH","2020-07-22","2025-12-31"),("000852.SH","2014-10-17","2026-01-01"),("588000.SSE","2024-01-01","2025-12-31"),("000852.SH","2025-01-02","2025-01-01")])
def test_negative_scope(symbol, start, end):
    with pytest.raises(ValueError):
        module.assert_scope(symbol, start, end, contract)
