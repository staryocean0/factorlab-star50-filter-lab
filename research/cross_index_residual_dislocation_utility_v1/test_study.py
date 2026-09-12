from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("study", HERE / "run_study.py")
study = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(study)


def synthetic():
    x = np.linspace(-0.012, 0.014, study.REL_WINDOW)
    noise = 0.0012 * np.sin(np.arange(study.REL_WINDOW) * 0.73)
    y = 0.0004 + 1.35 * x + noise
    return y, x


def test_relationship_global_sign_invariance():
    y, x = synthetic()
    a = study.relationship_metrics(y, x, 0.006, 0.003)
    b = study.relationship_metrics(-y, -x, -0.006, -0.003)
    assert a is not None and b is not None
    assert np.isclose(a["RZ48"], b["RZ48"], rtol=0, atol=1e-12)
    assert np.isclose(a["QZ48"], b["QZ48"], rtol=0, atol=1e-12)
    assert np.isclose(a["beta"], b["beta"], rtol=0, atol=1e-12)
    assert np.isclose(a["alpha"], -b["alpha"], rtol=0, atol=1e-12)


def test_relationship_uses_exact_frozen_window():
    y, x = synthetic()
    assert study.relationship_metrics(y[:-1], x[:-1], 0.006, 0.003) is None
    m = study.relationship_metrics(y, x, 0.006, 0.003)
    assert m is not None
    assert m["RZ48"] >= 0 and m["QZ48"] >= 0


def test_degenerate_other_history_is_unavailable():
    y = np.linspace(-0.01, 0.01, study.REL_WINDOW)
    x = np.zeros(study.REL_WINDOW)
    assert study.relationship_metrics(y, x, 0.001, 0.0) is None


def test_r_q_scalar_blocks_are_schema_identical():
    q = pd.DataFrame({
        "previous_state": ["NORMAL", "UNSAFE", "RECOVERING", "NORMAL"],
        "RZ48": [0.1, 0.5, 1.0, 2.0],
        "QZ48": [0.2, 0.6, 1.1, 2.1],
    })
    r, rn = study.severity_block(q, "RZ48")
    c, cn = study.severity_block(q, "QZ48")
    assert r.shape == c.shape == (4, 8)
    assert rn == cn
    assert len(rn) == 8
    assert np.isfinite(r).all() and np.isfinite(c).all()


def test_scalar_block_rejects_negative_severity():
    q = pd.DataFrame({
        "previous_state": ["NORMAL"],
        "RZ48": [-0.1],
    })
    try:
        study.severity_block(q, "RZ48")
    except ValueError:
        return
    raise AssertionError("negative severity must fail closed")
