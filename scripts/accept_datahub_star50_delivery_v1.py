"""Independent, read-only delivery checks. Never promotes DataHub or trades."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time
from zoneinfo import ZoneInfo

import duckdb
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/datahub_acceptance_v1_20260906'
HUB = Path('/home/starryocean/桌面/量化/unified_datahub')
DB = HUB/'.runtime/live/meta/metadata.sqlite3'
PYTHON = HUB/'.venv/bin/python'
CLI = HUB/'scripts/star50_history_bbo_onboarding.py'
HANDOFF = HUB/'evidence/star50_history_bbo_20260906/factorlab_handoff.json'


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str)+'\n')


def cli(name, args, extra_env=None):
    started = time.monotonic()
    p = subprocess.run([str(PYTHON), str(CLI), *args], cwd=HUB,
                       env={**os.environ, 'OPENBLAS_NUM_THREADS': '1', **(extra_env or {})},
                       text=True, capture_output=True, timeout=90)
    (OUT/(name+'.log')).write_text(p.stdout+p.stderr)
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError:
        data = None
    return {'name': name, 'args': args, 'returncode': p.returncode,
            'seconds': time.monotonic()-started, 'output': data, 'stderr': p.stderr[-1500:]}


def check_file(task):
    kind, root, item = task
    path = root/item['path']
    rows = pq.ParquetFile(path).metadata.num_rows
    digest = sha(path)
    return {'product': kind, 'path': item['path'], 'rows': rows, 'bytes': path.stat().st_size,
            'sha256': digest, 'valid': rows == item['record_count'] and digest == item['sha256']
            and path.stat().st_size == item['byte_count']}


def main():
    assert not (OUT/'file_checks.json').exists(), 'Do not overwrite acceptance evidence'
    handoff = json.loads(HANDOFF.read_text())
    save('supplier_handoff.json', handoff)
    roots, manifests, grants = {}, {}, {}
    with sqlite3.connect('file:'+str(DB)+'?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        for kind in ['option', 'spot']:
            h = handoff[kind]
            roots[kind] = Path(h['coverage']['storage_uri'])
            m = json.loads((roots[kind]/'manifest.json').read_text())
            manifests[kind] = m
            assert sha(roots[kind]/'manifest.json') == h['coverage']['manifest_sha256']
            assert m['dataset_version'] == h['dataset_version'] and m['production_granted'] is False
            rows = [dict(r) for r in conn.execute(
                'SELECT decision_id,product_id,consumer_contract,capability,dataset_version,action,manifest_hash,sequence_no,decided_at FROM product_serving_decisions WHERE product_id=? AND consumer_contract=? AND capability=? ORDER BY sequence_no DESC',
                (h['product_id'], h['consumer_contract'], h['capability']))]
            grants[kind] = rows
    save('actual_serving_decisions.json', grants)
    tasks = [(k, roots[k], item) for k, m in manifests.items() for item in m['files']]
    print('Verifying', len(tasks), 'files;', sum(t[2]['byte_count'] for t in tasks), 'bytes', flush=True)
    checks = []
    workers = max(1, min(2, int(os.environ.get('FACTOR_LAB_RESEARCH_WORKERS', '2'))))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [pool.submit(check_file, task) for task in tasks]
        for job in as_completed(jobs):
            checks.append(job.result())
            if len(checks)%150 == 0:
                print('File hashes and footer counts checked:', len(checks), flush=True)
    checks.sort(key=lambda x: (x['product'], x['path']))
    save('file_checks.json', checks)
    sidecars = []
    for kind, m in manifests.items():
        for path, digest in m.get('sidecars', {}).items():
            sidecars.append({'product': kind, 'path': path, 'valid': sha(roots[kind]/path) == digest})
    save('sidecar_checks.json', sidecars)
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Shanghai'")
    con.execute(f'SET threads={workers}')
    spot_paths = [str(roots['spot']/item['path']) for item in manifests['spot']['files']]
    spot = con.execute('''SELECT instrument_id,trading_day,count(*) n,
       min(market_observed_at) first_observed,max(market_observed_at) last_observed,
       count_if(valid_until<valid_from) negative_intervals,
       count_if(CAST(market_observed_at AS DATE)<>CAST(trading_day AS DATE)) day_mismatch,
       count_if(bid_price_x10000_1>ask_price_x10000_1 AND ask_price_x10000_1>0) crossed,
       count_if(bid_size_1<0 OR ask_size_1<0) negative_size
       FROM read_parquet(?,hive_partitioning=false) GROUP BY 1,2 ORDER BY 1,2''', [spot_paths]).fetchdf()
    spot.to_csv(OUT/'spot_all_symbol_days.csv', index=False)
    option_samples = []
    sample_days = ['20230605','20231229','20240102','20240325','20241231','20251231']
    for item in manifests['option']['files']:
        if item['trading_day'] not in sample_days:
            continue
        p = str(roots['option']/item['path'])
        frame = con.execute('''SELECT underlying_symbol,trading_day,count(*) n,
          min(observation_datetime) first_observed,max(observation_datetime) last_observed,
          count(DISTINCT listing_instance_id) contracts,
          count_if(CAST(observation_datetime AS DATE)<>trading_day) day_mismatch,
          count_if(CAST(expiry_date AS DATE)<trading_day) expired,
          count_if(bid_price_1>ask_price_1 AND ask_price_1>0) crossed,
          count_if(contract_multiplier<=0 OR strike<=0) invalid_terms,
          min(contract_multiplier) min_multiplier,max(contract_multiplier) max_multiplier
          FROM read_parquet(?,hive_partitioning=false) GROUP BY 1,2''', [p]).fetchdf()
        option_samples.extend(frame.to_dict('records'))
    save('option_sample_checks.json', option_samples)
    master = con.execute('''SELECT * FROM read_parquet(?) WHERE listed_date<='2025-12-31' ''',
                         [str(roots['option']/'contract_metadata.parquet')]).fetchdf()
    save('contract_metadata_summary.json', {'all_rows_footer': pq.ParquetFile(roots['option']/'contract_metadata.parquet').metadata.num_rows,
         'rows_listed_by_2025': len(master), 'fields': list(master.columns),
         'underlyings': sorted(master.underlying_symbol.unique().tolist()),
         'multipliers': sorted(master.contract_multiplier.unique().tolist()),
         'duplicate_order_book_ids': int(master.order_book_id.duplicated().sum())})
    con.close()
    cases = []
    for kind in ['option','spot']:
        common = ['--product',kind,'--dataset-version',handoff[kind]['dataset_version']]
        cases.append(cli(kind+'_coverage', ['coverage', *common]))
        day = '2023-06-05' if kind == 'option' else '2024-01-02'
        symbol = '588000.XSHG' if kind == 'option' else '588000.SSE'
        query = ['query',*common,'--start-time',day+'T09:40:00','--end-time',day+'T09:42:00','--symbol',symbol,'--limit','2']
        cases.append(cli(kind+'_positive',query))
        cases.append(cli(kind+'_missing_version',['coverage','--product',kind]))
        with tempfile.TemporaryDirectory(prefix='star50-no-serving-') as temp:
            # No modifications to the live database or grants. A reader claiming
            # exact serving must refuse a database with no serving decision.
            missing = str(Path(temp)/'absent.sqlite3')
            cases.append(cli(kind+'_no_serving_database', [*query,'--metadata-db',missing]))
    cases.append(cli('spot_gap',['query','--product','spot','--dataset-version',handoff['spot']['dataset_version'],
        '--start-time','2021-01-04T09:30:00','--end-time','2021-01-04T09:31:00','--limit','2']))
    save('query_canaries.json', cases)
    failures = [x['name'] for x in cases if x['name'].endswith('no_serving_database') and x['returncode'] == 0]
    save('inspection_summary.json', {
        'checked_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'all_file_checks_passed': all(x['valid'] for x in checks), 'files': len(checks),
        'all_sidecars_passed': all(x['valid'] for x in sidecars),
        'rows_by_product': {k:sum(x['rows'] for x in checks if x['product']==k) for k in roots},
        'spot_symbol_days_checked': len(spot), 'spot_invariant_failures':
           spot[['negative_intervals','day_mismatch','crossed','negative_size']].sum().to_dict(),
        'option_sample_symbol_days': len(option_samples),
        'negative_serving_canaries_failed': failures,
        'raw_source_reprocessing_performed': False,
        'strategy_returns_computed': False, 'production_authority': False})
    print((OUT/'inspection_summary.json').read_text(), flush=True)


if __name__ == '__main__':
    main()
