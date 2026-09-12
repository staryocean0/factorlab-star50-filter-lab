from pathlib import Path
import json
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]

def test_only_star50_and_roles():
    man = json.loads((ROOT / "data/manifest.json").read_text())
    assert man["symbol"] == "000688.SH"
    df = pd.read_parquet(ROOT / "data/development/5m_offset_0.parquet", columns=["symbol", "trading_day"])
    assert set(df["symbol"].unique()) == {"000688.SH"}
    assert str(df["trading_day"].min()) >= "2020-07-23"

