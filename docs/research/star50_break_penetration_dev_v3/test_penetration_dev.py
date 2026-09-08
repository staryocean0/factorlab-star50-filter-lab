from __future__ import annotations
import importlib.util
from pathlib import Path

MOD=Path(__file__).resolve().parent/'run_penetration_dev.py'
s=importlib.util.spec_from_file_location('p',MOD);p=importlib.util.module_from_spec(s);s.loader.exec_module(p)


def test_development_boundary_and_thresholds_fixed():
    assert p.START=='2021-01-01' and p.END=='2023-12-31'
    assert p.YEARS==(2021,2022,2023)
    assert p.THRESHOLDS==(0.50,1.00,2.00)


def test_penetration_bands_are_economic_not_percentiles():
    assert p.LABELS==('lt_0.25','0.25_0.50','0.50_1.00','1.00_2.00','ge_2.00')


def test_nonoverlap_uses_three_minute_hold():
    import pandas as pd
    z=pd.DataFrame([
      {'session':'s','onset_row':40,'signed_3m_bp':1.0},
      {'session':'s','onset_row':42,'signed_3m_bp':2.0},
      {'session':'s','onset_row':44,'signed_3m_bp':3.0},
    ])
    q=p.nonoverlap(z,3)
    assert list(q.onset_row)==[40,44]
