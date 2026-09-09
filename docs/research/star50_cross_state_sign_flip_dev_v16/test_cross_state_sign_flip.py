from pathlib import Path
import importlib.util


def load_module():
    p=Path(__file__).parent/'run_cross_state_sign_flip.py'
    s=importlib.util.spec_from_file_location('v16',p)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_v16_fixed_design():
    m=load_module()
    assert m.START=='2021-01-01' and m.END=='2023-12-31'
    assert m.YEARS==(2021,2022,2023)
    assert m.STAR=='000688.SH' and m.CSI=='000852.SH'
    assert m.VIEWS==('all','CSIHighVol','CSINormalVol')
