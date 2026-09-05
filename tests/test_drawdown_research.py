"""Synthetic financial-account and causality checks; no market data is read."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from star50_filter.drawdown_diagnostics import drawdown_summary
from star50_filter.drawdown_research import (
    account,
    causal_states,
    exact_gap_attribution,
    lag,
    open_component_attribution,
    targets,
)


def synthetic_frame(days, opens=None, closes=None):
    n = len(days)
    opens = np.asarray(opens if opens is not None else np.exp(np.arange(n) / 100), dtype=float)
    closes = np.asarray(closes if closes is not None else opens * 1.002, dtype=float)
    return pd.DataFrame(
        {
            "trading_day": days,
            "timestamp": pd.date_range("2020-12-31", periods=n, freq="5min"),
            "open": opens,
            "close": closes,
            "year": pd.Series(days).str[:4].astype(int),
        }
    )


def test_signal_earns_only_next_open_interval_and_costs_at_execution_open():
    df = synthetic_frame(["2020-12-31"] + ["2021-01-04"] * 5)
    signal = np.array([1.0, -1, 1, 1, -1, 1])
    result = account(df, signal, cost_bps=3)
    # The first scored mark opens the account flat; the pre-close target enters
    # at that mark, pays its cost there, and earns its first return at mark 2.
    np.testing.assert_array_equal(result.position, [0, 0, 1, -1, 1, 1])
    np.testing.assert_array_equal(result.turnover, [0, 1, 2, 2, 0, 1])
    assert result.gross_log_pnl.iloc[1] == 0
    assert result.net_log_pnl.iloc[1] == pytest.approx(np.log1p(-0.0003))
    np.testing.assert_allclose(result.gross_log_pnl, result.position * result.market_log_return)
    np.testing.assert_allclose(result.cost_log, -np.log1p(-result.turnover * 0.0003))
    assert result.turnover.iloc[-1] == abs(result.position.iloc[-1])


def test_unliquidated_year_prefix_matches_full_continuous_account():
    days = ["2020-12-31"] * 2 + ["2021-12-31"] * 3 + ["2022-01-04"] * 4
    df = synthetic_frame(days)
    signal = np.array([1, 1, -1, 1, -1, -1, 1, 1, -1], dtype=float)
    first_year = account(df.iloc[:5], signal[:5], cost_bps=5, terminal_liquidation=False)
    full = account(df, signal, cost_bps=5, terminal_liquidation=False)
    pd.testing.assert_frame_equal(first_year, full.iloc[:5])
    # The position and high-water accounting are not reset at the second year.
    assert full.position.iloc[5] == signal[3]
    full_returns = full.loc[full.is_development, "net_log_pnl"].to_numpy()
    summary = drawdown_summary(full_returns)
    assert summary["n_returns"] == 7


def test_simple_equity_uses_signed_simple_returns_before_costs():
    df = synthetic_frame(["2021-01-04"] * 4, opens=[100, 110, 88, 96.8])
    signal = np.array([-1.0, 0.5, 1, 1])
    result = account(df, signal, cost_bps=1, mode="simple_equity")
    expected_gross = np.log1p(result.position.to_numpy() * np.array([0, 0.1, -0.2, 0.1]))
    np.testing.assert_allclose(result.gross_log_pnl, expected_gross, atol=1e-15)
    np.testing.assert_allclose(result.net_log_pnl, expected_gross + np.log1p(-result.turnover / 10000))
    # A short earns +20% equity on a -20% index move, not +25% inverse NAV.
    assert np.expm1(result.gross_log_pnl.iloc[2]) == pytest.approx(0.2)


def test_target_or_price_after_current_close_cannot_change_available_feature_or_past_pnl():
    n = 1900
    rng = np.random.default_rng(7)
    x = np.cumsum(rng.normal(0, 0.004, n))
    days = ["2020-12-31"] * 200 + ["2021-01-04"] * (n - 200)
    df = synthetic_frame(days, np.exp(x), np.exp(x + 0.001))
    boundary = 1600
    revised = df.copy()
    revised.loc[boundary + 1 :, ["open", "close"]] *= np.exp(np.linspace(0.1, 3, n - boundary - 1))[:, None]
    before, after = causal_states(df), causal_states(revised)
    pd.testing.assert_frame_equal(before.iloc[: boundary + 1], after.iloc[: boundary + 1])
    before_targets, after_targets = targets(before), targets(after)
    for name in before_targets:
        original = account(df, before_targets[name], cost_bps=3)
        revised_account = account(revised, after_targets[name], cost_bps=3)
        pd.testing.assert_frame_equal(original.iloc[: boundary + 1], revised_account.iloc[: boundary + 1])
        # A target at close j is the holding for the open[j+1] -> open[j+2]
        # interval, matching the lag2 state used for descriptive condition cells.
        np.testing.assert_array_equal(
            original.position.iloc[201:], lag(before_targets[name], 2, fill=0)[201:]
        )


def test_mean_exposure_matched_constant_has_identical_interval_average():
    df = synthetic_frame(["2020-12-31"] * 2 + ["2021-12-31"] * 6 + ["2022-01-04"] * 4)
    baseline = np.array([1, 1, -1, -1, 1, 1, -1, -1, 1, -1, 1, 1], dtype=float)
    dynamic = baseline * np.array([1, 0.5, 1, 0.5, 0.5, 1, 1, 0.5, 1, 0.5, 1, 1])
    qb, qd = account(df, baseline).position, account(df, dynamic).position
    mask = df.year == 2022
    alpha = qd.loc[mask].abs().sum() / qb.loc[mask].abs().sum()
    constant = account(df, alpha * baseline)
    assert constant.position.loc[mask].abs().mean() == pytest.approx(qd.loc[mask].abs().mean())
    # This alpha is an interval-matched retrospective comparator, not a
    # deployable causal feature. The mechanism policies themselves are causal.


def test_open_and_gap_attribution_are_exact_on_nav_peak_to_trough_slice():
    days = ["2020-12-31"] + ["2021-01-04"] * 3 + ["2021-01-05"] * 3
    df = synthetic_frame(days, opens=[100, 102, 105, 100, 95, 98, 106], closes=[101, 103, 103, 97, 96, 100, 107])
    position = np.array([0, 1, 1, 1, 1, -1, 1], dtype=float)
    market_log_return = np.diff(np.log(df.open), prepend=np.log(df.open.iloc[0]))
    pnl = position * market_log_return
    components = open_component_attribution(df, position)
    gaps = exact_gap_attribution(df, position)
    np.testing.assert_allclose(components.sum(axis=1), pnl, atol=1e-14)
    np.testing.assert_allclose(gaps.sum(axis=1), pnl, atol=1e-14)
    summary = drawdown_summary(pnl[1:])
    event = summary["episodes"][0]
    p, t = event["peak_index"], event["trough_index"]
    # NAV indexes refer to before/after return counts. A score-frame iloc[p:t]
    # therefore contains exactly the peak-to-trough returns, without an offset.
    decline = pnl[1:][p:t]
    assert -np.expm1(decline.sum()) == pytest.approx(event["drawdown"])
    assert components.iloc[1:].iloc[p:t].sum().sum() == pytest.approx(decline.sum())
    assert gaps.iloc[1:].iloc[p:t].sum().sum() == pytest.approx(decline.sum())
    assert gaps.overnight_gap_log_pnl.iloc[4] == pytest.approx(np.log(95 / 97))
    assert gaps.overnight_gap_log_pnl.iloc[3] == 0


def test_loader_excludes_post_2025_prices_before_price_validation():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("baseline_for_cutoff_test", root / "scripts/reproduce_historical_baseline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Synthetic sentinel after the allowed boundary: invalid price must never
    # reach numeric validation, filters or accounts. No external data is read.
    frame = pd.DataFrame(
        {"trading_day": ["2025-12-31", "2026-01-05"], "open": [100, "excluded"], "close": [101, "excluded"]}
    )
    allowed = module._normalise_bars(frame)
    assert len(allowed) == 1
    assert allowed.trading_day.iloc[0] == "2025-12-31"
