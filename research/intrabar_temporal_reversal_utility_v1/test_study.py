from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("intrabar_temporal_study", HERE / "run_study.py")
study = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(study)


def sample_returns() -> np.ndarray:
    return np.array([3, -1, 2, -4, 1, 5, -2, 2, -3, 4, 1, -1, 3, -2, 5, -4, 2, 1, -3], dtype=float)


def test_protocol_and_parent_are_pinned():
    assert study.git_blob_bytes((HERE / "PROTOCOL.md").read_bytes()) == study.PROTOCOL_BLOB
    assert study.git_blob_bytes(study.PARENT_PATH.read_bytes()) == study.PARENT_BLOB
    assert study.INTRABAR_RETURNS == 19
    assert study.MODELS == ("C", "T", "O")


def test_temporal_coordinates_global_sign_invariant():
    r = sample_returns()
    a = study.temporal_coordinates(r, 0.001)
    b = study.temporal_coordinates(-r, 0.001)
    assert a is not None and b is not None
    for key in ("arf19", "lac19", "frms19", "npe19"):
        assert np.isclose(a[key], b[key], rtol=0, atol=1e-15)


def test_order_invariant_control_survives_permutation_but_temporal_block_changes():
    r = sample_returns()
    a = study.temporal_coordinates(r, 0.001)
    b = study.temporal_coordinates(np.sort(r), 0.001)
    assert a is not None and b is not None
    assert np.isclose(a["frms19"], b["frms19"], rtol=0, atol=1e-15)
    assert np.isclose(a["npe19"], b["npe19"], rtol=0, atol=1e-15)
    assert not (
        np.isclose(a["arf19"], b["arf19"], rtol=0, atol=1e-12)
        and np.isclose(a["lac19"], b["lac19"], rtol=0, atol=1e-12)
    )


def test_invalid_or_degenerate_paths_fail_closed():
    assert study.temporal_coordinates(np.ones(18), 0.001) is None
    assert study.temporal_coordinates(np.zeros(19), 0.001) is None
    assert study.temporal_coordinates(sample_returns(), 0.0) is None
    r = sample_returns()
    r[5] = np.nan
    assert study.temporal_coordinates(r, 0.001) is None


def test_equal_complexity_design(monkeypatch):
    n = 7
    fake_names = [f"c{i}" for i in range(84)]

    def fake_parent_design(q, model):
        assert model == "C"
        return np.ones((len(q), 84), dtype=float), fake_names

    monkeypatch.setattr(study.parent, "design", fake_parent_design)
    q = pd.DataFrame(
        {
            "arf19": np.linspace(0.1, 0.7, n),
            "lac19": np.linspace(-0.6, 0.5, n),
            "frms19": np.linspace(0.2, 0.8, n),
            "npe19": np.linspace(0.15, 0.75, n),
            "previous_state": ["NORMAL", "UNSAFE", "RECOVERING", "NORMAL", "UNSAFE", "RECOVERING", "NORMAL"],
        }
    )
    c, cn = study.design(q, "C")
    t, tn = study.design(q, "T")
    o, on = study.design(q, "O")
    assert c.shape == (n, 84)
    assert t.shape == o.shape == (n, 104)
    assert tn[:84] == on[:84] == cn
    assert len(tn) - len(cn) == len(on) - len(cn) == 20


def test_invariant_self_check():
    out = study.invariant_checks()
    assert out["global_sign_invariant"] is True
    assert out["control_permutation_invariant"] is True
    assert out["temporal_block_order_sensitive"] is True
    assert out["current_bar_returns"] == 19
