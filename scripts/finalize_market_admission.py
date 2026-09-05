"""Aggregate reviewed inventory/metadata evidence only; no price data access."""
import json
from audit_market_admission import ROOT, OUT, DOC, OLD, POLICIES, validate, sha, write_json


def build():
    if (OUT / 'feasibility_totals.json').exists():
        raise ValueError('Do not overwrite closeout')
    validate()
    sessions = [json.loads((OUT / 'sessions' / str(y) / 'summary.json').read_text())
                for y in range(2021, 2026)]
    totals = []
    for policy in POLICIES:
        rows = [next(r for r in s['metrics'] if r['policy'] == policy) for s in sessions]
        keys = ['minute_observations', 'negative_target_minutes', 'cash_mismatch_minutes',
                'frozen_order_events', 'next_day_pending_events', 'blocked_sell_events',
                'blocked_sell_units_requested']
        result = {k: sum(r[k] for r in rows) for k in keys}
        result['policy'] = policy
        result['negative_target_share'] = result['negative_target_minutes'] / result['minute_observations']
        result['cash_mismatch_share'] = result['cash_mismatch_minutes'] / result['minute_observations']
        totals.append(result)
    write_json(OUT / 'feasibility_totals.json', {'metrics': totals,
        'yearly': [{'year': s['year'], 'metrics': s['metrics']} for s in sessions],
        'source': 'sealed annual summaries', 'tradable_pnl_computed': False})
    carrier = ROOT / 'artifacts/drawdown_conditions/input_material_receipt.json'
    receipt = json.loads(carrier.read_text())
    required = ['source_sent_at', 'received_at', 'first_seen_at', 'revision_id']
    source = {'input_receipt_sha256': sha(carrier), 'metadata_only': True,
              'views': [{'view': v['view_id'], 'rows': v['rows'],
                         'missing_provenance_fields': sorted(set(required) - set(v['columns']))}
                        for v in receipt['views']],
              'source_audits': [], 'legacy_availability_status': 'unproven',
              'market_realtime_publication_exists': True,
              'source_or_receiver_archive_delivered': False,
              'raw_etf_execution_history_delivered': False,
              'intraday_strategy_admitted': False, 'production_authority': False}
    for year in range(2021, 2026):
        p = OLD / str(year) / 'source_audit.json'
        r = json.loads(p.read_text())
        source['source_audits'].append({'year': year, 'sha256': sha(p),
            'minute_rows': r['minute_rows'], 'synthetic_minutes': r['synthetic_minutes'],
            'availability_offset_patterns': r['availability_offset_patterns']})
    write_json(OUT / 'source_inventory.json', source)
    print(json.dumps(totals, ensure_ascii=False))


if __name__ == '__main__':
    build()
