from pathlib import Path
import importlib.util

def test_v10_boundaries():
    p=Path(__file__).parent/'run_cross_state.py'
    s=importlib.util.spec_from_file_location('v10',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    assert m.START=='2021-01-01'
    assert m.END=='2023-12-31'
