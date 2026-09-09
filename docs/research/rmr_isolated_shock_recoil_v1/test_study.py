import importlib.util
from pathlib import Path
import pandas as pd
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('study',HERE/'run_study.py'); study=importlib.util.module_from_spec(spec); spec.loader.exec_module(study)

def test_synthetic_recoil_can_pass():
    rows=[]
    for s in study.SYMBOLS:
        for y in study.YEARS:
            for d in ('UP','DOWN'):
                for _ in range(25):
                    rows.append({'symbol':s,'year':y,'shock_direction':d,'signed_F5_bp':-5.0,'reversal5':True,
                                 'recovery_fraction_5':0.2,'recovery50_5':False,'signed_F1_bp':-1.0,'signed_F3_bp':-3.0,'signed_F15_bp':-6.0})
    _,_,decision=study.summarize(pd.DataFrame(rows))
    assert decision['verdict']=='broad_signal_source_supported'
