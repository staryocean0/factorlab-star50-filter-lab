from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_validation.py"
FROZEN = HERE.parent / "highvol_horizon_state_value_v14" / "FROZEN_HORIZON_SURFACE.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("v14_validation", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_validation_boundary_is_frozen():
    mod = load_runner()
    assert mod.SYMBOLS == ("000688.SH", "000852.SH")
    assert mod.VAL_YEARS == (2024, 2025, 2026)
    assert mod.REF_YEARS == (2020, 2021, 2022, 2023, 2024, 2025, 2026)
    assert mod.HORIZONS == (15, 30, 60)
    assert mod.CUTOFF == "2026-08-21"


def test_sealed_2026_inputs_are_fixed():
    mod = load_runner()
    assert mod.EXPECTED_2026_BLOBS == {
        "000688.SH": "4626fb307bbcae1c417ddcd69ac694cf322c8bbc",
        "000852.SH": "8de5cd3caab99dbacae229a2c87f15c4ff2f8558",
    }


def test_frozen_horizon_surface_identity_and_role():
    mod = load_runner()
    frozen = json.loads(FROZEN.read_text())
    assert mod.EXPECTED_FROZEN_SURFACE_BLOB == "be06a4988fb4a602e2b72d115268c926421aa1f5"
    assert frozen["source_execution_commit"] == "a9223748933fc842a68865a3837e24f49f014691"
    assert frozen["source_run_id"] == 34454169246
    assert frozen["source_artifact_id"] == 10142758729
    assert frozen["horizons_minutes"] == [15, 30, 60]
    assert frozen["threshold_search_performed"] is False
    assert frozen["pnl_computed"] is False
    assert frozen["trading_rule_created"] is False
    assert frozen["production_authority"] is False


def test_synthesis_contract_selects_fifth_minute_of_each_block():
    mod = load_runner()
    import pandas as pd
    rows = []
    day = "2023-01-03"
    for i in range(240):
        if i < 120:
            ts = pd.Timestamp(day + " 09:31:00") + pd.Timedelta(minutes=i)
        else:
            ts = pd.Timestamp(day + " 13:01:00") + pd.Timedelta(minutes=i - 120)
        rows.append({"symbol": "X", "trading_day": day, "timestamp": ts, "close": float(i)})
    syn = mod.synthesize_5m(pd.DataFrame(rows))
    assert len(syn) == 48
    assert syn.close.iloc[:3].tolist() == [4.0, 9.0, 14.0]
    assert syn.close.iloc[24:27].tolist() == [124.0, 129.0, 134.0]
    assert syn.close.iloc[-1] == 239.0
