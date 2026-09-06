from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from star50_filter.slope_union import build_signals
from star50_filter.slope_union_v2 import Policy, account, family, features, targets
from test_slope_union import bars_from_returns


def test_family_and_v1_exact():
    policies = family()
    assert len(policies) == len({p.id for p in policies}) == 324
    assert Policy() in policies
    rng = np.random.default_rng(71)
    bars = bars_from_returns(rng.normal(0, 0.001, 1500) + 0.001 * np.sin(np.arange(1500) / 50))
    _, slopes, sigma = features(bars.close)
    np.testing.assert_array_equal(targets(slopes, sigma[240], Policy()), build_signals(bars).target_at_close)


def test_cooldown_and_confirmation_and_mirror():
    s = np.repeat(np.array([0, 1, 1, 1, -1, -1, -1, 1, 1, 1, -1, -1, -1])[:, None], 5, axis=1)
    sigma = np.ones(len(s))
    p = replace(Policy(), entry_confirm=3, cooldown=5)
    t = targets(s, sigma, p)
    assert list(t[:5]) == [0, 0, 0, 1, 0]
    assert np.all(t[5:12] == 0)
    assert t[12] == -1
    np.testing.assert_array_equal(t, -targets(-s, sigma, p))


def test_future_prefix():
    bars = bars_from_returns(np.random.default_rng(4).normal(0, 0.001, 1800))
    _, s, v = features(bars.close)
    for p in [Policy(), replace(Policy(), entry_confirm=3, cooldown=5)]:
        _, ss, vv = features(bars.close.iloc[:900])
        np.testing.assert_array_equal(targets(s, v[240], p)[:900], targets(ss, vv[240], p))


@pytest.mark.parametrize("side", [1, -1])
def test_fixed_entry_units_simple_returns_and_two_fees(side):
    times = pd.Series(pd.date_range("2021-01-04 09:30", periods=4, freq="min"))
    ledger, daily, nav, m = account([100, 100, 110, 110], times, [side, side, 0, 0], fee_bps=2)
    expected = (side * 0.1 - 0.0002 * 2.1) / 1.0002
    assert np.isclose(ledger.net_bp.iloc[0], expected * 10000)
    assert np.isclose(nav[-1], 1 + expected)
    assert ledger.entry_i.iloc[0] == 1 and ledger.exit_i.iloc[0] == 3
    assert m["trades"] == 1


def test_reversal_and_no_terminal_signal_execution():
    times = pd.Series(pd.date_range("2021-01-04 09:30", periods=5, freq="min"))
    ledger, _, nav, _ = account([100, 100, 110, 99, 500], times, [1, -1, 0, 0, 1], fee_bps=0)
    assert len(ledger) == 2
    assert np.isclose(nav[-1], 1.1 * 1.1)
    assert list(ledger.side) == [1, -1]
    assert ledger.exit_i.max() == 3


def test_annual_forced_exit_and_flat_account():
    times = pd.Series(pd.date_range("2021-01-04 09:30", periods=4, freq="min"))
    ledger, _, _, _ = account([100, 100, 110, 120], times, [1, 1, 1, 1])
    assert ledger.forced_year_end.all()
    ledger, daily, nav, _ = account([100, 100, 110, 120], times, [0, 0, 0, 0])
    assert ledger.empty and np.all(nav == 1) and (daily["return"] == 0).all()


def test_last_open_spike_is_not_earned_by_new_signal():
    times = pd.Series(pd.date_range("2021-01-04 09:30", periods=4, freq="min"))
    ledger, _, nav, _ = account([100, 100, 100, 200], times, [0, 0, 1, 1])
    assert ledger.empty and np.all(nav == 1)
