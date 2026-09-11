import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_audit.py"


def load():
    spec = importlib.util.spec_from_file_location("audit", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixed_year_roles_and_leads():
    m = load()
    assert m.REF_YEARS == (2020, 2021, 2022, 2023, 2024, 2025)
    assert m.AUDIT_YEARS == (2021, 2022, 2023, 2024, 2025)
    assert m.LATER_LEADS == (6, 3)


def test_intensity_bands_are_frozen():
    m = load()
    assert m.intensity_band(2.49) == "LT2_5"
    assert m.intensity_band(2.5) == "M2_5_3_0"
    assert m.intensity_band(2.999) == "M2_5_3_0"
    assert m.intensity_band(3.0) == "M3_0_3_5"
    assert m.intensity_band(3.5) == "M3_5_4_0"
    assert m.intensity_band(4.0) == "GE4_0"


def test_frozen_identities():
    m = load()
    assert m.EXPECTED_V19_BLOB == "ee2fce299d5ee21abf1ab2c2c5183bac101ae822"
    assert m.EXPECTED_V9_BLOB == "ae2a7e095df58692ef9df0dfee5856cac727ca44"
    assert m.EXPECTED_V18_BLOB == "62c207badff1c3e37cbb1a8e17ef89feeea611d8"
    assert m.EXPECTED_V17_BLOB == "397d80037806ba11cadf7f77717d36d55fbafc91"
    assert m.EXPECTED_V16_BLOB == "1f88966cf5dd3fb102f0d75746d5d00434555647"
