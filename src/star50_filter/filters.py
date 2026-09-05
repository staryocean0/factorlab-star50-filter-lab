"""Causal Butterworth helpers for STAR50 filter research."""
from __future__ import annotations
import numpy as np
from scipy import signal

def butter_lowpass(log_close: np.ndarray, period_bars: int, order: int = 1) -> np.ndarray:
    if period_bars < 3:
        raise ValueError("period_bars must be >= 3")
    wn = 1.0 / float(period_bars)
    if not (0.0 < wn < 0.5):
        raise ValueError("cutoff must be below Nyquist")
    sos = signal.butter(order, wn, btype="lowpass", fs=1.0, output="sos")
    y = signal.sosfilt(sos, log_close - log_close[0])
    warm = period_bars * max(order, 1)
    y[:warm] = np.nan
    return y

def butter_bandpass(log_close: np.ndarray, short_bars: int, long_bars: int, order: int = 1) -> np.ndarray:
    hi = 1.0 / float(short_bars)
    lo = 1.0 / float(long_bars)
    if not (0.0 < lo < hi < 0.5):
        raise ValueError("invalid band")
    sos = signal.butter(order, [lo, hi], btype="bandpass", fs=1.0, output="sos")
    y = signal.sosfilt(sos, log_close - log_close[0])
    y[:long_bars] = np.nan
    return y

def hysteresis_positions(y: np.ndarray, threshold) -> np.ndarray:
    n = len(y)
    pos = np.zeros(n)
    cur = 0.0
    extreme = np.nan
    t_arr = threshold if isinstance(threshold, np.ndarray) else None
    for i in range(1, n):
        if not np.isfinite(y[i]) or not np.isfinite(y[i - 1]):
            pos[i] = cur
            continue
        sl = np.sign(y[i] - y[i - 1])
        t = float(t_arr[i]) if t_arr is not None else float(threshold)
        if not np.isfinite(t) or t < 0:
            t = 0.0
        if cur == 0.0:
            if sl != 0:
                cur = sl
                extreme = y[i]
            pos[i] = cur
            continue
        if cur > 0:
            extreme = y[i] if not np.isfinite(extreme) else max(extreme, y[i])
        else:
            extreme = y[i] if not np.isfinite(extreme) else min(extreme, y[i])
        if sl != 0 and sl != cur and np.isfinite(extreme) and abs(y[i] - extreme) >= t:
            cur = sl
            extreme = y[i]
        pos[i] = cur
    return pos
