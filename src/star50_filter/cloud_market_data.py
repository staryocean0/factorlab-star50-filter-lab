"""Portable fixed-manifest input reader for the cross-index research package."""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
SYMBOLS = {"000688.SH", "000852.SH"}


def check_request(symbol, frequency, start, end):
    if symbol not in SYMBOLS or frequency not in {"3s", "1m", "5m"}:
        raise ValueError("only the two declared indices and 3s/1m/5m are authorized")
    first = {
        "000688.SH": "2020-07-23",
        "000852.SH": "2014-10-17" if frequency == "3s" else "2015-01-05",
    }[symbol]
    if (
        len(start) != 10
        or len(end) != 10
        or start < first
        or end > "2025-12-31"
        or start > end
    ):
        raise ValueError("outside the bounded historical input interval")
    pd.Timestamp(start)
    pd.Timestamp(end)


def load_market_data(symbol, frequency, start, end, *, root=ROOT):
    """Load exact supplied rows; retain same-second rows, repairs and provenance.

    No resampling, forward fill, market-event inference or trading computation.
    A source Z suffix encodes Shanghai wall clock, not an actual UTC timestamp.
    """
    check_request(symbol, frequency, start, end)
    root = Path(root).resolve()
    folder = root / (
        "data/cross_index_risk_gate_3s_v1"
        if frequency == "3s"
        else "data/cross_index_risk_gate_v1"
    )
    manifest = json.loads((folder / "manifest.json").read_text())
    parts = []
    for item in manifest["files"]:
        if item["symbol"] != symbol or (
            frequency != "3s" and item["frequency"] != frequency
        ):
            continue
        if item["last_day"] < start or item["first_day"] > end:
            continue
        path = (
            folder / item["path"] if frequency == "3s" else root / item["path"]
        ).resolve()
        if not path.is_relative_to(root):
            raise ValueError("manifest path escapes package")
        with path.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != item["sha256"]:
            raise ValueError(f"input hash mismatch: {path}")
        frame = pq.read_table(
            path, filters=[("trading_day", ">=", start), ("trading_day", "<=", end)]
        ).to_pandas()
        if set(frame.symbol) - {symbol}:
            raise ValueError("unexpected instrument in file")
        parts.append(frame)
    if not parts:
        return pd.DataFrame()
    frame = pd.concat(parts, ignore_index=True)
    clock = "observation_datetime" if frequency == "3s" else "timestamp"
    frame["market_time_shanghai"] = pd.to_datetime(
        frame[clock].str[:19]
    ).dt.tz_localize("Asia/Shanghai")
    if not (
        frame.market_time_shanghai.dt.strftime("%Y-%m-%d") == frame.trading_day
    ).all():
        raise ValueError("source calendar and clock mismatch")
    keys = (
        ["market_time_shanghai", "row_index"]
        if frequency == "3s"
        else ["market_time_shanghai"]
    )
    return frame.sort_values(keys, kind="stable").reset_index(drop=True)
