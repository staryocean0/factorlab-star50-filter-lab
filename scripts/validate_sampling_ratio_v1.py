"""Repeat only the sampling diagnostic in disposable output; preserve originals."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile

import study_sampling_ratio_v1 as study

ROOT=Path(__file__).resolve().parents[1]
FORMAL=study.OUT


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


names=['response.csv','common_5m_grid.parquet','signal_diagnostics.csv','alignment.csv',
       'slope_identity.json','comparison.png']
expected={n:sha(FORMAL/n) for n in names}
usage=json.loads((FORMAL/'data_usage.json').read_text())
assert usage['source_sha256']==sha(ROOT/'scripts/study_sampling_ratio_v1.py')
for n,h in usage['dependency_hashes'].items():assert sha(ROOT/n)==h
with tempfile.TemporaryDirectory(prefix='star50_sampling_repeat_') as temporary:
    study.OUT=Path(temporary)
    with contextlib.redirect_stdout(io.StringIO()):study.main()
    assert all(sha(study.OUT/n)==h for n,h in expected.items())
result={'six_diagnostic_files_byte_identical':True,'file_hashes':expected,
        'no_financial_backtest':True,'actual_seconds_data_tested':False,
        'validator_sha256':sha(Path(__file__))}
target=FORMAL/'repeat_validation.json'
if target.exists():assert json.loads(target.read_text())==result
else:target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS: six diagnostic files byte-identical; original files unchanged.')
