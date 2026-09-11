from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent


def load_mod():
    spec = importlib.util.spec_from_file_location("v19", HERE / "run_v19.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_close_confirmed_exit_hysteresis():
    m = load_mod()
    assert m.machine_e15_state("UNSAFE", "NORMAL") == "UNSAFE"
    assert m.machine_e15_state("RECOVERING", "NORMAL") == "RECOVERING"
    assert m.machine_e15_state("NORMAL", "NORMAL") == "NORMAL"
    assert m.machine_e15_state("NORMAL", "UNSAFE") == "UNSAFE"
    assert m.machine_e15_state("RECOVERING", "UNSAFE") == "UNSAFE"


def test_reference_has_same_exit_semantics():
    m = load_mod()
    assert m.reference_e15_state("UNSAFE", "NORMAL") == "UNSAFE"
    assert m.reference_e15_state("RECOVERING", "NORMAL") == "RECOVERING"
    assert m.reference_e15_state("NORMAL", "UNSAFE") == "UNSAFE"
    assert m.reference_e15_state("UNSAFE", "RECOVERING") == "RECOVERING"


def test_transition_classes_and_frozen_checkpoint():
    m = load_mod()
    assert m.PRIMARY_LEAD_SECONDS == 15
    assert m.DEV_YEARS == (2021, 2022, 2023)
    assert m.transition_class("NORMAL", "UNSAFE") == "SWITCH_ON"
    assert m.transition_class("RECOVERING", "UNSAFE") == "REESCALATE"
    assert m.transition_class("UNSAFE", "RECOVERING") == "UNSAFE_TO_RECOVERING"
    assert m.transition_class("UNSAFE", "NORMAL") == "EXIT_FROM_UNSAFE"
