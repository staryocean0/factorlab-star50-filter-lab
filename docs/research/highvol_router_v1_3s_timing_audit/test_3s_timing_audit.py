from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_3s_timing_audit.py"
DEV_RUNNER = HERE.parent / "highvol_router_v1_dev" / "run_router_dev.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_fixed_delay_menu_and_year_roles():
    m = load(RUNNER, "timing_menu")
    assert m.DELAYS_SEC == (0, 3, 6, 15)
    assert m.DEV_YEARS == (2021, 2022, 2023)
    assert m.VAL_YEARS == (2024, 2025)
    assert 2026 not in m.YEARS


def test_exact_frozen_trade_counts_are_guarded():
    m = load(RUNNER, "timing_counts")
    assert m.EXPECTED_TRADES == {2021: 37, 2022: 31, 2023: 36, 2024: 58, 2025: 49}


def test_frozen_router_identity_is_not_redefined():
    dev = load(DEV_RUNNER, "frozen_dev")
    assert dev.FROZEN["highvol_ratio_min"] == 1.5
    assert dev.FROZEN["slow_window_min"] == 30
    assert dev.FROZEN["tail2_share_min"] == 0.60
    assert dev.FROZEN["tail1_share_max_exclusive"] == 0.60
    assert dev.FROZEN["hold_min"] == 3


def test_protocol_denies_fill_claim_and_blackbox():
    text = (HERE / "PROTOCOL.md").read_text()
    assert "not a tradable fill study" in text
    assert "BlackBox-V1 is not queried" in text
    assert "no interpolation" in text.lower()
    assert "2026 is **not** part of this audit" in text
