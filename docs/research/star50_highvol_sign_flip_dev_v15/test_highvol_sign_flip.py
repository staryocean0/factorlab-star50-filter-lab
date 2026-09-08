from pathlib import Path
import importlib.util

def load_module():
    p=Path(__file__).parent/'run_highvol_sign_flip.py'; s=importlib.util.spec_from_file_location('v15',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_v15_fixed_design():
    m=load_module()
    assert m.START=='2021-01-01' and m.END=='2023-12-31'
    assert m.YEARS==(2021,2022,2023) and m.SYMBOL=='000688.SH'
    assert m.VIEWS==('all','UpToDown','DownToUp')
