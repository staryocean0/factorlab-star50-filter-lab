"""Artificial examples test clock leakage and inventory identities, not returns."""
import hashlib
import json
import pytest
from star50_filter.market_admission import (
    asof_prefix, check_versions, instant, inspect_bundle, visible_quote, CashT1Inventory)


def version(**kw):
    return dict(symbol='000688.SH', bar_end='2021-01-04T09:35:00+08:00',
                source_sent_at='2021-01-04T09:35:01+08:00',
                received_at='2021-01-04T09:35:02+08:00',
                version_id='first', is_first=True, source_kind='observed',
                price_view='raw', close=100., **kw)


def test_late_revision_never_rewrites_past_decision():
    first = version()
    revised = dict(first, version_id='correction', is_first=False, close=90.,
                   source_sent_at='2021-01-04T15:30:00+08:00',
                   received_at='2021-01-04T15:30:01+08:00')
    keys = [(first['symbol'], first['bar_end'])]
    assert asof_prefix([revised, first], '2021-01-04T10:00+08:00', 'received_at', keys)[0]['close'] == 100
    assert asof_prefix([first, revised], '2021-01-04T16:00+08:00', 'received_at', keys)[0]['close'] == 90
    with pytest.raises(ValueError):
        asof_prefix([revised], '2021-01-04T16:00+08:00', 'received_at', keys)


def test_missing_recursive_warmup_bar_blocks_prefix():
    row = version()
    keys = [(row['symbol'], row['bar_end']), (row['symbol'], '2021-01-04T09:30+08:00')]
    with pytest.raises(ValueError, match='Unavailable recursive prefix'):
        asof_prefix([row], '2021-01-04T10:00+08:00', 'received_at', keys)


def test_sender_clock_cannot_substitute_for_receiver():
    row = version()
    keys = [(row['symbol'], row['bar_end'])]
    decision = '2021-01-04T09:35:01.5+08:00'
    assert asof_prefix([row], decision, 'source_sent_at', keys)
    with pytest.raises(ValueError):
        asof_prefix([row], decision, 'received_at', keys)
    with pytest.raises(ValueError):
        instant('2021-01-04T09:35:00')
    assert instant('2021-01-04T09:35:00Z') != instant('2021-01-04T09:35:00+08:00')


@pytest.mark.parametrize('change', [
    {'received_at': '2021-01-04T09:34:00+08:00'},
    {'source_kind': 'synthetic'}, {'price_view': 'qfq'},
    {'bar_end': '2026-01-05T09:35:00+08:00'}, {'is_first': 'true'}])
def test_unproven_or_invalid_version_rejected(change):
    with pytest.raises(ValueError):
        check_versions([dict(version(), **change)], 'received_at')


def test_inventory_lock_and_next_trading_day_settlement():
    s = CashT1Inventory()
    s.advance('2021-12-31')
    assert s.request(2)['buy'] == 2
    assert s.request(-2)['blocked_sell'] == 2
    assert s.total == s.locked == 2
    s.advance('2022-01-04')
    assert s.request(-2)['sell'] == 2
    assert s.total == 0
    with pytest.raises(ValueError):
        s.advance('2021-12-31')


def test_sell_old_inventory_buyback_remains_locked_and_latest_target_wins():
    s = CashT1Inventory(settled=2)
    s.advance('2021-01-04')
    assert s.request(0)['sell'] == 2
    s.request(2)
    assert s.request(1)['blocked_sell'] == 1
    s.request(2)  # Supersedes old pending sale.
    s.advance('2021-01-05')
    assert s.request(2)['sell'] == 0
    assert s.total == s.settled == 2


def test_quote_visibility_raw_product_and_no_fallback_from_halt():
    q = dict(symbol='588000.SH', event_at='2021-01-04T09:35:00+08:00',
             received_at='2021-01-04T09:35:01+08:00', price_view='raw',
             bid=1., ask=1.001, bid_size=100, ask_size=100, phase='continuous')
    assert visible_quote([q], '588000.SH', '2021-01-04T09:35:00+08:00', 5) is None
    assert not visible_quote([q], '588000.SH', '2021-01-04T09:35:02+08:00', 5)['actual_fill_proven']
    assert visible_quote([q], '588000.SH', '2021-01-04T09:36:00+08:00', 5) is None
    halt = dict(q, received_at='2021-01-04T09:35:02+08:00', phase='halt')
    assert visible_quote([q, halt], '588000.SH', '2021-01-04T09:35:03+08:00', 5) is None
    with pytest.raises(ValueError):
        visible_quote([q], '000688.SH', '2021-01-04T09:35:02+08:00', 5)
    with pytest.raises(ValueError):
        visible_quote([dict(q, price_view='qfq')], '588000.SH', '2021-01-04T09:35:02+08:00', 5)


def test_evidence_hash_binding_and_no_automatic_economic_admission(tmp_path):
    files = {}
    for name in ['raw.txt', 'generator.txt', 'clocks.txt', 'coverage.txt']:
        p = tmp_path / name
        p.write_text('Artificial test evidence, no historical market proof.\n')
        files[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    r = dict(version(), evidence_ref='raw.txt', evidence_sha256=files['raw.txt'])
    p = tmp_path / 'versions.jsonl'
    p.write_text(json.dumps(r) + '\n')
    files[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = dict(schema='star50_external_market_bundle@1', files=files,
                    revision_policy='append_only_first_and_corrections',
                    clock_basis='received_at', bar_versions_file=p.name,
                    generator_evidence_file='generator.txt', clock_semantics_file='clocks.txt',
                    coverage_file='coverage.txt')
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    result = inspect_bundle(tmp_path)
    assert result['format_integrity_pass'] and not result['intraday_strategy_admitted']
    (tmp_path / 'raw.txt').write_text('changed')
    with pytest.raises(ValueError, match='hash mismatch'):
        inspect_bundle(tmp_path)
