from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("signed_risk_asymmetry_v1", HERE / "run_study.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def frame(values):
    return pd.DataFrame({"symbol": ["000688.SH"] * len(values), "r": values})


def test_exact_frozen_coordinates_use_previous_12_only():
    hist = np.array([-4.0, 3.0, -2.0, 1.0, 5.0, -6.0, 2.5, -1.5, 4.5, -3.5, 0.5, 7.0])
    q = mod.attach_asymmetry_history(frame(np.r_[hist, 999.0]))
    row = q.iloc[-1]
    energy = np.sum(hist * np.abs(hist)) / np.sum(hist * hist)
    signed_abs = np.sum(hist) / np.sum(np.abs(hist))
    l1l2 = np.sum(np.abs(hist)) / (np.sqrt(12.0) * np.sqrt(np.sum(hist * hist)))
    maxl2 = np.max(np.abs(hist)) / np.sqrt(np.sum(hist * hist))
    np.testing.assert_allclose(row.sei12, energy, rtol=0, atol=1e-15)
    np.testing.assert_allclose(row.sai12, signed_abs, rtol=0, atol=1e-15)
    np.testing.assert_allclose(row.l1l2_12, l1l2, rtol=0, atol=1e-15)
    np.testing.assert_allclose(row.maxl2_12, maxl2, rtol=0, atol=1e-15)
    assert bool(row.asymmetry_available)


def test_current_final_return_cannot_change_current_features():
    values = np.arange(1.0, 16.0)
    a = mod.attach_asymmetry_history(frame(values))
    changed = values.copy()
    changed[-1] = -1_000_000.0
    b = mod.attach_asymmetry_history(frame(changed))
    cols = ["sei12", "sai12", "l1l2_12", "maxl2_12"]
    np.testing.assert_allclose(a.loc[a.index[-1], cols].astype(float), b.loc[b.index[-1], cols].astype(float), rtol=0, atol=0)


def test_sign_flip_flips_signed_coordinates_only():
    values = np.array([-7.0, 1.0, 4.0, -2.0, 3.0, -8.0, 6.0, 2.0, -1.0, 5.0, -4.0, 9.0, 0.25])
    a = mod.attach_asymmetry_history(frame(values)).iloc[-1]
    b = mod.attach_asymmetry_history(frame(-values)).iloc[-1]
    np.testing.assert_allclose([b.sei12, b.sai12], [-a.sei12, -a.sai12], rtol=0, atol=1e-15)
    np.testing.assert_allclose([b.l1l2_12, b.maxl2_12], [a.l1l2_12, a.maxl2_12], rtol=0, atol=1e-15)


def test_future_append_does_not_change_prefix_features():
    base = np.array([(-1.0) ** i * (i + 1.0) for i in range(25)])
    a = mod.attach_asymmetry_history(frame(base))
    b = mod.attach_asymmetry_history(frame(np.r_[base, 100.0, -200.0, 300.0]))
    cols = ["sei12", "sai12", "l1l2_12", "maxl2_12"]
    np.testing.assert_allclose(a[cols].to_numpy(float), b.iloc[: len(a)][cols].to_numpy(float), rtol=0, atol=0, equal_nan=True)


def test_missing_return_is_skipped_not_zero_filled():
    previous_valid = np.array([1.0, -2.0, 3.0, -4.0, 5.0, -6.0, 7.0, -8.0, 9.0, -10.0, 11.0, -12.0])
    values = np.r_[previous_valid[:5], np.nan, previous_valid[5:], 77.0]
    q = mod.attach_asymmetry_history(frame(values))
    row = q.iloc[-1]
    expected = np.sum(previous_valid * np.abs(previous_valid)) / np.sum(previous_valid * previous_valid)
    np.testing.assert_allclose(row.sei12, expected, rtol=0, atol=1e-15)
    assert bool(row.asymmetry_available)


def test_A_and_M_are_exactly_complexity_matched(monkeypatch):
    def fake_design(q, model):
        assert model == "C"
        return np.zeros((len(q), 84), dtype=float), [f"c{i}" for i in range(84)]

    monkeypatch.setattr(mod.parent, "design", fake_design)
    q = pd.DataFrame({
        "previous_state": ["NORMAL", "UNSAFE", "RECOVERING"],
        "sei12": [-0.5, 0.1, 0.7],
        "sai12": [-0.2, 0.0, 0.4],
        "l1l2_12": [0.7, 0.8, 0.9],
        "maxl2_12": [0.4, 0.5, 0.6],
    })
    c, cn = mod.design(q, "C")
    a, an = mod.design(q, "A")
    m, mn = mod.design(q, "M")
    assert c.shape == (3, 84)
    assert a.shape == m.shape == (3, 104)
    assert len(an) == len(mn) == 104
    assert an[:84] == mn[:84] == cn
    assert len(an[84:]) == len(mn[84:]) == 20
