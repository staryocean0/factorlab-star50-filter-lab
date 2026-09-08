from __future__ import annotations
import importlib.util
from pathlib import Path
MOD=Path(__file__).resolve().parent/'run_age_mechanism.py';s=importlib.util.spec_from_file_location('a',MOD);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
def test_fixed_boundaries_and_landmarks():
 assert a.START=='2021-01-01' and a.END=='2023-12-31' and a.YEARS==(2021,2022,2023)
 assert a.LANDMARKS=={1:'onset',2:'early_persist',4:'mature',7:'late'}
