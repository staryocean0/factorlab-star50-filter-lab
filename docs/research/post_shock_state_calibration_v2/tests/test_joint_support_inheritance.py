from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "docs/research/post_shock_state_calibration_v2/code/state_calibration_v2_joint_support.py"
SPEC = importlib.util.spec_from_file_location("state_calibration_v2_joint_tested", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


def test_archived_exact_universe_is_hash_bound_and_has_frozen_counts():
    universe, receipt = m._load_inherited_universe(ROOT)
    assert len(universe) == 77
    counts = universe.groupby("symbol").size().to_dict()
    assert counts == m.EXPECTED_COUNTS
    assert receipt["evaluation_event_counts"]["total"] == 77
    assert receipt["operational_support_semantics"]["event_minute_floor"] == 33


def test_event_id_matches_historical_anchor_format():
    assert m._event_id("000852.SH", "2025-01-22/0", 44) == "000852.SH/2025-01-22/0/44"
