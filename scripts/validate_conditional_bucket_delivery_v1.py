"""Validate existing account replay outputs; never execute or refit a strategy."""
from __future__ import annotations

import hashlib
import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/conditional_bucket_accounts_v1p3'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    frozen = json.loads((OUT / 'source_freeze.json').read_text())
    for name, expected in frozen['sources'].items():
        assert digest(ROOT / name) == expected, name
    for name, key in [('causal_measurement_panel.parquet', 'panel_sha256'),
                      ('entry_measurements.parquet', 'entries_sha256')]:
        assert digest(ROOT / 'artifacts/conditional_bucket_v1_preflight' / name) == frozen[key]
    formal = OUT / 'family'
    isolated = OUT / 'isolated/family'
    names = sorted(p.relative_to(formal) for p in formal.glob('*/*.parquet'))
    names += [Path('summary.csv'), Path('run_receipt.json')]
    assert len(names) == 92
    assert {p.relative_to(isolated) for p in isolated.glob('*/*.parquet')} == set(names[:-2])
    checks = []
    for name in names:
        a, b = digest(formal / name), digest(isolated / name)
        checks.append({'path': str(name), 'formal_sha256': a,
                       'isolated_sha256': b, 'identical': a == b})
    assert all(x['identical'] for x in checks)
    save('replay_validation.json', {'passed': True, 'files': len(checks),
         'scope': 'fresh process/account states; same frozen implementation, not an alternative algorithm',
         'sources_and_feature_inputs_unchanged': True, 'checks': checks})
    tests = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=ROOT,
                           capture_output=True, text=True)
    save('test_receipt.json', {'command': [sys.executable, '-m', 'pytest', '-q'],
         'exit_code': tests.returncode, 'stdout': tests.stdout, 'stderr': tests.stderr})
    assert tests.returncode == 0, tests.stdout + tests.stderr
    accounts = json.loads((formal / 'account_validation.json').read_text())
    assert len(accounts) == 18
    assert all(a['accounting_passed'] and a['economic_valid'] and a['coverage_incidents'] == 0
               for a in accounts)
    with (OUT / 'comparison.csv').open() as stream:
        comparison = list(csv.DictReader(stream))
    assert len(comparison) == 18 and all(float(row['net_pnl']) < 0 for row in comparison)
    assert not any(row['joint_goals'] == 'True' for row in comparison if row['carrier'] == 'spot')
    assert {row['policy'] for row in comparison if row['carrier'] == 'option'
            and row['joint_goals'] == 'True'} == {'small_work', 'opposed_slow', 'reversal_chop'}
    save('controller_acceptance.json', {
        'controller': 'Codex', 'bounded_campaign_complete': True,
        'accounting_and_same_source_replay_passed': True,
        'source_freeze_sha256': digest(OUT / 'source_freeze.json'),
        'account_count': 18, 'challenger_count': 5,
        'period': '2025 consumed retrospective history',
        'valid_progression_retained': {
            '588000_option_joint_relative_improvement': ['small_work', 'opposed_slow', 'reversal_chop'],
            'both_etf_quality_only': ['fast_without_progress']},
        'all_accounts_net_losing': True,
        'no_etf_challenger_meets_both_goals': True,
        'strategy_promoted': False, 'owner_top_level_goal_achieved': False,
        'fresh_oos': False, 'production_authority': False,
        'blocked_replication': '588080 option PIT contract terms; bd://fl-vcyb3',
        'limitations': ['one complete economic year', 'fixed units, not prior full-investment path',
                        'observed-bid valuation, not latent unquoted-price risk',
                        'fee directions and carrier/account mapping are stated controller assumptions'],
    })
    paths = [ROOT / name for name in frozen['sources']]
    paths += [ROOT / 'scripts' / name for name in [
        'report_conditional_bucket_accounts_v1.py', 'replay_conditional_bucket_accounts_v1.py',
        'validate_conditional_bucket_delivery_v1.py']]
    paths += [ROOT / 'docs/research/conditional_bucket_v1' / name
              for name in ['result_v1.md', 'datahub_terms_repair_prompt.md']]
    paths += [p for p in OUT.iterdir() if p.is_file() and p.name != 'delivery_manifest.json']
    paths += [formal / name for name in names]
    paths += [formal / 'account_validation.json']
    save('delivery_manifest.json', {'purpose': 'bounded delivery closure; historical freezes unchanged',
         'files': {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(paths))}})
    print(tests.stdout.strip())
    print('PASS: 92 byte-identical raw replay files; 18 accounting checks; sources unchanged.')


if __name__ == '__main__':
    main()
