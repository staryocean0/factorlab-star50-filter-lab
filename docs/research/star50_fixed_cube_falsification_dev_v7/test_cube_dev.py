from __future__ import annotations
import importlib.util,itertools
from pathlib import Path
MOD=Path(__file__).resolve().parent/'run_cube_dev.py';s=importlib.util.spec_from_file_location('c',MOD);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def test_fixed_cube_has_exactly_16_cells():
 cells=list(itertools.product(('down','up'),(False,True),(False,True),(False,True)))
 assert len(cells)==16 and c.YEARS==(2021,2022,2023)
def test_nonoverlap_three_minute():
 import pandas as pd
 z=pd.DataFrame([{'session':'s','onset_row':40,'signed_3m_bp':1.},{'session':'s','onset_row':42,'signed_3m_bp':1.},{'session':'s','onset_row':44,'signed_3m_bp':1.}])
 q=c.nonoverlap(z,3);assert list(q.onset_row)==[40,44]
