from pathlib import Path
import importlib.util


def load_module():
    p=Path(__file__).parent/'run_price_impact_liquidity.py'
    s=importlib.util.spec_from_file_location('v13',p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def test_v13_fixed_design():
    m=load_module()
    assert m.START=='2021-01-01' and m.END=='2023-12-31'
    assert m.YEARS==(2021,2022,2023)
    assert m.SYMBOL=='000688.SH'
    assert m.IMPACT_THRESHOLD==1.0
    assert m.VIEWS==('all','ImpactAmplified','ImpactDamped')
