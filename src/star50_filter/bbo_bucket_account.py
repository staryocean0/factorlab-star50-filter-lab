"""Fixed-unit BBO accounts. No parameter or position search."""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import pandas as pd

POLICIES = ('baseline', 'small_work', 'opposed_slow', 'fast_without_progress', 'reversal_chop', 'union_four')


def calibrated_cutoffs(entries):
    d = entries.loc[entries.trading_day.between('2021-01-01','2023-12-31')]
    return {
        'eff_low': float(d.work_efficiency_48.quantile(.25)),
        'threshold_high': float(d.threshold_work_amplitude_48.quantile(.75)),
        'fast_high': float(d.fast_work_velocity_48.quantile(.75)),
        'progress_low': float(d.work_travel_threshold_12.quantile(.25)),
        'slow_coherent': float(d.slow_directional_efficiency_48.quantile(.75)),
    }


def veto_matrix(frame, cutoffs):
    c = cutoffs
    out = pd.DataFrame(index=frame.index)
    out['baseline'] = False
    out['small_work'] = (frame.work_efficiency_48 <= c['eff_low']) & (frame.threshold_work_amplitude_48 >= c['threshold_high'])
    out['opposed_slow'] = (frame.slow_opposition_strength_48 >= 1) & (frame.slow_directional_efficiency_48 >= c['slow_coherent'])
    out['fast_without_progress'] = (frame.fast_work_velocity_48 >= c['fast_high']) & (frame.work_travel_threshold_12 <= c['progress_low'])
    out['reversal_chop'] = (frame.reversal_count_48 >= 4) & (frame.work_efficiency_48 <= c['eff_low'])
    out['union_four'] = out.iloc[:,1:].any(axis=1)
    return out


@dataclass
class Book:
    t: np.ndarray
    bid: np.ndarray
    ask: np.ndarray
    bq: np.ndarray
    aq: np.ndarray
    executable: np.ndarray
    markable: np.ndarray
    until: np.ndarray | None = None
    code: str = ''
    expiry: str = ''
    strike: float = 0.
    multiplier: float = 1.
    option_type: str = ''

    def first(self, after, before, side, quantity):
        a, b = np.searchsorted(self.t, [after, before], side='left')
        if b <= a:
            return None
        px = self.ask if side == 'buy' else self.bid
        qty = self.aq if side == 'buy' else self.bq
        ok = self.executable[a:b] & (px[a:b] > 0) & (qty[a:b] >= quantity)
        ok &= (self.bid[a:b] <= self.ask[a:b]) & np.isfinite(px[a:b])
        ok &= (self.bid[a:b] > 0) & (self.ask[a:b] > 0) & (self.bq[a:b] > 0) & (self.aq[a:b] > 0)
        if self.until is not None:
            ok &= self.until[a:b] > self.t[a:b]
        indices = np.flatnonzero(ok)
        return None if not len(indices) else a+int(indices[0])


