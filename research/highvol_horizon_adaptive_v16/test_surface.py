from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
RUNNER=HERE/'run_surface.py'
PROTOCOL=HERE/'PROTOCOL.md'


def load_runner():
    spec=importlib.util.spec_from_file_location('v16_surface',RUNNER)
    assert spec is not None and spec.loader is not None
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def test_frozen_dimensions_and_lineage():
    m=load_runner()
    assert m.DEV_YEARS==(2021,2022,2023)
    assert m.HORIZONS==(15,30,60)
    assert m.STATES==('UNSAFE','RECOVERING')
    assert m.BUCKETS==('LT15','M15_25','M30_40','GE45')
    assert m.EXPECTED_ROWS==7327
    assert m.V15_RUNNER_BLOB=='5d29be64bb797dcd21388e2455b670127e0de81b'
    assert m.V15_RECEIPT_BLOB=='f430de0a4820c951af0b9153e3e81a0e355de3d8'


def test_projection_is_backward_only_and_monotone():
    m=load_runner()
    raw15=np.array([0.2,0.8,0.9])
    raw30=np.array([0.4,0.7,0.95])
    age60=np.array([0.9,0.6,0.8])
    p15,p30,p60=m.project(raw15,raw30,age60)
    assert np.all(p15<=p30)
    assert np.all(p30<=p60)
    assert np.all(p15<=raw15)
    assert np.all(p30<=raw30)
    assert np.allclose(p60,age60)


def test_protocol_fixes_horizon_roles():
    text=PROTOCOL.read_text()
    assert '`p60 = raw_age_only_60`' in text
    assert '`p30 = min(raw_state_age_30, p60)`' in text
    assert '`p15 = min(raw_state_age_15, p30)`' in text
    assert 'no PnL, payoff, routing or trading rule is created' in text
    assert 'Validation and BlackBox are not queried' in text
