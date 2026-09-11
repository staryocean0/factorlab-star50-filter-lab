from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_validation.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v17_validation", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_validation_boundary_is_fixed():
    rv = load_runner()
    assert rv.SYMBOLS == ("000688.SH", "000852.SH")
    assert rv.REF_YEARS == (2020, 2021, 2022, 2023, 2024, 2025)
    assert rv.VAL_YEARS == (2024, 2025)
    assert rv.HORIZONS == (15, 30, 60)
    assert rv.PRIMARY_LEAD_SECONDS == 15


def test_frozen_v17_identity_is_fixed():
    rv = load_runner()
    frozen = rv.frozen_transfer_authority()
    assert rv.EXPECTED_FROZEN_TRANSFER_BLOB == "5aca30ff398f73173a5424aa14b535bd461df5b4"
    assert rv.EXPECTED_V17_RUNNER_BLOB == "397d80037806ba11cadf7f77717d36d55fbafc91"
    assert frozen["source_execution_commit"] == "5ae8d6adab6c4afb617ed14ae44327d722e3db49"
    assert frozen["source_run_id"] == 34603682244
    assert frozen["checkpoint_seconds_before_5m_close"] == 15
    assert frozen["horizons_minutes"] == [15, 30, 60]
    assert frozen["validation_authorized"] is True
    assert frozen["probability_fit_performed"] is False
    assert frozen["blackbox_queried"] is False


def test_frozen_component_blobs_are_fixed():
    rv = load_runner()
    assert rv.EXPECTED_V9_BLOB == "ae2a7e095df58692ef9df0dfee5856cac727ca44"
    assert rv.EXPECTED_V11_BLOB == "713f0dcc41e7f32f75934fc7709a406ff71579e6"
