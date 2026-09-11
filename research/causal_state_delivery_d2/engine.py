"""D2 chronological risk-attribute delivery; no future labels, fit, or actions."""
from __future__ import annotations
from bisect import bisect_right
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import hashlib
import json
import math
from statistics import pstdev
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Asia/Shanghai')
SYMBOLS = ('000688.SH', '000852.SH')
STATES = ('NORMAL', 'UNSAFE', 'RECOVERING')
RISK = ('UNSAFE', 'RECOVERING')
V9 = 'ae2a7e095df58692ef9df0dfee5856cac727ca44'
V19 = 'ee2fce299d5ee21abf1ab2c2c5183bac101ae822'
V16 = '1f88966cf5dd3fb102f0d75746d5d00434555647'

def aware(t):
    if not isinstance(t, datetime) or t.utcoffset() is None:
        raise ValueError('timezone-aware timestamp required')
    return t.astimezone(TZ)

def next_bar(t):
    t = aware(t)
    if (t.hour, t.minute) == (11, 30):
        return t.replace(hour=13, minute=5)
    return t + timedelta(minutes=5)

def active(t):
    t = aware(t); hm = (t.hour, t.minute, t.second, t.microsecond)
    return (9,30,0,0) <= hm <= (11,30,0,0) or (13,0,0,0) <= hm <= (15,0,0,0)

def bucket(age):
    return 'LT15' if age <= 2 else 'M15_25' if age <= 5 else 'M30_40' if age <= 8 else 'GE45'

def transition(prev, ratio, shock):
    if shock: return 'UNSAFE'
    if prev in RISK:
        if ratio is None: return prev
        if ratio >= 1.5: return 'UNSAFE'
        if ratio > 1.1: return 'RECOVERING'
    return 'NORMAL'

def transition_kind(prev, state):
    if state is None: return 'UNAVAILABLE'
    if prev == state: return 'HOLD_' + state
    if prev == 'NORMAL' and state == 'UNSAFE': return 'SWITCH_ON'
    if prev == 'RECOVERING' and state == 'UNSAFE': return 'REESCALATE'
    if state == 'NORMAL': return 'EXIT_FROM_' + prev
    return prev + '_TO_' + state

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False,
                      default=lambda x: x.isoformat() if isinstance(x, datetime) else str(x))

@dataclass(frozen=True)
class Snapshot:
    symbol: str
    bar_end: datetime
    event_type: str
    decision_time: datetime
    published_at: datetime
    valid_until: datetime
    observation_time: datetime | None
    observation_known_at: datetime | None
    state: str | None
    previous_confirmed_state: str | None
    partial_state: str | None
    state_basis: str
    availability_reason: str
    transition: str
    exit_pending: bool
    shock: bool | None
    recent_shock_age_bars: int | None
    recovery_probabilities: tuple[float, float, float] | None
    recovery_reason: str
    vol_ratio: float | None
    shock_intensity: float | None
    schema: str = 'causal_kline_delivery_d2_v1'
    timing_basis: str = 'owner_realtime_assumption'
    age_clock: str = '5m_bar_steps_within_trading_day'
    probability_target_clock: str = 'frozen_V16_horizon_labels_at_reference_bar_end'
    frozen_v9_blob: str = V9
    frozen_v19_blob: str = V19
    frozen_v16_blob: str = V16
    production_authority: bool = False

    @property
    def event_id(self):
        return f'{self.symbol}|{self.bar_end.isoformat()}|{self.event_type}'

    def record(self):
        d = asdict(self)
        d['event_id'] = self.event_id
        d['bucket_key'] = 'UNAVAILABLE' if self.state is None else self.state + '|' + self.state_basis
        return d

