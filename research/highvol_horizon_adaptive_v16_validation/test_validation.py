from pathlib import Path

import numpy as np
import pandas as pd

import run_validation as rv


def test_frozen_v16_authority_and_surface_contract():
    frozen = rv.frozen_authority()
    adaptive, age_only = rv.prediction_maps(frozen)
    assert frozen["validation_authorized"] is True
    assert len(adaptive) == 8
    assert len(age_only) == 4
    for (state, bucket), p in adaptive.items():
        assert state in {"UNSAFE", "RECOVERING"}
        assert p[15] <= p[30] <= p[60]
        assert abs(p[60] - age_only[bucket][60]) <= 1e-15


def test_rowwise_guard_requires_monotone_and_exact_60m_anchor():
    frozen = rv.frozen_authority()
    adaptive, age_only = rv.prediction_maps(frozen)
    rows = pd.DataFrame(
        {
            "current_state": ["UNSAFE", "RECOVERING"],
            "age_bucket": ["LT15", "GE45"],
        }
    )
    g = rv.rowwise_surface_guard(rows, adaptive, age_only)
    assert g["passed"] is True
    assert g["monotone_all_rows"] is True
    assert g["max_abs_60m_anchor_diff"] <= 1e-15


def test_synthesis_uses_end_of_each_five_minute_block():
    day = "2023-01-03"
    am = pd.date_range(f"{day} 09:31:00", periods=120, freq="min")
    pm = pd.date_range(f"{day} 13:01:00", periods=120, freq="min")
    ts = am.append(pm)
    x = pd.DataFrame(
        {
            "symbol": "000688.SH",
            "trading_day": day,
            "timestamp": ts,
            "close": np.arange(240, dtype=float),
        }
    )
    z = rv.synthesize_5m(x)
    assert len(z) == 48
    assert z.close.iloc[:24].tolist() == list(np.arange(4, 120, 5, dtype=float))
    assert z.close.iloc[24:].tolist() == list(np.arange(124, 240, 5, dtype=float))
