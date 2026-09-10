from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUNNER=HERE/"run_validation.py"
FROZEN=HERE/"FROZEN_RISK_OBJECT_V9.json"

def load():
    spec=importlib.util.spec_from_file_location("v9val",RUNNER); assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def test_boundary_and_primary_checkpoint_are_frozen():
    mod=load(); assert mod.VAL_YEARS==(2024,2025); assert mod.REF_YEARS==(2020,2021,2022,2023,2024,2025); assert mod.SYMBOLS==("000688.SH","000852.SH")

def test_frozen_development_authority():
    f=json.loads(FROZEN.read_text()); assert f["source_commit"]=="e01b293dcfc3100a02265315376bc63a9137c3d3"; assert f["development_run_id"]==34443013548; assert f["development_artifact_id"]==10138625380

def test_no_fit_tuning_or_trading():
    f=json.loads(FROZEN.read_text()); assert f["probability_fit_performed"] is False; assert f["threshold_search_performed"] is False; assert f["pnl_computed"] is False; assert f["trading_rule_created"] is False; assert f["production_authority"] is False

def test_acceptance_is_same_as_development():
    f=json.loads(FROZEN.read_text()); assert f["acceptance"]=={"pooled_coverage_min":0.98,"annual_coverage_min":0.95,"pooled_probability_mae_max":0.01,"pooled_brier_degradation_max":0.002,"annual_brier_degradation_max":0.005}
