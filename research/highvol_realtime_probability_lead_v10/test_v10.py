import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parent/'run_v10.py'
def load():
    s=importlib.util.spec_from_file_location('v10',P); assert s and s.loader
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_fixed_leads_and_primary():
    m=load(); assert m.LEADS==(60,30,15,6,3); assert m.PRIMARY_LEAD==15

def test_development_boundary():
    m=load(); assert m.REF_YEARS==(2020,2021,2022,2023); assert m.DEV_YEARS==(2021,2022,2023)

def test_frozen_v9_blob():
    assert load().FROZEN_V9_BLOB=='ae2a7e095df58692ef9df0dfee5856cac727ca44'
