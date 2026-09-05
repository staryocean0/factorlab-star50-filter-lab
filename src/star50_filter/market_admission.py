"""Evidence and inventory primitives. Passing these checks is not proof of fills.

No signal calculation, return calculation, local bar aggregation, or production
adapter belongs here. External evidence still requires a provenance review.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path

import pandas as pd


def instant(value):
    """Reject naive timestamps; never repair the legacy wall-clock-Z convention."""
    t = pd.Timestamp(value)
    if pd.isna(t) or t.tzinfo is None:
        raise ValueError('Explicit timezone required')
    return t.tz_convert('UTC')


def check_versions(rows, basis):
    if basis not in ('source_sent_at', 'received_at') or not rows:
        raise ValueError('Nonempty version history and explicit clock basis required')
    seen, groups = set(), {}
    for row in rows:
        if row['symbol'] != '000688.SH' or not math.isfinite(row['close']) or row['close'] <= 0:
            raise ValueError('Require a positive STAR50 observed signal value')
        end = instant(row['bar_end'])
        known = instant(row[basis])
        if end.tz_convert('Asia/Shanghai').year > 2025:
            raise ValueError('Post-2025 market evidence excluded from this audit')
        if known < end:
            raise ValueError('Completed bar cannot be known before its end')
        if row.get('source_sent_at') is not None:
            sent = instant(row['source_sent_at'])
            if sent < end or (row.get('received_at') is not None and
                              instant(row['received_at']) < sent):
                raise ValueError('Inconsistent source/receiver clocks')
        if row.get('price_view') != 'raw' or row.get('source_kind') != 'observed':
            raise ValueError('Require observed raw versions, not repaired/final-only bars')
        key = (row['symbol'], end)
        identity = (*key, row['version_id'])
        if not row['version_id'] or identity in seen:
            raise ValueError('Duplicate or empty version identity')
        if type(row['is_first']) is not bool:
            raise ValueError('is_first must be a boolean')
        seen.add(identity)
        groups.setdefault(key, []).append((known, row))
    for values in groups.values():
        values.sort(key=lambda x: x[0])
        if (sum(r['is_first'] for _, r in values) != 1 or
                not values[0][1]['is_first'] or
                len({t for t, _ in values}) != len(values)):
            raise ValueError('Missing first version or ambiguous revision ordering')


def asof_prefix(rows, decision_at, basis, expected_keys):
    """Return a complete feature prefix at decision time, or fail closed.

    expected_keys is the externally declared warmup-through-decision bar menu.
    Recompute recursive state from this prefix when a historical bar is revised;
    never patch a cached final-history filter state with only the latest close.
    """
    check_versions(rows, basis)
    decision = instant(decision_at)
    keys = [(s, instant(t)) for s, t in expected_keys]
    expected = set(keys)
    if len(expected) != len(keys):
        raise ValueError('Duplicate required prefix key')
    if not expected or any(t > decision for _, t in expected):
        raise ValueError('Invalid required prefix')
    latest = {}
    for row in sorted(rows, key=lambda r: instant(r[basis])):
        key = (row['symbol'], instant(row['bar_end']))
        if key in expected and instant(row[basis]) <= decision:
            latest[key] = row
    missing = expected - latest.keys()
    if missing:
        raise ValueError(f'Unavailable recursive prefix: {len(missing)} bars')
    return [latest[k] for k in sorted(expected, key=lambda k: (k[1], k[0]))]


def inspect_bundle(folder):
    """Validate delivered files and version schema; do not assert historical truth."""
    root = Path(folder).resolve()
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest['schema'] != 'star50_external_market_bundle@1':
        raise ValueError('Unknown bundle schema')
    if manifest['revision_policy'] != 'append_only_first_and_corrections':
        raise ValueError('Final-only history is insufficient')
    files = manifest['files']
    for name, expected in files.items():
        p = (root / name).resolve()
        if not p.is_relative_to(root) or p == root:
            raise ValueError('Evidence path escapes bundle')
        if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise ValueError('Evidence hash mismatch: ' + name)
    versions = manifest['bar_versions_file']
    if versions not in files:
        raise ValueError('Version carrier not hash-bound')
    rows = [json.loads(x) for x in (root / versions).read_text().splitlines() if x]
    basis = manifest['clock_basis']
    check_versions(rows, basis)
    for row in rows:
        ref = row['evidence_ref']
        if ref == versions or ref not in files or row['evidence_sha256'] != files[ref]:
            raise ValueError('Missing independent raw evidence binding')
    for field in ('generator_evidence_file', 'clock_semantics_file', 'coverage_file'):
        if manifest[field] not in files:
            raise ValueError('Missing provenance or coverage document')
    return {'format_integrity_pass': True, 'rows': len(rows),
            'clock_basis': basis, 'evidence_files': len(files),
            'historical_truth_requires_review': True,
            'source_send_is_not_receiver_time': True,
            'intraday_strategy_admitted': False,
            'production_authority': False}


def visible_quote(quotes, symbol, arrival_at, max_age_seconds):
    """Latest received quote at arrival; quote visibility is not a fill model."""
    if symbol not in ('588000.SH', '588080.SH'):
        raise ValueError('This cash-ETF contract does not accept index/other prices')
    if max_age_seconds < 0:
        raise ValueError('Negative quote age')
    arrival = instant(arrival_at)
    eligible = [q for q in quotes if q['symbol'] == symbol and
                instant(q['received_at']) <= arrival]
    if not eligible:
        return None
    times = [instant(q['received_at']) for q in eligible]
    if len(set(times)) != len(times):
        raise ValueError('Ambiguous quote sequence; supply ordered receive timestamps')
    q = max(eligible, key=lambda q: instant(q['received_at']))
    event = instant(q['event_at'])
    if event.tz_convert('Asia/Shanghai').year > 2025:
        raise ValueError('Post-2025 market evidence excluded from this audit')
    if event > instant(q['received_at']):
        raise ValueError('Quote clock order invalid')
    if q['price_view'] != 'raw':
        raise ValueError('Adjusted prices cannot price fills')
    if (not all(math.isfinite(q[k]) for k in ('bid', 'ask', 'bid_size', 'ask_size')) or
            q['phase'] != 'continuous' or (arrival - event).total_seconds() > max_age_seconds or
            not 0 < q['bid'] <= q['ask'] or q['bid_size'] <= 0 or q['ask_size'] <= 0):
        return None
    return dict(q, actual_fill_proven=False)


@dataclass
class CashT1Inventory:
    """Optimistic unit feasibility only: no funding, price, fee or PnL engine."""
    trading_day: str | None = None
    settled: int = 0
    locked: int = 0
    desired: int = 0

    def __post_init__(self):
        for x in (self.settled, self.locked, self.desired):
            if type(x) is not int or x < 0:
                raise ValueError('Nonnegative integer inventory required')

    @property
    def total(self):
        return self.settled + self.locked

    def advance(self, trading_day):
        date.fromisoformat(trading_day)
        if self.trading_day is not None and trading_day < self.trading_day:
            raise ValueError('Nonchronological trading day')
        changed = self.trading_day != trading_day
        if changed:
            self.settled += self.locked
            self.locked = 0
            self.trading_day = trading_day
        return changed

    def request(self, signed_units):
        if self.trading_day is None or type(signed_units) is not int:
            raise ValueError('Advance calendar first; integer targets required')
        self.desired = max(signed_units, 0)
        before = self.total
        buy = max(0, self.desired - before)
        sell_need = max(0, before - self.desired)
        sell = min(sell_need, self.settled)
        self.settled -= sell
        self.locked += buy
        return {'signed_target': signed_units, 'cash_target': self.desired,
                'before': before, 'after': self.total, 'buy': buy, 'sell': sell,
                'blocked_sell': sell_need - sell,
                'unmapped_short_target': max(0, -signed_units),
                'settled': self.settled, 'locked': self.locked}

    def snapshot(self):
        return asdict(self)
