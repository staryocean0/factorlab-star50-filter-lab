import numpy as np
import pandas as pd
import pytest

from star50_filter.session_aware_information_bounds import (
    AUTHORITATIVE_SOURCE_ROWS,
    IntakeError,
    adjudicate_source_identity,
    evaluate_information_set_bounds,
    motion_concentration,
    summarize_bounds,
)


def support_rows(leg_id, moves, *, missing=()):
    rows = []
    price = 100.0
    for ordinal, move in enumerate(moves):
        opened = price
        closed = price + float(move)
        rows.append({
            "leg_id": leg_id,
            "step_ordinal": ordinal,
            "observed": ordinal not in set(missing),
            "open": opened,
            "high": max(opened, closed),
            "low": min(opened, closed),
            "close": closed,
        })
        price = closed
    return rows


def test_inherited_motion_concentration_equal_and_single_step():
    assert motion_concentration(np.array([0, 1, 2, 3, 4, 5], float)) == pytest.approx(1.0)
    assert motion_concentration(np.array([0, 5, 5, 5, 5, 5], float)) == pytest.approx(5.0)


def test_complete_actual_support_collapses_to_oracle_and_offset_can_have_six_steps():
    legs = pd.DataFrame([
        {"leg_id": "equal5", "expected_step_count": 5, "offset": 0, "published": True},
        {"leg_id": "equal6", "expected_step_count": 6, "offset": 1, "published": True},
    ])
    support = pd.DataFrame(support_rows("equal5", [1, 1, 1, 1, 1]) + support_rows("equal6", [1, 1, 1, 1, 1, 1]))
    out = evaluate_information_set_bounds(legs, support)
    a = out.set_index("leg_id").loc["equal5"]
    b = out.set_index("leg_id").loc["equal6"]
    assert a.oracle_comparable
    assert a.concentration_lower == pytest.approx(1.0)
    assert a.concentration_upper == pytest.approx(1.0)
    assert b.expected_step_count == 6
    assert b.oracle_comparable
    assert b.concentration_lower == pytest.approx(1.0)
    assert b.concentration_upper == pytest.approx(1.0)


def test_missing_source_step_is_retained_with_full_universal_interval():
    legs = pd.DataFrame([{
        "leg_id": "session-edge", "expected_step_count": 5,
        "boundary_class": "session_edge", "strict_pair": True, "qualified": True,
    }])
    support = pd.DataFrame(support_rows("session-edge", [1, 1, 1, 1, 1], missing={2}))
    out = evaluate_information_set_bounds(legs, support)
    row = out.iloc[0]
    assert len(out) == 1  # boundary leg is not silently dropped
    assert not row.support_complete
    assert row.support_gap
    assert not row.oracle_comparable
    assert row.universal_bound_used
    assert row.concentration_lower == pytest.approx(1.0)
    assert row.concentration_upper == pytest.approx(5.0)
    assert row.bound_reason == "support_gap"
    assert row.strict_pair and row.qualified


def test_complete_support_uses_current_bar_open_not_previous_adjacent_close():
    legs = pd.DataFrame([{
        "leg_id": "am-open", "expected_step_count": 2,
        "native_open": 100.0, "native_high": 102.0,
        "native_low": 100.0, "native_close": 102.0,
    }])
    support = pd.DataFrame(support_rows("am-open", [1, 1]))
    out = evaluate_information_set_bounds(legs, support)
    row = out.iloc[0]
    assert row.ohlc_consistency == "match"
    assert row.oracle_comparable
    assert row.motion_total == pytest.approx(2.0)


def test_ohlc_mismatch_fails_closed_to_universal_bound_not_false_oracle():
    legs = pd.DataFrame([{
        "leg_id": "bad-envelope", "expected_step_count": 2,
        "native_open": 99.0, "native_high": 102.0,
        "native_low": 99.0, "native_close": 102.0,
    }])
    support = pd.DataFrame(support_rows("bad-envelope", [1, 1]))
    out = evaluate_information_set_bounds(legs, support)
    row = out.iloc[0]
    assert row.support_complete
    assert row.ohlc_consistency == "mismatch"
    assert not row.oracle_comparable
    assert row.universal_bound_used
    assert row.concentration_lower == pytest.approx(1.0)
    assert row.concentration_upper == pytest.approx(2.0)
    assert row.bound_reason == "data_consistency_mismatch"


def test_authoritative_identity_accepts_only_expected_surface_by_default():
    identity = adjudicate_source_identity(AUTHORITATIVE_SOURCE_ROWS)
    assert identity.status == "accepted"
    with pytest.raises(IntakeError, match="factorlab_1m_official"):
        adjudicate_source_identity(350_561)
    diagnostic = adjudicate_source_identity(350_561, authoritative=False)
    assert diagnostic.status == "rejected_factorlab_1m_official_is_not_datahub_authority"


def test_results_blind_gate_rejects_future_or_trading_outcomes():
    legs = pd.DataFrame([{"leg_id": "x", "expected_step_count": 1, "future_return": 0.01}])
    support = pd.DataFrame(support_rows("x", [1]))
    with pytest.raises(IntakeError, match="results-blind"):
        evaluate_information_set_bounds(legs, support)


def test_topology_rejects_duplicate_or_out_of_range_ordinals():
    legs = pd.DataFrame([{"leg_id": "x", "expected_step_count": 2}])
    support = pd.DataFrame(support_rows("x", [1, 1]))
    support.loc[1, "step_ordinal"] = 0
    with pytest.raises(IntakeError, match="duplicate step_ordinal"):
        evaluate_information_set_bounds(legs, support)

    support = pd.DataFrame(support_rows("x", [1, 1]))
    support.loc[1, "step_ordinal"] = 2
    with pytest.raises(IntakeError, match="outside"):
        evaluate_information_set_bounds(legs, support)


def test_summary_is_topology_only_and_stratifies_frozen_overlays():
    legs = pd.DataFrame([
        {"leg_id": "a", "expected_step_count": 2, "offset": 0, "published": True},
        {"leg_id": "b", "expected_step_count": 2, "offset": 1, "published": True},
    ])
    support = pd.DataFrame(support_rows("a", [1, 1]) + support_rows("b", [1, 1], missing={1}))
    bounds = evaluate_information_set_bounds(legs, support)
    summary = summarize_bounds(bounds)
    assert summary["legs"] == 2
    assert summary["support_gap"] == 1
    assert summary["oracle_comparable"] == 1
    assert summary["by_offset"]["0"]["oracle_comparable"] == 1
    assert summary["by_offset"]["1"]["support_gap"] == 1
    assert not any("return" in key or "pnl" in key for key in summary)
