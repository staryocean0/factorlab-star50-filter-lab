from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_v17.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v17_runner", RUNNER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_v17_boundary_and_checkpoint_are_fixed():
    rv = load_runner()
    assert rv.SYMBOLS == ("000688.SH", "000852.SH")
    assert rv.REF_YEARS == (2020, 2021, 2022, 2023)
    assert rv.DEV_YEARS == (2021, 2022, 2023)
    assert rv.HORIZONS == (15, 30, 60)
    assert rv.PRIMARY_LEAD_SECONDS == 15
    assert rv.EXPECTED_ROW_COUNT == 7327


def test_frozen_v16_identity_and_horizon_adaptive_map():
    rv = load_runner()
    frozen = rv.frozen_authority()
    adaptive, age_only = rv.prediction_maps(frozen)
    assert rv.EXPECTED_V16_SURFACE_BLOB == "1f88966cf5dd3fb102f0d75746d5d00434555647"
    assert frozen["source_execution_commit"] == "bcdc18d5886869865c6454fa323ebc6858090249"
    assert frozen["source_run_id"] == 34497737506
    assert len(adaptive) == 8
    assert len(age_only) == 4
    for (state, bucket), p in adaptive.items():
        assert state in {"UNSAFE", "RECOVERING"}
        assert p[15] <= p[30] <= p[60]
        assert abs(p[60] - age_only[bucket][60]) <= 1e-15


def test_frozen_component_blobs_are_fixed():
    rv = load_runner()
    assert rv.EXPECTED_V9_BLOB == "ae2a7e095df58692ef9df0dfee5856cac727ca44"
    assert rv.EXPECTED_V11_BLOB == "713f0dcc41e7f32f75934fc7709a406ff71579e6"


def test_rowwise_guard_requires_monotone_and_exact_60m_anchor():
    rv = load_runner()
    x = pd.DataFrame(
        {
            "realtime_reason": ["scored", "scored", "partial_normal"],
            "realtime_p_15m": [0.01, 0.20, float("nan")],
            "realtime_p_30m": [0.10, 0.50, float("nan")],
            "realtime_p_60m": [0.80, 0.90, float("nan")],
            "reference_p_60m": [0.80, 0.90, 0.95],
        }
    )
    g = rv.rowwise_guard(x)
    assert g["scored_rows"] == 2
    assert g["monotone_all_rows"] is True
    assert g["sixty_minute_anchor_exact"] is True
    assert g["max_abs_60m_anchor_diff"] == 0.0
