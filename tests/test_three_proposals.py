import numpy as np
import pandas as pd

from star50_filter.three_proposals import (SIDE_FEE, L3_SOURCES, asof_channel, causal_features,
    compose, execution_fields, trade_ledger, load_l3_channel)


def features(q, body):
    return pd.DataFrame({'q12': q, 'body_log': body, 'sigma_prior': .01})


def test_features_causal_prefix():
    rng = np.random.default_rng(7)
    close = np.exp(rng.normal(0, .003, 400).cumsum())
    opened = np.r_[close[0], close[:-1]]
    full = causal_features(opened, close)
    pd.testing.assert_frame_equal(full.iloc[:200], causal_features(opened[:200], close[:200]))


def test_veto_closes_old_does_not_keep_opposite_position():
    base = [1, 1, -1, -1, -1, 1]
    target, _, _ = compose(base, features([1, 1, 1, 1, 1, 1], [0, 0, .02, -.03, 0, 0]),
                            [0] * 6, 2, 'B')
    assert target.tolist() == [1, 1, 0, 0, 0, 1]


def test_a_latches_until_new_original_reversal():
    target, _, _ = compose([1, 1, -1, -1, 1], features([3, 1, 1, 3, 1], [0] * 5),
                            [0] * 5, 2, 'A')
    assert target.tolist() == [0, 0, -1, -1, 1]


def test_b_uses_only_large_opposite_body():
    target, _, _ = compose([1, -1, 1, -1], features([1] * 4, [-.009, .01, -.011, .02]),
                            [0] * 4, 2, 'B')
    assert target.tolist() == [1, -1, 0, 0]


def test_channel_has_priority_and_handoff_veto():
    target, owner, _ = compose([1, 1, 1, 1], features([1] * 4, [0, 0, -.02, 0]),
                                [-1, -1, 0, 0], 2, 'BC')
    assert target.tolist() == [-1, -1, 0, 0]
    assert owner.tolist() == [2, 2, 0, 0]


def test_asof_does_not_see_future_channel():
    times = pd.date_range('2021-01-04 09:35', periods=5, freq='5min')
    native = pd.DataFrame({'timestamp': times[[1, 4]], 'decision_position_for_next_bar': [1, -1]})
    assert asof_channel(times, native).channel.tolist() == [0, 1, 1, 1, -1]


def test_fill_cost_precedes_first_completed_interval():
    f = execution_fields([1, -1, 0, 0], [1, 1, 0, 0])
    assert f.filled_position.tolist() == [0, 1, -1, 0]
    assert f.exec_pos.tolist() == [0, 0, 1, -1]
    assert f.turnover_sides.tolist() == [0, 1, 2, 1]


def test_final_bar_open_and_close_are_not_lost():
    f = execution_fields([1, -1, 1, 1], [1] * 4)
    f['timestamp'] = pd.date_range('2021-01-04 09:35', periods=4, freq='5min')
    f['open'] = [100., 102., 101., 105.]
    f['previous_open'] = [100., 100., 102., 101.]
    f['gross_log'] = f.exec_pos * np.log(f.open / f.previous_open)
    f['net_log'] = f.gross_log + f.turnover_sides * np.log1p(-SIDE_FEE)
    trades, orders = trade_ledger(f)
    assert trades.complete.tolist() == [True, True, False]
    assert trades.iloc[-1].gross_log == 0
    assert len(orders) == 5


def test_no_trade_is_valid_empty_ledger():
    f = execution_fields([0] * 4, [0] * 4)
    f['timestamp'] = pd.date_range('2021-01-04', periods=4, freq='5min')
    f['open'] = f['previous_open'] = 100.
    f['gross_log'] = f['net_log'] = 0.
    trades, orders = trade_ledger(f)
    assert trades.empty and orders.empty


def test_exact_l3_prefix_and_scoped_module_restoration():
    from pathlib import Path
    import sys
    import pytest
    root = Path('/home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab')
    missing = [relative for relative in L3_SOURCES if not (root / relative).is_file()]
    if missing:
        pytest.skip(
            'canonical local L3 sources are not mounted in this environment; '
            'exact-prefix assertions remain mandatory when those frozen sources are present: '
            + ', '.join(missing)
        )
    before = {k: v for k, v in sys.modules.items() if k.startswith('factor_lab')}
    build, spec = load_l3_channel(root)
    after = {k: v for k, v in sys.modules.items() if k.startswith('factor_lab')}
    assert before == after
    rng = np.random.default_rng(17)
    close = pd.Series(np.exp(rng.normal(0, .003, 600).cumsum()),
        index=pd.date_range('2020-01-01', periods=600, freq='15min'))
    full = build(close, spec('opposite_rail', (48, 96)))
    prefix = build(close.iloc[:430], spec('opposite_rail', (48, 96)))
    pd.testing.assert_frame_equal(full.iloc[:430], prefix)
