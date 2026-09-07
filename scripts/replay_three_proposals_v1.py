"""Fresh-input/state reproduction after every scientific year is reviewed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

import run_three_proposals_v1 as runner
import report_three_proposals_v1 as reporter

ROOT = Path(__file__).resolve().parents[1]
FORMAL = runner.OUT
REPLAY = FORMAL / 'isolated'


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    runner.check(prepared=True)
    for year in range(2021, 2026):
        assert (FORMAL / str(year) / 'review.json').exists()
    assert not REPLAY.exists(), 'Do not overwrite an existing independent run'
    REPLAY.mkdir()
    shutil.copyfile(FORMAL / 'freeze.json', REPLAY / 'freeze.json')
    runner.OUT = REPLAY
    runner.prepare()
    for name in ['signals.parquet', 'native_channel.parquet', 'science_acceptance.json', 'prepared.json']:
        assert sha(FORMAL / name) == sha(REPLAY / name), name
    for year in range(2021, 2026):
        (REPLAY / str(year)).mkdir()
        # These are consumed review inputs to reproduction, not newly authored reviews.
        for name in ['baseline_review.json', 'review.json']:
            shutil.copyfile(FORMAL / str(year) / name, REPLAY / str(year) / name)
        runner.annual(year, True)
        runner.annual(year, False)
    reporter.OUT = REPLAY
    reporter.main()
    checks = []
    for p in sorted(REPLAY.rglob('*')):
        if not p.is_file() or p.name in ['freeze.json', 'baseline_review.json', 'review.json']:
            continue
        relative = p.relative_to(REPLAY)
        expected = FORMAL / relative
        assert expected.exists(), str(relative)
        same = sha(p) == sha(expected)
        checks.append({'path': str(relative), 'sha256': sha(p), 'identical': same})
        assert same, str(relative)
    signals = pd.read_parquet(FORMAL / 'signals.parquet')
    keep = signals.year.to_numpy() >= 2021
    opens = signals.open.to_numpy()
    price_move = np.r_[0., np.log(opens[1:] / opens[:-1])]
    errors = []
    for policy in runner.POLICIES:
        q = signals[policy].to_numpy()
        assert np.isin(q, [-1, 0, 1]).all()
        executed = np.r_[0, 0, q[:-2]]
        filled = np.r_[0, q[:-1]]
        turnover = abs(np.diff(np.r_[0, filled]))
        gross = (executed * price_move)[keep]
        net = gross + turnover[keep] * np.log1p(-runner.SIDE_FEE)
        bars = pd.concat([pd.read_parquet(FORMAL / str(y) / 'accounts' / (policy + '.parquet'))
                          for y in range(2021, 2026)], ignore_index=True)
        assert np.array_equal(gross, bars.gross_log.to_numpy())
        assert np.array_equal(net, bars.net_log.to_numpy())
        assert np.array_equal(turnover[keep], bars.turnover_sides.to_numpy())
        nav = np.exp(net.cumsum())
        peak = np.maximum.accumulate(np.r_[1., nav])[1:]
        error = float(np.max(abs(nav - bars.net_nav.to_numpy())))
        assert error < 1e-10
        assert np.max(abs((1 - nav / peak) - bars.net_drawdown.to_numpy())) < 1e-12
        errors.append({'policy': policy, 'independent_cumulative_nav_max_error': error})
    base = pd.read_csv(FORMAL / 'comparison.csv')
    f = base.loc[(base.policy == 'F') & (base.basis == 'original_zero_cost')].iloc[0]
    assert abs(f.cagr - .8675662509083047) < 1e-12
    assert abs(f.mdd - .14323804733417234) < 1e-12
    tests = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=ROOT, capture_output=True, text=True)
    assert tests.returncode == 0, tests.stdout + tests.stderr
    runner.save(FORMAL / 'validation.json', {'same_source_fresh_input_and_account_state_replay': True,
        'source_frozen_and_original_baseline_passed': True,
        'files_identical': len(checks), 'checks': checks,
        'independent_account_equation_checks': errors,
        'test_command': [sys.executable, '-m', 'pytest', '-q'],
        'test_exit_code': tests.returncode, 'test_stdout': tests.stdout,
        'replay_source_sha256': sha(Path(__file__)),
        'report_source_sha256': sha(ROOT / 'scripts/report_three_proposals_v1.py'),
        'actual_etf_option_execution_validated': False,
        'fresh_oos': False, 'production_authority': False})
    print('PASS:', len(checks), 'byte-identical artifacts; original baseline and account equations.')
    print(tests.stdout.strip())


if __name__ == '__main__':
    main()
