import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parent/'run_validation.py'
def load():
    s=importlib.util.spec_from_file_location('v10val',P); assert s and s.loader
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_fixed_validation_boundary():
    m=load(); assert m.VAL_YEARS==(2024,2025); assert m.REF_YEARS==(2020,2021,2022,2023,2024,2025)

def test_primary_lead_is_frozen_15s():
    m=load(); assert m.LEADS==(60,30,15,6,3); assert m.PRIMARY_LEAD==15

def test_frozen_v10_blob():
    assert load().FROZEN_V10_BLOB=='783b5bb474758956b7b86a0e8c72a1264ab2e1e5'
