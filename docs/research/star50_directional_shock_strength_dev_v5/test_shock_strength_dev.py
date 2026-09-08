from __future__ import annotations
import importlib.util
from pathlib import Path
MOD=Path(__file__).resolve().parent/'run_shock_strength_dev.py';s=importlib.util.spec_from_file_location('z',MOD);z=importlib.util.module_from_spec(s);s.loader.exec_module(z)
def test_bounds_and_thresholds():
 assert z.START=='2021-01-01' and z.END=='2023-12-31' and z.YEARS==(2021,2022,2023)
 assert z.Z_THRESHOLDS==(1.0,1.5,2.0,3.0)
