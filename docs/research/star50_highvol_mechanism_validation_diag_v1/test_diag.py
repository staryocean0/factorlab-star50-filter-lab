from __future__ import annotations
import importlib.util
from pathlib import Path
MOD=Path(__file__).resolve().parent/'run_diag.py';s=importlib.util.spec_from_file_location('m',MOD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def test_validation_horizon_fixed():
    assert m.START=='2024-01-01' and m.END=='2026-08-21' and m.YEARS==(2024,2025,2026)

def test_no_candidate_menu_in_diag():
    assert m.HORIZONS==(1,2,3,5,10)
