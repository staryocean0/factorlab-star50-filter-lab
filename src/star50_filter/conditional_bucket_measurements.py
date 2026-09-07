"""Causal measurement candidates; no fitted cutoffs, buckets or trading vetoes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from star50_filter.filters import butter_lowpass

FEATURES = (
    'work_efficiency_48', 'threshold_work_amplitude_48',
    'fast_work_velocity_48', 'slow_opposition_strength_48',
    'slow_directional_efficiency_48', 'reversal_count_48',
    'work_slow_direction_agreement', 'work_travel_threshold_12',
)


def _ratio(numerator, denominator):
    return numerator / denominator.where(denominator > 1e-12)


def causal_measurements(close, signal_position):
    """Inputs are completed 5m+0 bars; row i never uses row i+1 or later.

    The signal is the frozen original signal, not a fitted or bucketed policy.
    Missing warmup/zero-denominator observations stay missing, never fail-open.
    """
    price = pd.Series(np.asarray(close, dtype=float))
    side = pd.Series(np.asarray(signal_position, dtype=float))
    if len(price) != len(side) or len(price) < 2:
        raise ValueError('price and frozen signal lengths must match')
    if not np.isfinite(price).all() or not (price > 0).all():
        raise ValueError('positive finite prices required')
    if not side.isin([-1., 0., 1.]).all():
        raise ValueError('original signal must be -1/0/+1')
    x = np.log(price)
    low = {p: pd.Series(butter_lowpass(x.to_numpy(), p, 1)) for p in (12, 48, 240)}
    work = low[12]-low[48]
    fast = x-low[12]
    sigma = x.diff().rolling(48).std(ddof=0)
    amplitude = work.rolling(48).std(ddof=0)
    slow_move = low[240].diff(48)
    flips = ((side != side.shift()) & (side != 0) & (side.shift() != 0)).astype(float)
    flips.iloc[0] = np.nan
    out = pd.DataFrame({
        'work_efficiency_48': _ratio(low[12].diff(48).abs(), low[12].diff().abs().rolling(48).sum()),
        'threshold_work_amplitude_48': _ratio(sigma, amplitude),
        'fast_work_velocity_48': np.sqrt(_ratio(fast.diff().pow(2).rolling(48).mean(), work.diff().pow(2).rolling(48).mean())),
        'slow_opposition_strength_48': _ratio((-side*slow_move).clip(lower=0), amplitude),
        'slow_directional_efficiency_48': _ratio(slow_move.abs(), low[240].diff().abs().rolling(48).sum()),
        'reversal_count_48': flips.rolling(48).sum(),
        'work_slow_direction_agreement': np.sign(low[12].diff(12))*np.sign(slow_move),
        'work_travel_threshold_12': _ratio(low[12].diff().abs().rolling(12).sum(), 2*sigma),
    })
    out.loc[side == 0, 'slow_opposition_strength_48'] = np.nan
    return out.loc[:, FEATURES]
