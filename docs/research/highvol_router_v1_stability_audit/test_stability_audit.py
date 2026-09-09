from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_stability_audit.py"
DEV_RUNNER = HERE.parent / "highvol_router_v1_dev" / "run_router_dev.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_audit_menu_is_fixed():
    m = load(RUNNER, "audit_menu")
    assert m.COSTS == (0.5, 1.0, 1.5, 2.0)
    assert m.BOOTSTRAP_DRAWS == 10_000
    assert m.BOOTSTRAP_SEED == 20260909
    assert m.PRIMARY_COST == 1.0


def test_frozen_candidate_identity_remains_exact():
    dev = load(DEV_RUNNER, "dev_identity")
    assert dev.FROZEN == {
        "highvol_ratio_min": 1.5,
        "highvol_fast_window_min": 5,
        "highvol_background_window_min": 30,
        "highvol_background_floor_bp": 1.0,
        "slow_window_min": 30,
        "tail2_share_min": 0.60,
        "tail1_share_max_exclusive": 0.60,
        "hold_min": 3,
        "cost_bp_per_leg": 1.0,
    }


def test_audit_source_has_no_candidate_threshold_menu():
    text = RUNNER.read_text()
    assert "tail2_share_min" not in text
    assert "tail1_share_max_exclusive" not in text
    assert "highvol_ratio_min" not in text
    assert "frozen_qualifying" in text
    assert "apply_nonoverlap" in text


def test_protocol_forbids_blackbox_and_candidate_change():
    text = (HERE / "PROTOCOL.md").read_text()
    assert "does not query BlackBox-V1" in text
    assert "cannot change the router" in text
    assert "creates no new candidate" in text
