"""Metadata preflight and causal measurement surface; no policy PnL evaluation."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from star50_filter.conditional_bucket_measurements import FEATURES, causal_measurements
from star50_filter.filters import butter_lowpass, hysteresis_positions

OUT = ROOT/'artifacts/conditional_bucket_v1_preflight'
CONTRACT = ROOT/'docs/research/conditional_bucket_v1/owner_contract.json'
VERSIONS = {
    'fund': 'fund_cb_l2_quote_change_cn_a_3s_baidu_shidang_20250901_20260828_v1_20260902',
    'option': 'derivative_option_quote_change_l5_cn_etf_recent_1y_20250901_20260825_ready_v1_20260901',
}


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def main():
    assert not OUT.exists(), 'Do not overwrite preflight evidence'
    OUT.mkdir(parents=True)
    now = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    inventory = {}
    for key, version in VERSIONS.items():
        response = requests.get('http://127.0.0.1:8400/api/v1/history/datasets/'+version, timeout=15)
        response.raise_for_status()
        data = response.json()['data']
        save(key+'_api_manifest.json', data)
        path = Path(data['storage_uri'])/'manifest.json'
        manifest = json.loads(path.read_text())
        files = manifest['files']
        bounded = []
        for item in files:
            text = item['path']
            if key == 'option' and item['exchange'] != 'SSE':
                continue
            if key == 'option':
                day = item['trading_day']
                day = day[:4]+'-'+day[4:6]+'-'+day[6:8]
            else:
                day = Path(text).name.split('=')[1].split('.parquet')[0]
            if day <= '2025-12-31':
                bounded.append({'day': day, 'path': str(path.parent/text),
                                'exists': (path.parent/text).is_file(),
                                'manifest_sha256': item['sha256']})
        save(key+'_bounded_files.json', bounded)
        inventory[key] = {'version': version, 'api_state': data['state'],
                          'manifest_sha256': sha(path), 'days_at_or_before_2025': len(bounded),
                          'first': min(i['day'] for i in bounded), 'last': max(i['day'] for i in bounded),
                          'files_present': sum(i['exists'] for i in bounded),
                          'symbol_specific_quote_coverage_verified': False,
                          'quote_values_read': 0}
    provider = Path('/home/starryocean/桌面/量化/unified_datahub')
    args = [str(provider/'.venv/bin/python'), str(provider/'scripts/etf_option_depth_onboarding.py'),
            'coverage', '--db-path', str(provider/'.runtime/live/meta/metadata.sqlite3'),
            '--dataset-version', 'derivative_option_depth_snapshots_cn_etf_source_native_ms_20200102_20260825_ready_v1_20260830',
            '--now', now]
    result = subprocess.run(args, text=True, capture_output=True, timeout=45)
    (OUT/'deep_history_coverage.log').write_text(result.stdout+result.stderr)
    inventory['deep_history'] = {'returncode': result.returncode, 'command': args,
                                 'log_sha256': sha(OUT/'deep_history_coverage.log'),
                                 'read_denied': result.returncode != 0}
    source = ROOT/'artifacts/drawdown_material/5m_offset_0.parquet'
    frame = pd.read_parquet(source, columns=['timestamp', 'trading_day', 'close'],
                            filters=[('trading_day', '<=', '2025-12-31')])
    assert frame.trading_day.max() <= '2025-12-31'
    price = frame.close.to_numpy(float)
    x = np.log(price)
    sigma = pd.Series(x).diff().rolling(48).std(ddof=0).to_numpy()
    signal = hysteresis_positions(butter_lowpass(x, 12, 1), sigma)
    measurements = causal_measurements(price, signal)
    stop = len(frame)//2
    pd.testing.assert_frame_equal(measurements.iloc[:stop], causal_measurements(price[:stop], signal[:stop]))
    output = pd.concat([frame[['timestamp', 'trading_day']].reset_index(drop=True), measurements], axis=1)
    output['frozen_signal'] = signal
    flips = np.r_[False, (signal[1:] != signal[:-1]) & (signal[1:] != 0) & (signal[:-1] != 0)]
    output['original_entry_event'] = flips
    output['all_measurements_present'] = measurements.notna().all(axis=1)
    output = output.loc[output.trading_day >= '2021-01-01'].copy()
    output.to_parquet(OUT/'causal_measurement_panel.parquet', index=False)
    output.loc[output.original_entry_event].to_parquet(OUT/'entry_measurements.parquet', index=False)
    sources = ['src/star50_filter/conditional_bucket_measurements.py', 'src/star50_filter/filters.py',
               'scripts/prepare_conditional_bucket_v1.py', 'tests/test_conditional_bucket_measurements.py']
    report = {
        'prepared_at': now, 'owner_contract_sha256': sha(CONTRACT), 'source_input_sha256': sha(source),
        'sources': {p: sha(ROOT/p) for p in sources}, 'inventory': inventory,
        'measurement_features': FEATURES, 'development_rows': len(output),
        'original_entry_events': int(output.original_entry_event.sum()),
        'entry_events_with_all_measurements': int((output.original_entry_event & output.all_measurements_present).sum()),
        'real_price_prefix_invariance': True,
        'measurement_panel_sha256': sha(OUT/'causal_measurement_panel.parquet'),
        'entry_panel_sha256': sha(OUT/'entry_measurements.parquet'),
        'quote_values_read': 0, 'new_pnl_or_bucket_results_computed': False,
        'new_veto_admitted': False, 'data_2026_used': False,
        'blocking_choices': ['fee_per_side_or_round_trip', 'underlying_and_direction_mapping'],
        'account_backtest_ready': False, 'production_authority': False,
        'status': 'causal_measurements_prepared_pending_execution_contract_and_coverage',
    }
    save('preflight.json', report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
