"""Frozen causal vetoes and a strict-priority existing-channel adapter."""
from __future__ import annotations

import numpy as np
import pandas as pd

POLICIES = ('F', 'A', 'B', 'AB', 'C', 'AC', 'BC', 'ABC', 'channel_only')
SIDE_FEE = .0002

L3_SOURCES = (
    'src/factor_lab/strategy/services/risk_off_v58_frequency_bollinger.py',
    'src/factor_lab/market_state/fda_explosive_channel_prototype.py',
    'src/factor_lab/market_state/fda_multiscale_channel_v1.py',
)


def load_l3_channel(factorlab_root):
    """Execute exact three canonical source files without unrelated package init.

    Parent/module bindings are scoped and restored, including on exceptions.
    No source rewriting, registry modification, or production use is performed.
    """
    import importlib.util
    import sys
    import types
    from pathlib import Path
    module_names = [str(Path(n).with_suffix('')).replace('src/', '', 1).replace('/', '.')
                    for n in L3_SOURCES]
    parents = ['factor_lab', 'factor_lab.strategy', 'factor_lab.strategy.services', 'factor_lab.market_state']
    names = parents + module_names
    previous = {name: sys.modules.get(name) for name in names}
    try:
        for name in parents:
            module = types.ModuleType(name)
            module.__path__ = []
            sys.modules[name] = module
        for name, relative in zip(module_names, L3_SOURCES):
            spec = importlib.util.spec_from_file_location(name, Path(factorlab_root) / relative)
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        final = sys.modules[module_names[-1]]
        return final.build_fda_multiscale_channel, final.FDAMultiscaleChannelSpec
    finally:
        for name, value in previous.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


def causal_features(open_price, close):
    close = pd.Series(np.asarray(close, float))
    opened = pd.Series(np.asarray(open_price, float))
    if not ((close > 0).all() and (opened > 0).all()
            and np.isfinite(close).all() and np.isfinite(opened).all()):
        raise ValueError('positive prices required')
    r = np.log(close).diff()
    road = r.abs().rolling(12).sum()
    q = 12 * r.pow(2).rolling(12).sum() / road.pow(2).where(road > 0)
    return pd.DataFrame({'return_log': r, 'q12': q,
        'sigma_prior': r.rolling(48).std(ddof=0).shift(1),
        'body_log': np.log(close / opened)})


def asof_channel(times, native):
    required = ['timestamp', 'decision_position_for_next_bar']
    out = pd.merge_asof(pd.DataFrame({'timestamp': pd.to_datetime(times)}),
        native[required].rename(columns={'timestamp': 'channel_observed_at'}),
        left_on='timestamp', right_on='channel_observed_at', direction='backward')
    valid = out.channel_observed_at.notna()
    assert (out.loc[valid, 'channel_observed_at'] <= out.loc[valid, 'timestamp']).all()
    out['channel'] = out.decision_position_for_next_bar.fillna(0).astype(np.int8)
    return out[['channel', 'channel_observed_at']]


def compose(base_signal, feature, channel, q_cutoff, policy):
    if policy not in POLICIES:
        raise ValueError(policy)
    base, channel = np.asarray(base_signal, int), np.asarray(channel, int)
    assert np.isin(base, [-1, 0, 1]).all() and np.isin(channel, [-1, 0, 1]).all()
    q, sigma, body = (feature[k].to_numpy(float) for k in ['q12', 'sigma_prior', 'body_log'])
    has_a, has_b, has_c = 'A' in policy, 'B' in policy, 'C' in policy
    target = np.zeros(len(base), dtype=np.int8)
    owner = np.zeros(len(base), dtype=np.int8)  # 0 flat, 1 filter, 2 channel
    veto = np.zeros(len(base), bool)
    allowed = False
    prior_channel = False
    prior_target = 0

    def blocked(i):
        a = has_a and (not np.isfinite(q[i]) or q[i] > q_cutoff)
        b = has_b and (not np.isfinite(sigma[i]) or sigma[i] <= 0
                       or base[i] * body[i] < -sigma[i])
        return bool(a or b)

    for i, signal in enumerate(base):
        fresh = i == 0 or signal != base[i - 1]
        if fresh:
            veto[i] = signal != 0 and blocked(i)
            allowed = signal != 0 and not veto[i]
        if policy == 'channel_only':
            target[i] = channel[i]
            owner[i] = 2 if channel[i] else 0
        elif has_c and channel[i] != 0:
            target[i], owner[i] = channel[i], 2
        else:
            # Handoff to a DIFFERENT filter position is a new entry and must
            # obey its currently known veto; unchanged-position handoffs cost zero.
            if prior_channel and allowed and signal != prior_target and blocked(i):
                allowed, veto[i] = False, True
            target[i] = signal if allowed else 0
            owner[i] = 1 if target[i] else 0
        prior_channel = bool((has_c or policy == 'channel_only') and channel[i] != 0)
        prior_target = int(target[i])
    if policy == 'F':
        assert np.array_equal(target, base)
    assert np.array_equal(owner == 0, target == 0)
    return target, owner, veto


