import hashlib
import json

import pandas as pd
import pytest

from star50_filter.cloud_market_data import check_request, load_market_data


@pytest.mark.parametrize(
    "symbol,freq,start,end",
    [
        ("588000.SSE", "3s", "2024-01-01", "2025-01-01"),
        ("000852.SH", "1m", "2014-01-01", "2015-01-01"),
        ("000688.SH", "3s", "2025-01-01", "2026-01-01"),
        ("000688.SH", "15s", "2024-01-01", "2025-01-01"),
    ],
)
def test_denied(symbol, freq, start, end):
    with pytest.raises(ValueError):
        check_request(symbol, freq, start, end)


def test_clock_same_second_and_hash(tmp_path):
    folder = tmp_path / "data/cross_index_risk_gate_3s_v1"
    folder.mkdir(parents=True)
    file = folder / "test.parquet"
    pd.DataFrame(
        {
            "symbol": ["000688.SH"] * 2,
            "trading_day": ["2024-01-02"] * 2,
            "observation_datetime": ["2024-01-02T09:30:00Z"] * 2,
            "row_index": [1, 2],
            "price": [1000.0, 1001.0],
        }
    ).to_parquet(file, index=False)
    item = {
        "path": file.name,
        "symbol": "000688.SH",
        "first_day": "2024-01-02",
        "last_day": "2024-01-02",
        "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
    }
    (folder / "manifest.json").write_text(json.dumps({"files": [item]}))
    frame = load_market_data(
        "000688.SH", "3s", "2024-01-02", "2024-01-02", root=tmp_path
    )
    assert len(frame) == 2 and frame.market_time_shanghai.dt.hour.tolist() == [9, 9]
    assert frame.row_index.tolist() == [1, 2]
    with file.open("ab") as f:
        f.write(b"tamper")
    with pytest.raises(ValueError, match="hash"):
        load_market_data("000688.SH", "3s", "2024-01-02", "2024-01-02", root=tmp_path)
