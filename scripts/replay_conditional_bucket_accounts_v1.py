"""Independent process/output replay of the exact frozen account family."""
from pathlib import Path
import shutil
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_conditional_bucket_accounts_v1 as run

original=run.OUT
isolated=original/'isolated'
assert not isolated.exists(), 'Do not overwrite independent replay'
isolated.mkdir()
for name in ['source_freeze.json','frozen_signals.parquet','baseline_review.json']:
    shutil.copy2(original/name,isolated/name)
run.OUT=isolated
run.execute('family')
