from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

MOD = Path(__file__).resolve().parent / 'run_dev.py'
SPEC = importlib.util.spec_from_file_location('star50_v2_dev', MOD)
DEV = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(DEV)


def test_frozen_dates_and_hold():
    assert DEV.START == '2021-01-01'
    assert DEV.END == '2023-12-31'
    assert DEV.YEARS == (2021, 2022, 2023)
    assert DEV.HOLD_MIN == 3


def test_selector_is_accelerated_downside_not_old_v1():
    rows = pd.DataFrame([
        {'direction':'down','slow30_net_bp':1,'net5_bp':-1,'efficiency5':.60,'tail2_share':.50,'signed_3m_bp':2,'session':'a','onset_row':40},
        {'direction':'down','slow30_net_bp':1,'net5_bp':-1,'efficiency5':.60,'tail2_share':.49,'signed_3m_bp':2,'session':'b','onset_row':40},
        {'direction':'down','slow30_net_bp':1,'net5_bp':-1,'efficiency5':.59,'tail2_share':.80,'signed_3m_bp':2,'session':'c','onset_row':40},
        {'direction':'down','slow30_net_bp':-1,'net5_bp':-1,'efficiency5':.80,'tail2_share':.80,'signed_3m_bp':2,'session':'d','onset_row':40},
    ])
    out = DEV.select(rows)
    assert len(out) == 1
    assert float(out.iloc[0]['tail2_share']) == .50


def test_two_leg_cost_and_break_even_math():
    z = pd.DataFrame({'gross_bp':[4.0, 2.0]})
    m = DEV.metrics(z)
    assert abs(m['mean_net_1bp_per_leg'] - 1.0) < 1e-12
    assert abs(m['one_way_break_even_bp'] - 1.5) < 1e-12


def test_non_overlap_project_convention():
    rows = pd.DataFrame([
        {'direction':'down','slow30_net_bp':1,'net5_bp':-1,'efficiency5':.8,'tail2_share':.8,'signed_3m_bp':1,'session':'a','onset_row':40},
        {'direction':'down','slow30_net_bp':1,'net5_bp':-1,'efficiency5':.8,'tail2_share':.8,'signed_3m_bp':1,'session':'a','onset_row':43},
        {'direction':'down','slow30_net_bp':1,'net5_bp':-1,'efficiency5':.8,'tail2_share':.8,'signed_3m_bp':1,'session':'a','onset_row':44},
    ])
    out = DEV.select(rows)
    assert list(out['onset_row']) == [40, 44]
