from pathlib import Path
import importlib.util


def load_module():
    p=Path(__file__).parent/'run_turnover_pressure.py'
    s=importlib.util.spec_from_file_location('v12',p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def test_v12_fixed_design():
    m=load_module()
    assert m.START=='2021-01-01' and m.END=='2023-12-31'
    assert m.YEARS==(2021,2022,2023)
    assert m.SYMBOL=='000688.SH'
    assert m.ACTIVITY_FIELD=='amount'
    assert m.VIEWS==('all','TurnoverSupported','TurnoverOpposed')
