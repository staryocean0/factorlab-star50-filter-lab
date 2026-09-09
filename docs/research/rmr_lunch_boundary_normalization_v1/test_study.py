import importlib.util
from pathlib import Path
import pandas as pd
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('study',HERE/'run_study.py'); study=importlib.util.module_from_spec(spec); spec.loader.exec_module(study)

def test_band_edges():
    assert study.band(0.5)=='low'
    assert study.band(1.0)=='low'
    assert study.band(1.5)=='mid'
    assert study.band(2.5)=='high'

def test_synthetic_lunch_normalization_can_pass():
    rows=[]
    for s in study.SYMBOLS:
        for y in study.YEARS:
            for d in ('UP','DOWN'):
                for _ in range(25):
                    rows.append({'symbol':s,'year':y,'Z':1.5,'band':'mid','gap_direction':d,
                                 'signed_F5_bp':-4.0,'signed_F15_bp':-5.0,'reversal5':True,'recovery_fraction_5':0.2})
            for _ in range(100):
                rows.append({'symbol':s,'year':y,'Z':0.5,'band':'low','gap_direction':'UP',
                             'signed_F5_bp':1.0,'signed_F15_bp':1.5,'reversal5':False,'recovery_fraction_5':-0.1})
    _,_,decision=study.summarize(pd.DataFrame(rows))
    assert decision['verdict']=='broad_signal_source_supported'
