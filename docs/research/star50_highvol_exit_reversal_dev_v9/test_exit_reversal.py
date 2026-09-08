from __future__ import annotations
import importlib.util
from pathlib import Path
MOD=Path(__file__).resolve().parent/'run_exit_reversal.py'
s=importlib.util.spec_from_file_location('x',MOD);x=importlib.util.module_from_spec(s);s.loader.exec_module(x)

def test_bounds_and_run_bands():
    assert x.START=='2021-01-01' and x.END=='2023-12-31' and x.YEARS==(2021,2022,2023)
    assert x.RUN_BANDS==('run_1','run_2_3','run_4_6','run_ge_7')

def test_run_band_mapping():
    assert x.run_band(1)=='run_1'
    assert x.run_band(2)==x.run_band(3)=='run_2_3'
    assert x.run_band(4)==x.run_band(6)=='run_4_6'
    assert x.run_band(7)==x.run_band(20)=='run_ge_7'
