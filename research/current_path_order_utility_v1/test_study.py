from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("current_path_order_v1", HERE / "run_study.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def fixture_returns() -> np.ndarray:
    return np.array([
        1.0, -2.0, 3.0, 0.5, -1.5, 4.0, -3.0, 2.5, -0.5, 1.25,
        -2.75, 3.5, -1.0, 0.75, -4.5, 2.0, 1.5, -0.25, 5.0,
    ], dtype=float)


def test_path_coordinates_exact_and_bounded():
    r = fixture_returns()
    c = mod.path_coordinates(r)
    assert c is not None
    energy = np.sum(r * r)
    tv = np.sum(np.abs(r))
    cum = np.r_[0.0, np.cumsum(r)]
    np.testing.assert_allclose(c["l1l2_19"], tv / (np.sqrt(19.0) * np.sqrt(energy)), rtol=0, atol=1e-15)
    np.testing.assert_allclose(c["maxl2_19"], np.max(np.abs(r)) / np.sqrt(energy), rtol=0, atol=1e-15)
    np.testing.assert_allclose(c["rtv19"], (cum.max() - cum.min()) / tv, rtol=0, atol=1e-15)
    np.testing.assert_allclose(c["ap19"], np.sum(r[1:] * r[:-1]) / energy, rtol=0, atol=1e-15)
    assert 0 <= c["rtv19"] <= 1
    assert -1 <= c["ap19"] <= 1


def test_global_sign_flip_leaves_all_frozen_coordinates_unchanged():
    r = fixture_returns()
    a = mod.path_coordinates(r)
    b = mod.path_coordinates(-r)
    assert a is not None and b is not None
    for key in ("l1l2_19", "maxl2_19", "rtv19", "ap19"):
        np.testing.assert_allclose(a[key], b[key], rtol=0, atol=1e-15)


def test_permutation_preserves_magnitude_net_and_rms_but_changes_order():
    r = fixture_returns()
    perm = np.r_[r[::2], r[1::2]]
    a = mod.path_coordinates(r)
    b = mod.path_coordinates(perm)
    assert a is not None and b is not None
    np.testing.assert_allclose(np.sum(r), np.sum(perm), rtol=0, atol=1e-15)
    np.testing.assert_allclose(np.sqrt(np.mean(r * r)), np.sqrt(np.mean(perm * perm)), rtol=0, atol=1e-15)
    np.testing.assert_allclose(a["l1l2_19"], b["l1l2_19"], rtol=0, atol=1e-15)
    np.testing.assert_allclose(a["maxl2_19"], b["maxl2_19"], rtol=0, atol=1e-15)
    assert abs(a["rtv19"] - b["rtv19"]) > 1e-6 or abs(a["ap19"] - b["ap19"]) > 1e-6


def test_wrong_length_or_zero_energy_is_unavailable():
    assert mod.path_coordinates(np.ones(18)) is None
    assert mod.path_coordinates(np.ones(20)) is None
    assert mod.path_coordinates(np.zeros(19)) is None


def _fake_source_day() -> pd.DataFrame:
    return pd.DataFrame({
        "trading_day": ["2023-01-03"],
        "obs_dt": [pd.Timestamp("2023-01-03 09:30:00")],
        "price": [100.0],
        "row_index": [0],
    })


def _one_bar() -> pd.DataFrame:
    return pd.DataFrame({
        "symbol": ["000688.SH"],
        "trading_day": ["2023-01-03"],
        "year": [2023],
        "afternoon": [0],
        "slot": [575],
        "bar_end": [pd.Timestamp("2023-01-03 09:35:00")],
        "row_id": [0],
    })


def test_final_15_seconds_cannot_change_current_E15_path(monkeypatch):
    base_r = np.full(481, np.nan)
    base_r[1:20] = fixture_returns()
    base_r[20] = 999.0  # 09:34:45 -> 09:35:00 final 15 seconds, after E15.
    price = np.full(481, 100.0)
    age = np.zeros(481)
    second = np.arange(0, 7201, 15)

    monkeypatch.setattr(mod.parent, "load_3s", lambda root, symbol, year: _fake_source_day().copy())

    def sample_a(*args, **kwargs):
        return {"second": second, "price": price, "return_bp": base_r.copy(), "age": age}

    monkeypatch.setattr(mod.parent, "sample_session", sample_a)
    a = mod.build_fine_order_e15(Path("."), _one_bar(), (2023,)).iloc[0]

    changed = base_r.copy()
    changed[20] = -1_000_000.0

    def sample_b(*args, **kwargs):
        return {"second": second, "price": price, "return_bp": changed.copy(), "age": age}

    monkeypatch.setattr(mod.parent, "sample_session", sample_b)
    b = mod.build_fine_order_e15(Path("."), _one_bar(), (2023,)).iloc[0]
    assert bool(a.path19_complete) and bool(b.path19_complete)
    for key in ("l1l2_19", "maxl2_19", "rtv19", "ap19"):
        np.testing.assert_allclose(float(a[key]), float(b[key]), rtol=0, atol=0)


def test_future_bar_append_does_not_change_feature_prefix(monkeypatch):
    r15 = np.zeros(481)
    r15[1:] = np.resize(fixture_returns(), 480)
    price = np.full(481, 100.0)
    age = np.zeros(481)
    second = np.arange(0, 7201, 15)
    monkeypatch.setattr(mod.parent, "load_3s", lambda root, symbol, year: _fake_source_day().copy())
    monkeypatch.setattr(mod.parent, "sample_session", lambda *args, **kwargs: {"second": second, "price": price, "return_bp": r15.copy(), "age": age})

    p2 = pd.DataFrame({
        "symbol": ["000688.SH"] * 2,
        "trading_day": ["2023-01-03"] * 2,
        "year": [2023] * 2,
        "afternoon": [0] * 2,
        "slot": [575, 580],
        "bar_end": [pd.Timestamp("2023-01-03 09:35:00"), pd.Timestamp("2023-01-03 09:40:00")],
        "row_id": [0, 1],
    })
    p3 = pd.concat([p2, pd.DataFrame({
        "symbol": ["000688.SH"], "trading_day": ["2023-01-03"], "year": [2023],
        "afternoon": [0], "slot": [585], "bar_end": [pd.Timestamp("2023-01-03 09:45:00")], "row_id": [2],
    })], ignore_index=True)
    a = mod.build_fine_order_e15(Path("."), p2, (2023,))
    b = mod.build_fine_order_e15(Path("."), p3, (2023,)).iloc[:2]
    cols = ["fine_complete", "path19_complete", "l1l2_19", "maxl2_19", "rtv19", "ap19", "A5", "partial_price"]
    pd.testing.assert_frame_equal(a[cols].reset_index(drop=True), b[cols].reset_index(drop=True), check_exact=True)


def test_B_O_L_expected_counts_and_complexity_match(monkeypatch):
    def fake_parent_design(q, model):
        assert model == "A"
        return np.zeros((len(q), 92), dtype=float), [f"parent{i}" for i in range(92)]

    monkeypatch.setattr(mod.parent, "design", fake_parent_design)
    q = pd.DataFrame({
        "previous_state": ["NORMAL", "UNSAFE", "RECOVERING"],
        "l1l2_19": [0.6, 0.7, 0.8],
        "maxl2_19": [0.3, 0.4, 0.5],
        "rtv19": [0.2, 0.4, 0.7],
        "ap19": [-0.2, 0.1, 0.3],
        "rtv19_lag": [0.25, 0.35, 0.65],
        "ap19_lag": [-0.1, 0.0, 0.2],
    })
    b, bn = mod.design(q, "B")
    o, on = mod.design(q, "O")
    l, ln = mod.design(q, "L")
    assert b.shape == (3, 112)
    assert o.shape == l.shape == (3, 132)
    assert on == ln
    assert on[:112] == ln[:112] == bn
    assert len(on[112:]) == 20
