"""Read-only provider diagnosis; writes evidence only inside the STAR50 lab."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/conditional_bucket_v1_datahub_diagnosis'
HUB = Path('/home/starryocean/桌面/量化/unified_datahub')
DB = HUB/'.runtime/live/meta/metadata.sqlite3'
RAW = Path('/home/starryocean/.cache/datahub/etf-option-raw-prefetch-v10')
OLD_WORK = Path('/datahub/cold/runtime/live/worksets/etf_option_depth_source_native_ms_v1')
LAKE = Path('/datahub/cold/runtime/live/lake/derivative_option_depth_snapshots')


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(name, obj):
    (OUT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')


def main():
    assert not OUT.exists(), 'Preserve prior diagnosis'
    OUT.mkdir(parents=True)
    now = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    queries = {
        'deep_legacy_versions': "SELECT dataset_version,dataset_kind,state,time_range_start,time_range_end,storage_uri FROM dataset_versions WHERE dataset_version LIKE '%option%depth%'",
        'deep_v2_versions': "SELECT dataset_version,product_id,storage_uri FROM dataset_versions_v2 WHERE dataset_version LIKE '%option%depth%' OR product_id LIKE '%etf%depth%'",
        'deep_serving_decisions': "SELECT product_id,consumer_contract,capability,dataset_version,action,reason,sequence_no,decided_at FROM product_serving_decisions WHERE product_id LIKE '%etf%depth%' OR dataset_version LIKE '%option%depth%'",
        'all_option_serving_decisions': "SELECT product_id,consumer_contract,capability,dataset_version,action,sequence_no FROM product_serving_decisions WHERE product_id LIKE '%option%' ORDER BY decided_at DESC",
        'fund_quote_versions': "SELECT dataset_version,state,time_range_start,time_range_end,storage_uri FROM dataset_versions WHERE dataset_version LIKE '%fund_cb_l2%'",
        'sse_etf_option_versions': "SELECT dataset_version,state,time_range_start,time_range_end FROM dataset_versions WHERE dataset_version LIKE '%option%' AND (dataset_version LIKE '%etf%' OR dataset_version LIKE '%sse%' OR dataset_version LIKE '%depth%')",
    }
    with sqlite3.connect('file:'+str(DB)+'?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        records = {name: [dict(r) for r in conn.execute(sql)] for name, sql in queries.items()}
    save('registry_readonly_snapshot.json', {'queried_at': now, 'db': str(DB), 'queries': queries, 'results': records})
    raw_days = sorted(p.name.split('=')[-1] for p in (RAW/'daily').iterdir() if p.is_dir())
    allowed = [d for d in raw_days if d <= '20251231']
    retirements = []
    for path in sorted((RAW/'retirement/daily_directory').glob('*.json')):
        data = json.loads(path.read_text())
        retirements.append({'path': str(path), 'sha256': sha(path), 'key': data['key'],
                            'status': data['status'],
                            'expected_outputs': [{'path': item['path'], 'exists': Path(item['path']).is_file(),
                                                  'expected_sha256': item['sha256']}
                                                 for item in data['workset_day_receipts']]})
    save('raw_inventory_and_retirement.json', {
        'raw_root': str(RAW), 'raw_day_count': len(raw_days),
        'raw_days_through_2025': allowed, 'raw_prices_read': 0,
        'raw_payload_hashes_not_reverified': True,
        'retirement_receipts': retirements,
        'lake_root': str(LAKE), 'lake_children': [p.name for p in LAKE.iterdir()],
        'old_work_root': str(OLD_WORK), 'old_work_root_exists': OLD_WORK.exists()})
    units = ['datahub-etf-option-depth-backfill.service',
             'datahub-etf-option-depth-prefetched-materialization.service',
             'datahub-etf-option-depth-candidate-audit.path',
             'datahub-etf-option-depth-replay-determinism.path']
    states = {}
    for unit in units:
        result = subprocess.run(['systemctl', '--user', 'show', unit, '-p', 'LoadState', '-p', 'ActiveState',
                                 '-p', 'SubState', '-p', 'FragmentPath'], capture_output=True, text=True)
        states[unit] = {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    save('service_states.json', states)
    args = [str(HUB/'.venv/bin/python'), str(HUB/'scripts/etf_option_depth_onboarding.py'), 'coverage',
            '--db-path', str(DB), '--dataset-version',
            'derivative_option_depth_snapshots_cn_etf_source_native_ms_20200102_20260825_ready_v1_20260830',
            '--now', now]
    result = subprocess.run(args, capture_output=True, text=True, timeout=45)
    (OUT/'coverage_error.log').write_text(result.stdout+result.stderr)
    references = [HUB/'evidence/etf_option_depth_onboarding_20260830/raw_prefetch_final_acceptance.json',
                  HUB/'evidence/etf_option_depth_onboarding_20260830/source_feasibility_ledger.json',
                  HUB/'docs/modules/history/etf-option-depth-source-native-ms-workflow.md',
                  HUB/'docs/planning/fund_cb_l2_quote_change_recent_1y_onboarding_20260901.md']
    save('diagnosis.json', {
        'checked_at': now, 'responsible_owner': 'DataHub',
        'factorlab_date_filter_is_not_the_sufficient_cause': True,
        'recent_quote_products_only_confirmed_joint_2025_window': ['2025-09-01', '2025-12-31'],
        'recent_quote_product_joint_days': 82,
        'long_option_raw_archive_exists': True,
        'raw_directories_remaining': len(raw_days), 'raw_directories_through_2025': len(allowed),
        'remaining_raw_range_through_2025': [allowed[0], allowed[-1]],
        'deep_registered_versions': len(records['deep_v2_versions']),
        'deep_serving_decisions': len(records['deep_serving_decisions']),
        'deep_lake_root_children': len(list(LAKE.iterdir())),
        'expected_old_work_root_exists': OLD_WORK.exists(),
        'retirement_receipt_count': len(retirements),
        'missing_retirement_output_paths': sum(not i['exists'] for r in retirements for i in r['expected_outputs']),
        'coverage_command': args, 'coverage_exit_code': result.returncode,
        'coverage_log_sha256': sha(OUT/'coverage_error.log'),
        'historical_fund_bbo_requires_separate_source_scope_audit': True,
        'do_not_infer_historical_book_from_daily_or_minute_bars': True,
        'do_not_infer_deleted_or_lost_from_missing_current_path': True,
        'required_provider_action': 'locate_previous_materialization_and_retired_outputs; reuse_available_raw; audit_bounded_STAR50_history; certify_register_and_grant_exact_research_access',
        'references': {str(p): sha(p) for p in references},
        'provider_mutations': 0, 'raw_quote_or_return_values_read': 0,
        'strategy_research_resumed': False,
    })
    print((OUT/'diagnosis.json').read_text())


if __name__ == '__main__':
    main()
