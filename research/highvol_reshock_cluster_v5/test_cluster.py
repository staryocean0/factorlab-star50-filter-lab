from __future__ import annotations

import importlib.util
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent
RUNNER=HERE/'run_cluster.py'


def load_mod():
    spec=importlib.util.spec_from_file_location('cluster_v5',RUNNER); mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod); return mod


def test_frozen_horizons():
    m=load_mod(); assert m.DEV_YEARS==(2021,2022,2023); assert m.NORMAL_HORIZONS==(3,6,12); assert m.RESH_HORIZONS==(3,6)


def test_anchor_outcome_excludes_anchor_shock():
    m=load_mod(); day=pd.DataFrame({'risk_state':['UNSAFE','UNSAFE','RECOVERING','NORMAL'],'shock':[True,False,False,False]})
    support,val=m.outcome(day,0,3,3,'reshock'); assert support is True and val is False


def test_anchor_outcome_detects_next_shock():
    m=load_mod(); day=pd.DataFrame({'risk_state':['UNSAFE','UNSAFE','RECOVERING','NORMAL'],'shock':[True,True,False,False]})
    support,val=m.outcome(day,0,3,3,'reshock'); assert support is True and val is True
