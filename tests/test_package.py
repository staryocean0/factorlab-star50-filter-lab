from pathlib import Path
import json
import numpy as np
import pandas as pd
from star50_filter.filters import butter_lowpass, hysteresis_positions
from star50_filter.backtest import execute_next_open

ROOT = Path(__file__).resolve().parents[1]

def test_only_star50_and_roles():
    man = json.loads((ROOT / "data/manifest.json").read_text())
    assert man["symbol"] == "000688.SH"
    df = pd.read_parquet(ROOT / "data/development/5m_offset_0.parquet", columns=["symbol", "trading_day"])
    assert set(df["symbol"].unique()) == {"000688.SH"}
    assert str(df["trading_day"].min()) >= "2020-07-23"

def test_lowpass_is_causal():
    x = np.cumsum(np.random.default_rng(0).normal(size=200))
    y = butter_lowpass(x, 12, order=1)
    y2 = butter_lowpass(np.concatenate([x, np.array([x[-1] + 10.0])]), 12, order=1)
    np.testing.assert_allclose(y[20:180], y2[20:180], atol=1e-12)

def test_hysteresis_holds_until_threshold():
    y = np.array([0.0, 0.1, 0.2, 0.15, 0.14, 0.0, -0.2], dtype=float)
    pos = hysteresis_positions(y, 0.15)
    assert pos[2] == 1.0
    assert pos[4] == 1.0  # small dip does not reverse
    assert pos[-1] == -1.0

def test_execute_delay():
    sig = np.array([0.0, 1.0, 1.0, -1.0, -1.0])
    op = np.array([1.0, 1.0, 1.01, 1.0, 0.99])
    exec_pos, pnl = execute_next_open(sig, op)
    assert exec_pos[0] == 0 and exec_pos[1] == 0
    assert exec_pos[3] == 1.0
