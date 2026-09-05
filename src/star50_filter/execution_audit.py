"""Frozen-signal execution diagnostics; no tradable-price or feed-latency claim.

Five-minute signals remain unchanged. One-minute data are execution/mark
carriers only; no new signal bars are constructed. All clock conventions are
explicit assumptions backed by endpoint reconciliation, not tick timestamps.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


SCENARIOS = ('legacy_on_minute', 'delay_1m', 'delay_1m_observed',
             'literal_publication')
POLICIES = ('baseline', 'slow_conflict_half', 'constant_075', 'constant_050')


def wall_close(df):
    """Exported Z labels are documented Shanghai wall-clock labels."""
    return pd.to_datetime(df.timestamp.astype(str).str[:19]).to_numpy('datetime64[ns]')


def publication_clock(df):
    # Unlike timestamp, available_at has genuine explicit offsets. Keep them.
    return (pd.to_datetime(df.available_at, utc=True, format='mixed')
            .dt.tz_convert('Asia/Shanghai').dt.tz_localize(None)
            .to_numpy('datetime64[ns]'))


def coarse_open_clock(bars, minute=None):
    close = wall_close(bars)
    widths = np.full(len(bars), 5)
    if 'export_view_id' in bars:
        offset = bars.export_view_id.astype(str).str.match(r'5m_offset_[1-4]$').to_numpy()
        clock = pd.DatetimeIndex(close)
        session = np.where(clock.hour < 12, 'AM', 'PM')
        key = bars.trading_day.astype(str).to_numpy() + session
        first = np.r_[True, key[1:] != key[:-1]]
        widths[first & offset] = 6
    starts = close - widths.astype('timedelta64[m]')
    if minute is not None:
        mo = wall_close(minute) - np.timedelta64(1, 'm')
        idx = np.searchsorted(mo, starts)
        if np.any(idx >= len(mo)) or not np.array_equal(mo[idx], starts):
            raise ValueError('Missing nominal opening minute')
        synthetic = minute.source_kind.astype(str).str.contains('causal_flat_missing_minute').to_numpy()
        missing = synthetic[idx]
        if missing.any():
            observed_idx = np.flatnonzero(~synthetic)
            pos = np.searchsorted(observed_idx, idx[missing])
            if np.any(pos >= len(observed_idx)):
                raise ValueError('No observed opening quote')
            replacement = mo[observed_idx[pos]]
            if np.any(replacement >= close[missing]):
                raise ValueError('No observed quote inside coarse bar')
            starts[missing] = replacement
    return starts


def endpoint_audit(bars, minute):
    mc = wall_close(minute)
    bc = wall_close(bars)
    starts = coarse_open_clock(bars, minute)
    mo = mc - np.timedelta64(1, 'm')
    oi = np.searchsorted(mo, starts)
    ci = np.searchsorted(mc, bc)
    if np.any(oi >= len(mc)) or np.any(ci >= len(mc)):
        raise ValueError('Missing minute endpoint')
    if not (np.array_equal(mo[oi], starts) and np.array_equal(mc[ci], bc)):
        raise ValueError('Source endpoint clocks do not match')
    oe = np.abs(bars.open.to_numpy() - minute.open.to_numpy()[oi])
    ce = np.abs(bars.close.to_numpy() - minute.close.to_numpy()[ci])
    return {'bars': len(bars), 'open_mismatches': int((oe > 1e-10).sum()),
            'close_mismatches': int((ce > 1e-10).sum()),
            'max_open_error': float(oe.max()), 'max_close_error': float(ce.max()),
            'open_endpoint_synthetic': int(minute.source_kind.astype(str)
                .str.contains('causal_flat_missing_minute').to_numpy()[oi].sum()),
            'close_endpoint_synthetic': int(minute.source_kind.astype(str)
                .str.contains('causal_flat_missing_minute').to_numpy()[ci].sum()),
            'publication_after_close': int((publication_clock(bars) > bc).sum())}


def schedule_sources(bars, minute, scenario):
    """Return latest source signal row active AFTER each minute-open event.

    Same-time batch releases use the latest completed source. Delayed orders
    that coincide also use the latest source; stale intermediate orders never
    generate phantom turnover. Synthetic marks are retained but can be skipped
    as execution events.
    """
    if scenario not in SCENARIOS:
        raise ValueError('Unregistered scenario')
    bc = wall_close(bars)
    mo = wall_close(minute) - np.timedelta64(1, 'm')
    scheduled = coarse_open_clock(bars, minute)
    signal_row = np.arange(len(bars), dtype=np.int64) - 1
    if scenario == 'literal_publication':
        release = np.maximum(bc, publication_clock(bars))
        # A recursive signal also depends on every preceding bar.
        release = np.maximum.accumulate(release)
        signal_row = np.searchsorted(release, scheduled, side='right') - 1
    desired = scheduled.copy()
    if scenario in ('delay_1m', 'delay_1m_observed'):
        desired += np.timedelta64(1, 'm')
    valid_minutes = np.arange(len(mo))
    if scenario == 'delay_1m_observed':
        observed = ~minute.source_kind.astype(str).str.contains(
            'causal_flat_missing_minute').to_numpy()
        valid_minutes = valid_minutes[observed]
    locations = np.searchsorted(mo[valid_minutes], desired, side='left')
    possible = locations < len(valid_minutes)
    event_i = valid_minutes[locations[possible]]
    source = signal_row[possible]
    scheduled = scheduled[possible]
    # Flat score-account boundary, including delayed warmup orders.
    start_clock = coarse_open_clock(bars, minute)[
        np.flatnonzero(bars.trading_day.astype(str).to_numpy() >= '2021-01-01')[0]]
    keep = (source >= 0) & (scheduled >= start_clock)
    event_i, source = event_i[keep], source[keep]
    events = np.full(len(mo), -1, dtype=np.int64)
    # Indexed assignment resolves collisions in chronological source order.
    events[event_i] = source
    latest_event = np.maximum.accumulate(np.where(events >= 0, np.arange(len(mo)), -1))
    active = np.full(len(mo), -1, dtype=np.int64)
    active[latest_event >= 0] = events[latest_event[latest_event >= 0]]
    used = active >= 0
    if np.any(bc[active[used]] > mo[used]):
        raise AssertionError('Signal used before close')
    if scenario == 'literal_publication':
        if np.any(publication_clock(bars)[active[used]] > mo[used]):
            raise AssertionError('Signal used before publication')
    return active


def minute_account(bars, minute, target, scenario, terminal_liquidation=True,
                   active_sources=None):
    """Cost-independent sufficient account snapshot at minute OPEN marks."""
    source = (schedule_sources(bars, minute, scenario) if active_sources is None
              else np.asarray(active_sources).copy())
    mo = wall_close(minute) - np.timedelta64(1, 'm')
    bo = coarse_open_clock(bars, minute)
    scored = bars.trading_day.astype(str).to_numpy() >= '2021-01-01'
    start = bo[np.flatnonzero(scored)[0]]
    end = bo[-1] if terminal_liquidation else mo[-1]
    q_after = np.zeros(len(minute))
    used = source >= 0
    q_after[used] = np.asarray(target)[source[used]]
    q_after[mo < start] = 0
    if terminal_liquidation:
        q_after[mo >= end] = 0
    q_before = np.r_[0., q_after[:-1]]
    market = np.r_[0., np.diff(np.log(minute.open.to_numpy(dtype=float)))]
    turnover = np.abs(q_after - q_before)
    out = pd.DataFrame({'trading_day': minute.trading_day.astype(str),
                        'timestamp': mo, 'mark_open': minute.open.to_numpy(),
                        'market_log_return': market, 'q_before': q_before,
                        'q_after': q_after, 'turnover': turnover,
                        'gross_log_pnl': q_before * market,
                        'source_after': source,
                        'synthetic_mark': minute.source_kind.astype(str).str.contains(
                            'causal_flat_missing_minute').to_numpy()})
    out = out.loc[(mo >= start) & (mo <= end)].reset_index(drop=True)
    if not np.isfinite(out.gross_log_pnl).all():
        raise ValueError('Nonfinite account')
    return out


def reprice(snapshot, cost_bps, scale=1.):
    fee = cost_bps * scale * snapshot.turnover.to_numpy() / 10000.
    if np.any(fee >= 1):
        raise ValueError('Bankrupt transaction cost')
    cost_log = -np.log1p(-fee)
    gross = scale * snapshot.gross_log_pnl.to_numpy()
    return gross - cost_log, cost_log


def condition_attribution(snapshot, states):
    src_after = snapshot.source_after.to_numpy(dtype=int)
    # The first scored minute has no earned exposure. For later rows the
    # prior source explains the earned interval, even when a new order arrives.
    src_before = np.r_[-1, src_after[:-1]]
    good = src_before >= 0
    slow = np.zeros(len(snapshot), dtype=bool)
    chop = np.zeros(len(snapshot), dtype=bool)
    slow[good] = states.slow_conflict.to_numpy()[src_before[good]]
    chop[good] = states.chop.to_numpy()[src_before[good]]
    return np.where(slow, np.where(chop, 'both', 'slow_only'),
                    np.where(chop, 'chop_only', 'neither'))


def signed_opportunity(base, slow, base_cost, slow_cost, mask=None):
    """Exact removed wins/losses; outcomes are hindsight, not runtime states."""
    if mask is None:
        mask = np.ones(len(base), dtype=bool)
    b = base.loc[mask]
    s = slow.loc[mask]
    delta = s.gross_log_pnl.to_numpy() - b.gross_log_pnl.to_numpy()
    wins_removed = float(-delta[delta < 0].sum())
    losses_avoided = float(delta[delta > 0].sum())
    savings = float((base_cost - slow_cost)[mask].sum())
    return {'wins_removed_log': wins_removed, 'losses_avoided_log': losses_avoided,
            'gross_delta_log': float(delta.sum()), 'cost_savings_log': savings,
            'net_delta_log': losses_avoided - wins_removed + savings}