class Kernel:
    """Only completed-close calls mutate the confirmed state/return/age buffers."""
    def __init__(self, symbol, surface):
        if symbol not in SYMBOLS: raise ValueError('unsupported symbol')
        self.symbol, self.surface = symbol, dict(surface)
        self.returns = deque(maxlen=48)
        self.day = None; self.state = 'NORMAL'; self.prev_close = None
        self.previous_end = None; self.previous_known = None
        self.position = -1; self.last_shock = None

    def prepare(self, end):
        end = aware(end)
        if end.second or end.microsecond or end.minute % 5:
            raise ValueError('not a 5m close')
        hm = (end.hour, end.minute)
        if not ((9,35) <= hm <= (11,30) or (13,5) <= hm <= (15,0)):
            raise ValueError('outside declared bar grid')
        if not 2020 <= end.year <= 2025: raise ValueError('outside data boundary')
        if self.day is not None and end.date() < self.day: raise ValueError('out-of-order day')
        if end.date() != self.day:
            self.day = end.date(); self.state = 'NORMAL'; self.prev_close = None
            self.previous_end = None; self.previous_known = None
            self.position = -1; self.last_shock = None
        if self.previous_end is not None and end != next_bar(self.previous_end):
            raise ValueError('missing/out-of-order close; no gap imputation')
        return end

    def measures(self, price):
        if price is None or self.prev_close is None or len(self.returns) < 48:
            return None, None, None
        if not math.isfinite(price) or price <= 0: raise ValueError('invalid price')
        bg = pstdev(self.returns)
        if bg <= 0: return None, None, None
        ret = math.log(price) - math.log(self.prev_close)
        ratio = pstdev(list(self.returns)[-11:] + [ret]) / bg
        intensity = abs(ret) / bg
        return ratio, intensity, intensity >= 3.0

    def probabilities(self, state, shock, age, kind, available):
        if not available: return None, 'missing_reference_or_checkpoint'
        if shock: return None, 'fresh_partial_shock' if kind == 'E15' else 'fresh_final_shock'
        if state not in RISK: return None, 'provisional_normal' if kind == 'E15' else 'confirmed_normal'
        if age is None or age <= 0: return None, 'no_prior_finalized_shock'
        return tuple(self.surface[(state, bucket(age))]), 'scored'

    def e15(self, *, bar_end, price, observation_time, observation_known_at=None, published_at=None):
        end = self.prepare(bar_end); decision = end - timedelta(seconds=15)
        pub = aware(published_at) if published_at is not None else decision
        if pub < decision: raise ValueError('publication backdated')
        obs = aware(observation_time) if observation_time is not None else None
        known = aware(observation_known_at) if observation_known_at is not None else obs
        if obs is not None and known is not None and known < obs: raise ValueError('known before observed')
        ratio, intensity, shock = self.measures(price)
        reason = 'AVAILABLE'
        if self.prev_close is None or len(self.returns) < 48 or self.previous_known is None:
            reason = 'REFERENCE_UNAVAILABLE'
        elif self.previous_known > decision: reason = 'REFERENCE_NOT_KNOWN'
        elif obs is None or known is None or price is None: reason = 'CHECKPOINT_UNAVAILABLE'
        elif obs > decision or known > decision: reason = 'INPUT_NOT_KNOWN_BY_DECISION'
        elif obs < end - timedelta(minutes=5): reason = 'OBSERVATION_OUTSIDE_CURRENT_BAR'
        elif ratio is None: reason = 'REFERENCE_UNAVAILABLE'
        good = reason == 'AVAILABLE'; prev = self.state
        partial = transition(prev, ratio, shock) if good else None
        state = (partial if partial in RISK else prev if prev in RISK else 'NORMAL') if good else None
        pending = good and partial == 'NORMAL' and prev in RISK
        basis = ('PRIOR_CONFIRMED_EXIT_PENDING' if pending else 'E15_PROVISIONAL') if good else 'UNAVAILABLE'
        age = self.position + 1 - self.last_shock if self.last_shock is not None else None
        prob, pr = self.probabilities(partial, shock, age, 'E15', good)
        return Snapshot(self.symbol,end,'E15',decision,pub,end,obs,known,state,prev if good else None,
                        partial,basis,reason,transition_kind(prev,state),pending,shock if good else None,
                        age if good else None,prob,pr,ratio if good else None,intensity if good else None)

    def close(self, *, bar_end, price, known_at=None, published_at=None):
        end = self.prepare(bar_end); known = aware(known_at) if known_at is not None else end
        pub = aware(published_at) if published_at is not None else known
        if known < end or pub < known: raise ValueError('close backdated')
        if not math.isfinite(price) or price <= 0: raise ValueError('invalid close')
        prev = self.state; ratio, intensity, shock = self.measures(price)
        good = ratio is not None; self.position += 1
        self.state = transition(prev, ratio, bool(shock))
        if shock: self.last_shock = self.position
        age = self.position-self.last_shock if self.last_shock is not None else None
        prob, pr = self.probabilities(self.state, shock, age, 'CLOSE', good)
        if self.prev_close is not None: self.returns.append(math.log(price)-math.log(self.prev_close))
        self.prev_close = price; self.previous_end = end; self.previous_known = known
        state = self.state if good else None
        expiry = next_bar(end) - timedelta(seconds=15)
        if (end.hour,end.minute)==(15,0): expiry=end+timedelta(microseconds=1)
        return Snapshot(self.symbol,end,'CLOSE',end,pub,expiry,end,known,state,prev if good else None,None,
                        'CLOSE_CONFIRMED' if good else 'UNAVAILABLE',
                        'AVAILABLE' if good else 'REFERENCE_UNAVAILABLE',transition_kind(prev,state),False,
                        bool(shock) if good else None,age if good else None,prob,pr,ratio,intensity)

class Ledger:
    def __init__(self):
        self._events=[]; self._ids={}; self._times={s:[] for s in SYMBOLS}; self._by_symbol={s:[] for s in SYMBOLS}
        self._head='0'*64
    @property
    def events(self): return tuple(self._events)
    @property
    def digest(self): return self._head
    def append(self, event):
        digest=hashlib.sha256(canonical(event.record()).encode()).hexdigest()
        if event.event_id in self._ids:
            if self._ids[event.event_id] != digest: raise ValueError('conflicting duplicate')
            return False
        if self._events and event.published_at < self._events[-1].published_at:
            raise ValueError('out-of-order publication')
        self._head=hashlib.sha256((self._head+digest).encode()).hexdigest()
        self._ids[event.event_id]=digest; self._events.append(event)
        self._times[event.symbol].append(event.published_at); self._by_symbol[event.symbol].append(event)
        return True
    def as_of(self, symbol, when):
        when=aware(when)
        if symbol not in SYMBOLS: raise ValueError('unsupported symbol')
        if not active(when): return None
        i=bisect_right(self._times[symbol],when)-1
        if i < 0: return None
        e=self._by_symbol[symbol][i]
        return e if e.bar_end.date()==when.date() and when < e.valid_until else None
    def read(self, symbol, when):
        """Public consumer result: missing means UNAVAILABLE, never safe/NORMAL."""
        event=self.as_of(symbol,when)
        if event is None:
            return {'state':None,'bucket_key':'UNAVAILABLE','availability_reason':
                    'SESSION_CLOSED' if not active(when) else 'NO_CURRENT_PUBLISHED_SNAPSHOT',
                    'production_authority':False}
        d=event.record()
        d['observation_age_seconds']=(when-event.observation_time).total_seconds() if event.observation_time else None
        return d
