"""Targeted reacceptance of F1/F2/E1; no provider or strategy mutations."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import accept_datahub_star50_delivery_v1 as audit

OUT = ROOT/'artifacts/datahub_reacceptance_v1_20260906'
OLD = ROOT/'artifacts/datahub_acceptance_v1_20260906'
HUB = Path('/home/starryocean/桌面/量化/unified_datahub')
audit.OUT = OUT


def save(name, obj):
    (OUT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str)+'\n')


def main():
    assert not (OUT/'controller_verdict.json').exists(), 'Preserve completed reacceptance'
    OUT.mkdir(exist_ok=True)
    old = json.loads((OLD/'supplier_handoff.json').read_text())
    new = json.loads((HUB/'evidence/star50_history_bbo_20260906/factorlab_handoff.json').read_text())
    if (OUT/'supplier_handoff.json').exists():
        assert json.loads((OUT/'supplier_handoff.json').read_text()) == new
    else:
        save('supplier_handoff.json', new)
    save('data_usage.json', {'kind': 'repeat_audit_only', 'quote_dates_max': '2025-12-31',
                            'strategy_results': False, 'live_provider_mutation': False})
    ro = Path(old['spot']['coverage']['storage_uri'])
    rn = Path(new['spot']['coverage']['storage_uri'])
    mo = json.loads((ro/'manifest.json').read_text())
    mn = json.loads((rn/'manifest.json').read_text())
    assert audit.sha(ro/'manifest.json') == old['spot']['coverage']['manifest_sha256']
    assert audit.sha(rn/'manifest.json') == new['spot']['coverage']['manifest_sha256']
    assert mn['dataset_hash'] == '0b0706fdaecc80f2406197e98638aef1b4712cbbcda9fde2e38deb7442a8251e'
    old_by_day = {r['trading_day']: r for r in mo['files']}
    assert set(old_by_day) == {r['trading_day'] for r in mn['files']}
    checks = json.loads((OUT/'spot_complete_diff.json').read_text()) if (OUT/'spot_complete_diff.json').exists() else []
    if checks:
        assert len(checks) == len(mn['files']) == 483
        print('Reusing completed full spot old/new comparison', flush=True)
    for item in ([] if checks else mn['files']):
        previous = old_by_day[item['trading_day']]
        a, b = ro/previous['path'], rn/item['path']
        assert audit.sha(a) == previous['sha256'], 'Old immutable payload changed'
        assert audit.sha(b) == item['sha256']
        f = pq.ParquetFile(a).read().to_pandas()
        g = pq.ParquetFile(b).read().to_pandas()
        assert len(f) == len(g) == item['record_count']
        assert set(f).issubset(g)
        extra = set(g)-set(f)
        assert extra <= {'trading_month'}
        if extra:
            month = item['trading_day'][:4]+'-'+item['trading_day'][4:6]
            assert (g.trading_month == month).all()
        pd.testing.assert_frame_equal(f.drop(columns='valid_until'),
                                      g.loc[:,f.columns].drop(columns='valid_until'),
                                      check_dtype=False, check_exact=True)
        reverse = f.valid_until < f.valid_from
        expected = f.valid_until.copy()
        expected.loc[reverse] = f.loc[reverse,'valid_from'] + pd.Timedelta(milliseconds=1)
        assert (pd.to_datetime(expected).astype('datetime64[ns]').to_numpy()
                == pd.to_datetime(g.valid_until).astype('datetime64[ns]').to_numpy()).all()
        assert not (g.valid_until < g.valid_from).any()
        assert (f.loc[reverse,'session_phase'] == 'post_close').all()
        zero_old = int((f.valid_until == f.valid_from).sum())
        zero_new = int((g.valid_until == g.valid_from).sum())
        assert zero_old == zero_new
        checks.append({'day': item['trading_day'], 'rows': len(g), 'changed_intervals': int(reverse.sum()),
                       'zero_width_preserved': zero_new, 'other_original_columns_exact': True,
                       'old_sha_preserved': True, 'new_sha_valid': True,
                       'extra_partition_column': sorted(extra)})
        if len(checks)%100 == 0:
            print('Compared complete old/new spot files:', len(checks), flush=True)
    save('spot_complete_diff.json', checks)
    assert sum(r['changed_intervals'] for r in checks) == 959
    assert sum(r['rows'] for r in checks) == 4755248
    cases = []
    sys.path.insert(0, str(HUB/'src'))
    from datahub.storage.schema import create_all_tables
    for kind in ['option', 'spot']:
        h = new[kind]
        common = ['--product',kind,'--dataset-version',h['dataset_version']]
        day = '2023-06-05' if kind == 'option' else '2024-01-02'
        symbol = '588000.XSHG' if kind == 'option' else '588000.SSE'
        query = ['query',*common,'--start-time',day+'T09:40:00','--end-time',day+'T09:42:00',
                 '--symbol',symbol,'--limit','2']
        cases.append(audit.cli(kind+'_live', query))
        cases.append(audit.cli(kind+'_coverage', ['coverage',*common]))
        with tempfile.TemporaryDirectory(prefix='star50-grant-negative-') as temp:
            tmp = Path(temp)
            empty = tmp/'empty.sqlite3'
            create_all_tables(empty)
            cases.append(audit.cli(kind+'_empty_db', [*query,'--metadata-db',str(empty)]))
            cases.append(audit.cli(kind+'_missing_db', [*query,'--metadata-db',str(tmp/'missing.sqlite3')]))
            fake_root = tmp/'wrong-manifest'/('dataset_version='+h['dataset_version'])
            fake_root.mkdir(parents=True)
            manifest = json.loads((Path(h['coverage']['storage_uri'])/'manifest.json').read_text())
            manifest['record_count'] += 1
            (fake_root/'manifest.json').write_text(json.dumps(manifest))
            cases.append(audit.cli(kind+'_wrong_manifest', [*query,'--'+kind+'-lake-parent',str(fake_root.parent)]))
    cases.append(audit.cli('spot_old_version', ['coverage','--product','spot','--dataset-version',old['spot']['dataset_version']]))
    save('read_gate_canaries.json', cases)
    for case in cases:
        positive = case['name'].endswith(('_live','_coverage'))
        assert (case['returncode'] == 0) == positive, case['name']
        if positive:
            assert case['output']['serving_grant']
    from datahub.core.services.reliability.operational_certification.product_serving import ProductServingPointerResolver
    resolutions = {}
    for kind, h in ((k,new[k]) for k in ['option','spot']):
        resolved = ProductServingPointerResolver(HUB/'.runtime/live/meta/metadata.sqlite3').resolve(
            product_id=h['product_id'], consumer_contract=h['consumer_contract'], capability=h['capability'])
        resolutions[kind] = resolved.to_dict()
        assert resolved.ready and resolved.dataset_version == h['dataset_version']
    save('active_resolutions.json', resolutions)
    # Reuse the prior full option-payload SHA acceptance; no option files changed
    # in this repair. Recheck manifest and sidecars, then rerun the five specific
    # logical source-replay samples into THIS acceptance evidence directory.
    opt_root = Path(new['option']['coverage']['storage_uri'])
    assert audit.sha(opt_root/'manifest.json') == old['option']['coverage']['manifest_sha256']
    opt_manifest = json.loads((opt_root/'manifest.json').read_text())
    for path, digest in opt_manifest['sidecars'].items():
        assert audit.sha(opt_root/path) == digest
    result = subprocess.run([str(HUB/'.venv/bin/python'), str(HUB/'scripts/star50_history_bbo_onboarding.py'),
                             'replay','--evidence-dir',str(OUT/'independent_replay')], cwd=HUB,
                            capture_output=True, text=True,
                            env={**os.environ,'OPENBLAS_NUM_THREADS':'1'}, timeout=240)
    (OUT/'independent_replay.log').write_text(result.stdout+result.stderr)
    assert result.returncode == 0, result.stderr[-1500:]
    replay = json.loads(result.stdout)
    save('replay_result.json', replay)
    required = {'strike','contract_multiplier','expiry_date','contract_symbol','option_type',
                'session_phase','observation_datetime','archive_available_at','ingested_at',
                'source_receipt_sha256','master_receipt_sha256','bid_price_1','ask_price_1',
                'bid_volume_1','ask_volume_1'}
    assert required <= set(replay['content_fields']) and len(replay['content_fields']) == 21
    assert len(replay['sample_days']) == 5 and all(r['content_identical'] for r in replay['sample_days'])
    previous_receipt = json.loads((HUB/'evidence/star50_history_bbo_20260906/option_replay.json').read_text())
    assert [r['content_digest'] for r in replay['sample_days']] == [r['content_digest'] for r in previous_receipt['sample_days']]
    verdict = {'status':'passed_for_bounded_L1_research', 'F1':'passed','F2':'passed','E1':'passed_21_fields_five_samples',
               'spot_version':new['spot']['dataset_version'], 'spot_rows':sum(r['rows'] for r in checks),
               'spot_changed_intervals':959,'spot_reverse_intervals_after':0,
               'spot_zero_width_unchanged':sum(r['zero_width_preserved'] for r in checks),
               'original_spot_columns_other_than_valid_until_unchanged':True,
               'old_spot_version_immutable':True, 'extra_trading_month_is_valid_partition_metadata':True,
               'option_full_file_integrity_prior_evidence_reused':True,
               'option_replay_scope':'21 declared L1/key/contract/time/receipt fields, five real dates; not all depth levels or every payload column',
               'post_close_rows_are_not_tradable':True,'zero_width_rows_are_not_executable_intervals':True,
               'known_spot_missing_days':['2024-11-18','2024-11-19'],
               'spot_2021_2023_unavailable':True,'strategy_returns_computed':False,'production_authority':False}
    save('controller_verdict.json',verdict)
    print(json.dumps(verdict,ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
