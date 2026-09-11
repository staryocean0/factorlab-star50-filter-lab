from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_runner():
    p = HERE / "run_validation.py"
    spec = importlib.util.spec_from_file_location("v18_validation_runner_test", p)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_frozen_identity():
    m = load_runner()
    assert m.VALID_YEARS == (2024, 2025)
    assert m.REF_YEARS == (2020, 2021, 2022, 2023, 2024, 2025)
    assert m.LEADS == (60, 30, 15, 6, 3)
    assert m.PRIMARY_LEAD == 15
    assert m.SOURCE_STATES == ("NORMAL", "RECOVERING")
    assert m.FROZEN_V18_BLOB == "62c207badff1c3e37cbb1a8e17ef89feeea611d8"
    assert m.FROZEN_V9_BLOB == "ae2a7e095df58692ef9df0dfee5856cac727ca44"


def test_contract_forbids_adaptation():
    c = json.loads((HERE / "FROZEN_VALIDATION_CONTRACT.json").read_text())
    assert c["validation_years"] == [2024, 2025]
    assert c["queried_3s_years"] == [2024, 2025]
    assert c["primary_lead_seconds"] == 15
    assert c["signal"] == "partial_state == UNSAFE"
    assert c["threshold_search_permitted"] is False
    assert c["feature_search_permitted"] is False
    assert c["probability_fit_permitted"] is False
    assert c["lead_time_selection_permitted"] is False
    assert c["subgroup_selection_permitted"] is False
    assert c["queried_2026_3s"] is False
    assert c["blackbox_query_permitted"] is False
    assert c["production_authority"] is False


def test_protocol_primary_is_e15_only():
    txt = (HERE / "PROTOCOL.md").read_text()
    assert "only `E-15s` is decisive" in txt
    assert "no 2026 3s" in txt
    assert "Failure is final" in txt
