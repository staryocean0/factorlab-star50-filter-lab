from pathlib import Path
import importlib.util

def load_module():
    p=Path(__file__).parent/'run_intraday_phase.py'; s=importlib.util.spec_from_file_location('v14',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_v14_fixed_design():
    m=load_module()
    assert m.START=='2021-01-01' and m.END=='2023-12-31'
    assert m.YEARS==(2021,2022,2023) and m.SYMBOL=='000688.SH'
    assert m.PHASES==('early','middle','late')
    assert m.phase_of(35)=='early' and m.phase_of(60)=='early'
    assert m.phase_of(61)=='middle' and m.phase_of(90)=='middle'
    assert m.phase_of(91)=='late' and m.phase_of(120)=='late'