def execution_fields(target, owner):
    target, owner = np.asarray(target, int), np.asarray(owner, int)
    filled = np.r_[0, target[:-1]]
    executed = np.r_[0, 0, target[:-2]]
    fill_owner = np.r_[0, owner[:-1]]
    book_owner = np.r_[0, 0, owner[:-2]]
    turnover = abs(np.diff(np.r_[0, filled]))
    return pd.DataFrame({'filled_position': filled, 'exec_pos': executed,
        'filled_owner': fill_owner, 'booked_owner': book_owner,
        'turnover_sides': turnover})


def trade_ledger(bars):
    """Derive fills and complete/unfinished trades from one unchanged snapshot.

    A trade may close or open at the final observed open; booked-position
    fragments alone would incorrectly lose that boundary event.
    """
    rows, orders = [], []
    prior = int(bars.exec_pos.iloc[0])
    reference = float(bars.previous_open.iloc[0]) if prior else 0.
    entry_index = -1
    entry_label = 'inherited_before_development'
    entry_owner = 1 if prior else 0
    for i, row in enumerate(bars.itertuples()):
        assert int(row.exec_pos) == prior
        current = int(row.filled_position)
        if current != prior:
            if prior:
                gross = prior * np.log(row.open / reference)
                sides = 1 + int(entry_index >= 0)
                rows.append({'entry_index': entry_index, 'exit_index': i,
                    'entry_label': entry_label, 'exit_label': str(row.timestamp),
                    'direction': prior, 'entry_price': reference, 'exit_price': float(row.open),
                    'gross_log': float(gross), 'fee_sides': sides,
                    'net_log': float(gross + sides * np.log1p(-SIDE_FEE)),
                    'complete': True, 'left_clipped': entry_index < 0,
                    'entry_owner': entry_owner})
                orders.append({'index': i, 'time_label': str(row.timestamp), 'action': 'exit',
                    'direction': prior, 'price': float(row.open)})
            if current:
                reference, entry_index, entry_label = float(row.open), i, str(row.timestamp)
                entry_owner = int(row.filled_owner)
                orders.append({'index': i, 'time_label': entry_label, 'action': 'entry',
                    'direction': current, 'price': reference})
            prior = current
    if prior:
        gross = prior * np.log(bars.open.iloc[-1] / reference)
        sides = int(entry_index >= 0)
        rows.append({'entry_index': entry_index, 'exit_index': len(bars) - 1,
            'entry_label': entry_label, 'exit_label': str(bars.timestamp.iloc[-1]),
            'direction': prior, 'entry_price': reference, 'exit_price': float(bars.open.iloc[-1]),
            'gross_log': float(gross), 'fee_sides': sides,
            'net_log': float(gross + sides * np.log1p(-SIDE_FEE)),
            'complete': False, 'left_clipped': entry_index < 0, 'entry_owner': entry_owner})
    trades = pd.DataFrame(rows, columns=['entry_index', 'exit_index', 'entry_label',
        'exit_label', 'direction', 'entry_price', 'exit_price', 'gross_log',
        'fee_sides', 'net_log', 'complete', 'left_clipped', 'entry_owner'])
    assert abs(trades.gross_log.sum() - bars.gross_log.sum()) < 1e-10
    assert trades.fee_sides.sum() == bars.turnover_sides.sum() == len(orders)
    assert abs(trades.net_log.sum() - bars.net_log.sum()) < 1e-10
    return trades, pd.DataFrame(orders)


def metrics(bars, years):
    trades, _ = trade_ledger(bars)
    complete = trades.loc[trades.complete.astype(bool) & ~trades.left_clipped.astype(bool)]
    rows = []
    for basis, column, trade_column in [('original_zero_cost', 'gross_log', 'gross_log'),
                                       ('uniform_fee_proxy', 'net_log', 'net_log')]:
        nav = np.exp(bars[column].cumsum().to_numpy())
        peak = np.maximum.accumulate(np.r_[1., nav])[1:]
        drawdown = 1 - nav / peak
        cagr = float(np.expm1(bars[column].sum() / years))
        mdd = float(drawdown.max())
        rows.append({'basis': basis, 'cagr': cagr, 'mdd': mdd, 'terminal_nav': float(nav[-1]),
            'calmar': cagr / mdd if mdd else 0., 'completed_trades': len(complete),
            'mean_trade_log_bp': float(complete[trade_column].mean() * 10000) if len(complete) else 0.,
            'win_rate': float((complete[trade_column] > 0).mean()) if len(complete) else 0.,
            'exposure_fraction': float(bars.exec_pos.abs().mean()),
            'turnover_sides': int(bars.turnover_sides.sum()),
            'terminal_filled_position': int(bars.filled_position.iloc[-1])})
    return rows