@dataclass
class Account:
    policy: str
    carrier: str
    underlying: str
    cash: float = 100000.
    holding: str | None = None
    direction: int = 0
    quantity: int = 0
    multiplier: float = 1.
    buy_day: str = ''
    buy_time: int = 0
    buy_price: float = 0.
    buy_fee: float = 0.
    last_bid: float = 0.
    last_time: int = -1
    peak: float = 100000.
    mdd: float = 0.
    max_cash_drawdown: float = 0.
    mdd_at: int = 0
    entry_signal_time: int = 0
    fees: float = 0.
    receivable: float = 0.
    holding_dividend: float = 0.
    trades: list = field(default_factory=list)
    orders: list = field(default_factory=list)
    marks: list = field(default_factory=list)
    segments: list = field(default_factory=list)
    incidents: list = field(default_factory=list)
    blocked_T1: int = 0
    unfilled: int = 0
    missing_bid_observations: int = 0
    last_bid_ns: int = 0
    expired_otm: int = 0

    @property
    def nav(self):
        return self.cash+self.receivable+self.quantity*self.multiplier*self.last_bid

    def observe(self, when, value):
        self.peak = max(self.peak,float(value))
        dd = 1-float(value)/self.peak
        if dd > self.mdd:
            self.mdd, self.mdd_at = dd, int(when)
        self.max_cash_drawdown = max(self.max_cash_drawdown,self.peak-float(value))

    def mark_to(self, books, when):
        freshly_priced = False
        if self.holding is not None:
            b = books.get(self.holding)
            if b is None:
                self.incidents.append({'time':int(when),'reason':'held_contract_book_missing','code':self.holding})
            else:
                a = int(np.searchsorted(b.t,self.last_time,side='right'))
                end = int(np.searchsorted(b.t,when,side='right'))
                valid_bid = np.isfinite(b.bid[a:end]) & (b.bid[a:end] > 0) & (b.bq[a:end] > 0)
                self.missing_bid_observations += int(np.count_nonzero(b.markable[a:end] & ~valid_bid))
                ix = np.flatnonzero(b.markable[a:end] & valid_bid)+a
                if len(ix):
                    freshly_priced = True
                    values = self.cash+self.receivable+self.quantity*self.multiplier*b.bid[ix]
                    peaks = np.maximum(self.peak,np.maximum.accumulate(values))
                    ratios = 1-values/peaks
                    k = int(np.argmax(ratios))
                    if ratios[k] > self.mdd:
                        self.mdd, self.mdd_at = float(ratios[k]),int(b.t[ix[k]])
                    self.max_cash_drawdown = max(self.max_cash_drawdown,float(np.max(peaks-values)))
                    self.segments.append({'start_ns':int(b.t[ix[0]]),'end_ns':int(b.t[ix[-1]]),
                        'code':self.holding,'quantity':self.quantity,'multiplier':self.multiplier,
                        'cash':self.cash,'receivable':self.receivable,'quote_count':len(ix),
                        'min_nav':float(values.min()),'max_nav':float(values.max()),
                        'last_nav':float(values[-1]),'max_drawdown_pct':float(ratios.max()),
                        'worst_ns':int(b.t[ix[k]])})
                    self.peak = float(peaks[-1])
                    self.last_bid = float(b.bid[ix[-1]])
                    self.last_bid_ns = int(b.t[ix[-1]])
        self.last_time = max(self.last_time,int(when))
        if self.holding is None or freshly_priced:
            self.observe(when,self.nav)

    def sell(self, books, after, before, day, reason):
        if self.holding is None:
            return after
        if self.carrier == 'spot' and self.buy_day == day:
            self.blocked_T1 += 1
            return None
        b = books.get(self.holding)
        i = None if b is None else b.first(after,before,'sell',self.quantity)
        if i is None:
            self.unfilled += 1
            return None
        t,price = int(b.t[i]),float(b.bid[i])
        self.mark_to(books,t)
        gross = self.quantity*self.multiplier*price
        fee = gross*.0002 if self.carrier == 'spot' else self.quantity*4.5
        self.cash += gross-fee
        self.fees += fee
        pnl = self.quantity*self.multiplier*(price-self.buy_price)-self.buy_fee-fee+self.holding_dividend
        self.trades.append({'code':self.holding,'direction':self.direction,'entry_ns':self.buy_time,
            'exit_ns':t,'entry_signal_ns':self.entry_signal_time,'quantity':self.quantity,
            'multiplier':self.multiplier,'entry_price':self.buy_price,'exit_price':price,
            'entry_fee':self.buy_fee,'exit_fee':fee,'dividend':self.holding_dividend,
            'net_pnl':pnl,'reason':reason})
        self.orders.append({'time_ns':t,'side':'sell','code':self.holding,'quantity':self.quantity,
                            'price':price,'fee':fee,'cash_after':self.cash,'reason':reason})
        self.holding,self.direction,self.quantity = None,0,0
        self.last_bid,self.holding_dividend = 0.,0.
        self.observe(t,self.nav)
        return t+1

    def step(self, books, spot, target, after, before, day, local_time, signal_time):
        self.mark_to(books,after-1)
        desired = max(0,int(target)) if self.carrier == 'spot' else int(target)
        expired = (self.holding is not None and self.carrier == 'option'
                   and books.get(self.holding) is not None
                   and books[self.holding].expiry <= day and local_time >= '14:55')
        if self.holding is not None and (desired != self.direction or expired):
            result = self.sell(books,after,before,day,'expiry_roll' if expired else 'target_changed')
            if result is None:
                return
            after = result
        if self.holding is not None or desired == 0 or after >= before:
            return
        if self.carrier == 'spot':
            b,quantity = spot,10000
        else:
            # The underlying coordinate becomes known at this actual observation,
            # not at an earlier index decision. Selection does not use fill PnL.
            s = spot.first(after,before,'buy',1)
            if s is None or spot.bid[s] <= 0:
                self.unfilled += 1
                return
            selection = int(spot.t[s])
            reference = float((spot.bid[s]+spot.ask[s])/2)
            kind = 'C' if desired > 0 else 'P'
            eligible = [x for x in books.values() if x.option_type == kind and x.expiry >= day
                        and len(x.t) and x.t[0] <= selection
                        and not (x.expiry == day and local_time >= '14:55')]
            if not eligible:
                self.unfilled += 1
                return
            b = min(eligible,key=lambda x:(x.expiry,abs(x.strike-reference),x.code))
            after,quantity = max(after,selection+1),1
        i = b.first(after,before,'buy',quantity)
        if i is None:
            self.unfilled += 1
            return
        price,t = float(b.ask[i]),int(b.t[i])
        gross = quantity*b.multiplier*price
        fee = gross*.0002 if self.carrier == 'spot' else quantity*4.5
        if gross+fee > self.cash:
            self.unfilled += 1
            return
        self.cash -= gross+fee
        self.fees += fee
        self.holding,self.direction,self.quantity,self.multiplier = b.code,desired,quantity,b.multiplier
        self.buy_day,self.buy_time,self.buy_price,self.buy_fee = day,t,price,fee
        self.entry_signal_time = int(signal_time)
        self.last_bid,self.last_time = float(b.bid[i]),t
        self.last_bid_ns = t
        self.orders.append({'time_ns':t,'side':'buy','code':b.code,'quantity':quantity,'price':price,
                            'fee':fee,'cash_after':self.cash,'reason':'admitted_target'})
        self.observe(t,self.nav)

    def end_day(self, books, spot, day, when):
        if self.carrier != 'option' or self.holding is None:
            return
        b = books.get(self.holding)
        if b is None or b.expiry > day:
            return
        ix = np.flatnonzero((spot.t <= when) & spot.markable & (spot.bid > 0) & (spot.ask >= spot.bid))
        if not len(ix):
            self.incidents.append({'time':int(when),'reason':'expiry_underlying_price_unavailable','code':self.holding})
            return
        i = int(ix[-1])
        otm = (b.option_type == 'C' and spot.ask[i] <= b.strike) or (b.option_type == 'P' and spot.bid[i] >= b.strike)
        if not otm:
            self.incidents.append({'time':int(when),'reason':'unresolved_ITM_expiry_delivery','code':self.holding})
            return
        self.mark_to(books,when)
        pnl = -self.quantity*self.multiplier*self.buy_price-self.buy_fee
        self.trades.append({'code':self.holding,'direction':self.direction,'entry_ns':self.buy_time,
            'exit_ns':int(when),'entry_signal_ns':self.entry_signal_time,'quantity':self.quantity,
            'multiplier':self.multiplier,'entry_price':self.buy_price,'exit_price':0.,
            'entry_fee':self.buy_fee,'exit_fee':0.,'dividend':0.,'net_pnl':pnl,
            'reason':'expired_OTM_not_a_fill','expiry_underlying_bid':float(spot.bid[i]),
            'expiry_underlying_ask':float(spot.ask[i]),'expiry_strike':b.strike})
        self.orders.append({'time_ns':int(when),'side':'expiry','code':self.holding,'quantity':self.quantity,
            'price':0.,'fee':0.,'cash_after':self.cash,'reason':'confirmed_OTM_right_expired_not_a_trade'})
        self.expired_otm += 1
        self.holding,self.direction,self.quantity = None,0,0
        self.last_bid,self.holding_dividend = 0.,0.
        self.observe(when,self.nav)

    def summary(self):
        pnl = np.asarray([t['net_pnl'] for t in self.trades])
        returns = self.nav/100000-1
        return {'policy':self.policy,'carrier':self.carrier,'underlying':self.underlying,
            'initial_cash':100000.,'terminal_nav':self.nav,'cagr_2025':returns,
            'net_pnl':self.nav-100000,'max_drawdown':self.mdd,'max_cash_drawdown':self.max_cash_drawdown,
            'mdd_at_ns':self.mdd_at,'completed_trades':len(pnl),
            'mean_net_trade':float(pnl.mean()) if len(pnl) else None,
            'win_rate':float((pnl>0).mean()) if len(pnl) else None,
            'fees':self.fees,'terminal_holding':self.holding,'terminal_quantity':self.quantity,
            'blocked_T1_attempts':self.blocked_T1,'unfilled_attempts':self.unfilled,
            'coverage_incidents':len(self.incidents),
            'missing_bid_observations':self.missing_bid_observations,
            'expired_otm':self.expired_otm,
            'calmar':returns/self.mdd if self.mdd else None}
