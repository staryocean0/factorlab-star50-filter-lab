"""Bounded direct-sum verification on two real ETF days; no full replay claim."""

# ruff: noqa: E402
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src")]
from research_resolution_transfer_v1 import BIND, OUT, save, sha, spot_coverage
from star50_filter.resolution_measurement import observed_grid


def main():
    binding = json.loads(BIND.read_text())["spot"]
    grant = spot_coverage(binding["dataset_version"])
    base = Path(grant["storage_uri"])
    assert sha(base / "manifest.json") == binding["manifest_file_sha256"]
    files = {r["trading_day"]: r for r in json.loads((base / "manifest.json").read_text())["files"]}
    checks = []
    for day in ["2024-01-02", "2025-01-02"]:
        item = files[day.replace("-", "")]
        p = base / item["path"]
        assert sha(p) == item["sha256"]
        raw = (
            pq.ParquetFile(p)
            .read(columns=["instrument_id", "market_observed_at", "valid_until", "event_seq", "bid_price_x10000_1", "ask_price_x10000_1"])
            .to_pandas()
        )
        expected = pd.read_parquet(OUT / f"seconds_{day[:4]}" / "common_support.parquet")
        expected = expected[(expected.day == day) & (expected.field == "mid") & (expected.horizon == 30)]
        for symbol, g in raw.groupby("instrument_id"):
            g = g[g.valid_until > g.market_observed_at].sort_values(["market_observed_at", "event_seq"])
            ts = pd.to_datetime(g.market_observed_at).astype("datetime64[ns]").astype("int64").to_numpy()
            until = pd.to_datetime(g.valid_until).astype("datetime64[ns]").astype("int64").to_numpy()
            bid = g.bid_price_x10000_1.to_numpy(float)
            ask = g.ask_price_x10000_1.to_numpy(float)
            price = np.where((bid > 0) & (ask >= bid), (bid + ask) / 20000, np.nan)
            for row in expected[expected.symbol == symbol].itertuples():
                start = pd.Timestamp(day + (" 09:30" if row.session == "am" else " 13:00")).value
                t = start + np.arange(row.minute * 60 - 1800, row.minute * 60 + 1, row.delta, dtype=np.int64) * 10**9
                keep = (ts >= start) & (ts <= start + 7200 * 10**9)
                values, _ = observed_grid(ts[keep], price[keep], until[keep], t)
                d = np.diff(np.log(values))
                road = abs(d).sum()
                net = np.log(values[-1]) - np.log(values[0])
                assert np.isfinite(d).all() and road > 0
                error = max(abs(abs(net) / road - row.er), abs(road - row.road), abs(net - row.net))
                assert error < 1e-12
                prefix = keep & (ts <= t[-1])
                truncated, _ = observed_grid(ts[prefix], price[prefix], until[prefix], t)
                np.testing.assert_array_equal(values, truncated)
                checks.append({"day": day, "symbol": symbol, "delta": row.delta, "minute": row.minute, "error": error})
    assert len(checks) > 100
    output = OUT / "formula_audit.json"
    assert not output.exists()
    save(
        output,
        {
            "scope": "two_real_ETF_days_direct_sums_and_no_future_observation_values",
            "cases": len(checks),
            "max_error": max(r["error"] for r in checks),
            "source_sha256": sha(Path(__file__)),
            "full_seconds_replay": False,
        },
    )
    print(output.read_text())


if __name__ == "__main__":
    main()
