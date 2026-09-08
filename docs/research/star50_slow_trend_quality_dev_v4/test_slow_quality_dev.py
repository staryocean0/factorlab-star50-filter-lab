from __future__ import annotations
import importlib.util
from pathlib import Path

MOD=Path(__file__).resolve().parent/'run_slow_quality_dev.py'
s=importlib.util.spec_from_file_location('q',MOD);q=importlib.util.module_from_spec(s);s.loader.exec_module(q)


def test_dev_boundary_and_thresholds():
    assert q.START=='2021-01-01' and q.END=='2023-12-31'
    assert q.YEARS==(2021,2022,2023)
    assert q.EFF_THRESHOLDS==(0.20,0.40,0.60)


def test_fixed_bands():
    assert q.EFF_LABELS==('eff_lt_0.20','eff_0.20_0.40','eff_0.40_0.60','eff_ge_0.60')
    assert q.UP_LABELS==('up_lt_0.55','up_0.55_0.60','up_0.60_0.65','up_ge_0.65')
