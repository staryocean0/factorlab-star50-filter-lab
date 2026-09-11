from __future__ import annotations

import json
from pathlib import Path

import run_validation as rv

HERE = Path(__file__).resolve().parent


def test_frozen_contract_identity():
    c = json.loads((HERE / "FROZEN_VALIDATION_CONTRACT.json").read_text())
    assert c["frozen_v19_runner_blob"] == rv.EXPECTED_V19_BLOB
    assert c["frozen_v9_runner_blob"] == rv.EXPECTED_V9_BLOB
    assert c["frozen_v18_runner_blob"] == rv.EXPECTED_V18_BLOB
    assert c["frozen_v17_runner_blob"] == rv.EXPECTED_V17_BLOB
    assert c["frozen_v16_surface_blob"] == rv.EXPECTED_V16_SURFACE_BLOB
    assert c["validation_years"] == [2024, 2025]
    assert c["queried_3s_years"] == [2024, 2025]
    assert c["checkpoint_seconds_before_5m_close"] == 15


def test_exact_v19_machine_semantics():
    v19 = rv.load_v19()
    assert tuple(v19.REF_YEARS) == rv.REF_YEARS
    assert tuple(v19.DEV_YEARS) == rv.VAL_YEARS
    assert v19.machine_e15_state("NORMAL", "UNSAFE") == "UNSAFE"
    assert v19.machine_e15_state("RECOVERING", "UNSAFE") == "UNSAFE"
    assert v19.machine_e15_state("UNSAFE", "RECOVERING") == "RECOVERING"
    assert v19.machine_e15_state("UNSAFE", "NORMAL") == "UNSAFE"
    assert v19.machine_e15_state("RECOVERING", "NORMAL") == "RECOVERING"
    assert v19.machine_e15_state("NORMAL", "NORMAL") == "NORMAL"


def test_reference_exit_is_close_confirmed():
    v19 = rv.load_v19()
    assert v19.reference_e15_state("UNSAFE", "NORMAL") == "UNSAFE"
    assert v19.reference_e15_state("RECOVERING", "NORMAL") == "RECOVERING"
    assert v19.reference_e15_state("NORMAL", "UNSAFE") == "UNSAFE"
    assert v19.reference_e15_state("NORMAL", "NORMAL") == "NORMAL"
