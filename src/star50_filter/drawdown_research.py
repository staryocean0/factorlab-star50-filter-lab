"""Frozen STAR50 diagnostic states and complete research accounts.

All signal features use completed bars. The exported available_at metadata is
audited separately: mathematical causality is not proof of live availability.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import signal
from .filters import butter_lowpass, hysteresis_positions


def lag(x, n=1, fill=np.nan):
    x = np.asarray(x, dtype=float)
    z = np.full(len(x), fill, dtype=float)
    if n == 0:
        return x.copy()
    z[n:] = x[:-n]
    return z


def causal_states(df, session_bars=48):
    x = np.log(df['close'].to_numpy(dtype=float))
    w = butter_lowpass(x, 12, 1)
    sigma = pd.Series(x).diff().rolling(session_bars).std(ddof=0).to_numpy()
    s = hysteresis_positions(w, sigma)
    slow = butter_lowpass(x, 20 * session_bars, 1)
    band = w - butter_lowpass(x, session_bars, 1)
    amp = pd.Series(band).rolling(session_bars).std(ddof=0).to_numpy()
    drift = slow - lag(slow, session_bars)
    path = pd.Series(slow).diff().abs().rolling(session_bars).sum().to_numpy()
    stable = np.divide(abs(drift), path, out=np.zeros(len(x)), where=path > 1e-15)
    wp = pd.Series(w).diff().abs().rolling(session_bars).sum().to_numpy()
    efficiency = np.divide(abs(w-lag(w,session_bars)), wp, out=np.zeros(len(x)), where=wp > 1e-15)
    flips = ((s * lag(s,fill=0)) < 0).astype(float)
    turns = pd.Series(flips).rolling(session_bars).sum().to_numpy()
    slow_conflict = (stable >= .8) & (abs(drift) >= amp) & (s * drift < 0)
    chop = (efficiency <= .2) & (turns >= 4)
    return pd.DataFrame(dict(signal=s, sigma=sigma, work_lowpass=w,
        slow=slow, work_band=band, work_amplitude=amp, slow_displacement=drift,
        slow_stability=stable, work_efficiency=efficiency, reversals=turns,
        slow_conflict=slow_conflict, chop=chop))


def targets(states):
    s = states['signal'].to_numpy()
    return {'baseline':s, 'constant_075':.75*s, 'constant_050':.5*s,
        'slow_conflict_half':s*np.where(states.slow_conflict,.5,1.),
        'chop_half':s*np.where(states.chop,.5,1.)}


def account(df, target, cost_bps=0., mode='log_index', terminal_liquidation=True):
    """Mark at opens. Costs at actual open; first scored open starts flat.

    q[i] earns open[i-1] -> open[i]. New target from close[i-1] is
    executed at open[i], and hence is q[i+1]. Last open liquidates.
    """
    op = df.open.to_numpy(dtype=float)
    day = df.trading_day.astype(str).str[:10].to_numpy()
    dev = (day >= '2021-01-01') & (day <= '2025-12-31')
    where = np.flatnonzero(dev)
    if not len(where):
        raise ValueError('No scored development rows')
    start, end = where[0], where[-1]
    q = lag(target,2,fill=0.)
    q[:start+1]=0.
    q[end+1:]=0.
    r = np.zeros(len(op)); r[1:] = np.log(op[1:]/op[:-1])
    turnover = np.zeros(len(op))
    turnover[start:end] = abs(q[start+1:end+1] - q[start:end])
    turnover[end] = abs(q[end]) if terminal_liquidation else abs(target[end-1]-q[end])
    fee = turnover * cost_bps / 10000.
    if np.any(fee>=1):
        raise ValueError('bankrupt cost')
    if mode=='log_index':
        gross = q*r
    elif mode=='simple_equity':
        simple = q*np.expm1(r)
        if np.any(simple<=-1):
            raise ValueError('bankrupt gross equity')
        gross = np.log1p(simple)
    else:
        raise ValueError(mode)
    log_fee = -np.log1p(-fee)
    net = gross - log_fee
    return pd.DataFrame({'trading_day':day,'timestamp':df.timestamp.to_numpy(),
        'position':q,'market_log_return':r,'gross_log_pnl':gross,
        'turnover':turnover,'cost_log':log_fee,'net_log_pnl':net,
        'is_development':dev})


def open_component_attribution(df, position, slow_sessions=20, session_bars=48):
    """Exact log-index PnL attribution on actual mark endpoints.

    This decomposition is nonorthogonal, filter-dependent, and descriptive.
    Filtering OPEN marks is only a PnL identity, never a signal input.
    """
    x=np.log(df.open.to_numpy(dtype=float)); z=x-x[0]
    def lp(p):
        return signal.sosfilt(signal.butter(1,1./p,fs=1.,output='sos'),z)
    slow=lp(slow_sessions*session_bars); work=lp(12)-slow; residual=z-lp(12)
    q=np.asarray(position)
    delta=lambda a: np.diff(a,prepend=a[0])
    a=pd.DataFrame({'slow_log_pnl':q*delta(slow),
        'work_log_pnl':q*delta(work),'residual_log_pnl':q*delta(residual)})
    np.testing.assert_allclose(a.sum(axis=1),q*delta(x),atol=1e-13,rtol=1e-11)
    return a


def exact_gap_attribution(df, position):
    """Split open-to-open PnL into prior open-close and close-next-open.

    day_gap marks only previous-session close to current-session open;
    remaining gaps are intraday bar-boundary gaps, not 'overnight'.
    """
    op=df.open.to_numpy(dtype=float); cl=df.close.to_numpy(dtype=float)
    q=np.asarray(position); n=len(op)
    inside=np.zeros(n); gap=np.zeros(n)
    inside[1:]=q[1:]*np.log(cl[:-1]/op[:-1])
    gap[1:]=q[1:]*np.log(op[1:]/cl[:-1])
    day=df.trading_day.astype(str).to_numpy()
    boundary=np.r_[False,day[1:]!=day[:-1]]
    return pd.DataFrame({'within_previous_bar_log_pnl':inside,
        'overnight_gap_log_pnl':np.where(boundary,gap,0.),
        'intraday_gap_log_pnl':np.where(boundary,0.,gap)})
