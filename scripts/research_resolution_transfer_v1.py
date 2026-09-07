"""Two separate bounded research lanes: observed-grid ER and fixed CSI1000 replay."""

# ruff: noqa: E402

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT.parent / "unified_datahub"
FACTOR = ROOT.parent / "baylum terminal 0.4.1/factor_lab"
sys.path[:0] = [str(ROOT / "src"), str(HUB / "src"), str(FACTOR / "src")]
from star50_filter.resolution_measurement import common_support, session_measurements
from star50_filter.slope_union import build_signals
from star50_filter.slope_union_v2 import Policy, account, features, targets

from factor_lab.data.services.standard_backtest_service import resolve_execution_window
from factor_lab.data.session_offset_defaults import DataContract

OUT = ROOT / "artifacts/resolution_transfer_v1"
DOC = ROOT / "docs/research/resolution_transfer_v1"
EXPORT = HUB / ".runtime/live/exports/factorlab_unified_index_kline_v3_20260824"
BIND = ROOT / "docs/research/conditional_bucket_v1/datahub_binding_v1.json"


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n")


def freeze():
    assert not OUT.exists()
    sources = [
        "src/star50_filter/resolution_measurement.py",
        "src/star50_filter/slope_union.py",
        "src/star50_filter/slope_union_v2.py",
        "scripts/research_resolution_transfer_v1.py",
        "tests/test_resolution_measurement.py",
        "docs/research/resolution_transfer_v1/protocol.md",
        "docs/research/resolution_transfer_v1/data_usage.json",
        "docs/research/half_day_slope_union_v2/selected_policy.json",
    ]
    m = json.loads((EXPORT / "manifest.json").read_text())
    assert sha(EXPORT / "1m_official.parquet") == m["artifacts"]["1m_official.parquet"]["sha256"]
    save(
        OUT / "freeze.json",
        {
            "sources": {n: sha(ROOT / n) for n in sources},
            "export_manifest_sha256": sha(EXPORT / "manifest.json"),
            "minute_source_sha256": m["artifacts"]["1m_official.parquet"]["sha256"],
            "spot_binding_sha256": sha(BIND),
            "production_authority": False,
        },
    )
    print("freeze complete, no new price rows read")


def check():
    f = json.loads((OUT / "freeze.json").read_text())
    for p, h in f["sources"].items():
        assert sha(ROOT / p) == h, p
    assert sha(BIND) == f["spot_binding_sha256"]
    return f


def spot_coverage(version):
    command = [str(HUB / '.venv/bin/python'), str(HUB / 'scripts/star50_history_bbo_onboarding.py'),
               'coverage', '--product', 'spot', '--dataset-version', version]
    result = subprocess.run(command, cwd=HUB, capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def seconds(year):
    check()
    assert year in [2024, 2025]
    dest = OUT / f"seconds_{year}"
    assert not dest.exists()
    dest.mkdir()
    binding = json.loads(BIND.read_text())["spot"]
    grant = spot_coverage(binding["dataset_version"])
    assert grant["serving_grant"]["dataset_version"] == binding["dataset_version"]
    path = Path(grant["storage_uri"])
    assert sha(path / "manifest.json") == binding["manifest_file_sha256"]
    manifest = json.loads((path / "manifest.json").read_text())
    files = [r for r in manifest["files"] if r["trading_day"].startswith(str(year))]
    rows = []
    quality = []
    inputs = {}
    counts = []
    start = time.perf_counter()
    cols = [
        "instrument_id",
        "market_observed_at",
        "valid_until",
        "event_seq",
        "last_price_x10000",
        "bid_price_x10000_1",
        "ask_price_x10000_1",
        "time_authority",
    ]
    for no, item in enumerate(files):
        # Each physical read repeats the exact current serving check.
        assert spot_coverage(binding["dataset_version"])["serving_grant"] == grant["serving_grant"]
        p = path / item["path"]
        assert sha(p) == item["sha256"]
        inputs[item["path"]] = item["sha256"]
        f = pq.ParquetFile(p).read(columns=cols).to_pandas()
        assert set(f.time_authority) == {"historical_market_replay"}
        day = item["trading_day"]
        day = f"{day[:4]}-{day[4:6]}-{day[6:]}"
        for symbol, g in f.groupby("instrument_id"):
            assert symbol in ["588000.SSE", "588080.SSE"]
            g = g.sort_values(["market_observed_at", "event_seq"])
            g = g[g.valid_until > g.market_observed_at].copy()
            assert not g.market_observed_at.duplicated().any()
            ts = pd.to_datetime(g.market_observed_at).astype("datetime64[ns]").astype("int64").to_numpy()
            until = pd.to_datetime(g.valid_until).astype("datetime64[ns]").astype("int64").to_numpy()
            bid = g.bid_price_x10000_1.to_numpy(float) / 10000
            ask = g.ask_price_x10000_1.to_numpy(float) / 10000
            good = (bid > 0) & (ask >= bid)
            mid = np.where(good, (bid + ask) / 2, np.nan)
            last = g.last_price_x10000.to_numpy(float) / 10000
            last[last <= 0] = np.nan
            counts.append({"day": day, "symbol": symbol, "source_rows": len(g)})
            for phase, clock in [("am", "09:30"), ("pm", "13:00")]:
                anchor = pd.Timestamp(day + " " + clock).value
                inside = (ts >= anchor) & (ts <= anchor + 7200 * 10**9)
                rec, q = session_measurements(
                    ts[inside], {"mid": mid[inside], "last": last[inside]}, until[inside], anchor, day, symbol, phase
                )
                rows.extend(rec)
                quality.extend(q)
        if (no + 1) % 40 == 0:
            print(year, no + 1, "/", len(files), "days", flush=True)
    frame = pd.DataFrame(rows)
    shared = common_support(frame)
    frame.to_parquet(dest / "measurements.parquet", index=False)
    shared.to_parquet(dest / "common_support.parquet", index=False)
    pd.DataFrame(quality).to_csv(dest / "coverage.csv", index=False)
    pd.DataFrame(counts).to_csv(dest / "source_counts.csv", index=False)
    tables = []
    for keys, g in shared.groupby(["symbol", "field", "horizon", "delta"]):
        symbol, field, h, delta = keys
        er = g.er
        var = float(er.var(ddof=1))
        non = g[g.nonoverlap]
        tables.append(
            {
                "year": year,
                "symbol": symbol,
                "field": field,
                "horizon": h,
                "delta": delta,
                "rows": len(g),
                "days": g.day.nunique(),
                "er_mean": er.mean(),
                "er_variance": var,
                "n_times_variance": var * h * 60 / delta,
                "cv2": var / er.mean() ** 2,
                "var60_median": g.var60.median(),
                "step5_mean": g.step5.mean(),
                "zero_share": g.zero_share.mean(),
                "top1_mean": g.top1.mean(),
                "nonoverlap_rows": len(non),
                "nonoverlap_variance": non.er.var(ddof=1),
            }
        )
    tab = pd.DataFrame(tables)
    tab.to_csv(dest / "summary.csv", index=False)
    save(
        dest / "receipt.json",
        {
            "year": year,
            "grant": grant,
            "inputs": inputs,
            "source_days": len(files),
            "freeze_sha256": sha(OUT / "freeze.json"),
            "elapsed_seconds": time.perf_counter() - start,
            "market_time_interpolation": False,
            "new_OHLC": False,
            "files": {p.name: sha(p) for p in dest.iterdir() if p.is_file()},
        },
    )
    print(tab[(tab.horizon == 30) & (tab.field == "mid")].to_string(index=False))
    print("seconds lane runtime", time.perf_counter() - start)


def migration(year):
    f = check()
    assert 2021 <= year <= 2025
    if year > 2021:
        assert (OUT / f"migration_{year - 1}" / "review.json").exists()
    dest = OUT / f"migration_{year}"
    assert not dest.exists()
    assert sha(EXPORT / "manifest.json") == f["export_manifest_sha256"]
    assert sha(EXPORT / "1m_official.parquet") == f["minute_source_sha256"]
    window = resolve_execution_window(
        DataContract(
            frequency="1m",
            close_anchor=None,
            session_offset_minutes=0,
            bar_align="session_wall_clock",
            construction_contract="cn_a_session_wall_clock_offset_v1",
            signal_view="identity_index_point",
            fill_view="raw_pit",
        )
    )
    assert window == "next_tradable_after_bar_close"
    bars = pd.read_parquet(
        EXPORT / "1m_official.parquet",
        filters=[("symbol", "==", "000852.SH"), ("trading_day", ">=", "2020-01-01"), ("trading_day", "<=", f"{year}-12-31")],
    )
    bars["timestamp"] = pd.to_datetime(bars.timestamp.astype(str).str[:19]).dt.tz_localize("Asia/Shanghai")
    bars = bars.sort_values("timestamp").reset_index(drop=True)
    assert not bars.timestamp.duplicated().any()
    assert (bars.groupby("trading_day").size() == 240).all()
    bars["year"] = bars.trading_day.astype(str).str[:4].astype(int)
    bars["trading_minute"] = np.arange(len(bars))
    assert bars.year.min() == 2020 and bars.year.max() == year
    cfg = json.loads((ROOT / "docs/research/half_day_slope_union_v2/selected_policy.json").read_text())["config"]
    policies = {"V1": Policy(), "V2": Policy(**cfg)}
    y, s, vol = features(bars.close)
    ix = np.flatnonzero(bars.year.to_numpy() == year)
    part = bars.iloc[ix].reset_index(drop=True)
    direct = build_signals(bars[["timestamp", "trading_minute", "close"]])
    np.testing.assert_array_equal(targets(s, vol[240], Policy()), direct.target_at_close)
    dest.mkdir()
    rows = []
    for label, p in policies.items():
        target = targets(s, vol[p.volatility_window], p)
        np.save(dest / f"{label}_targets.npy", target[ix])
        for fee in [0, 2, 4, 7]:
            t, d, nav, m = account(part.open, part.timestamp - pd.Timedelta(minutes=1), target[ix], int(target[ix[0] - 1]), fee)
            t.to_parquet(dest / f"{label}_fee{fee}_trades.parquet", index=False)
            d.to_parquet(dest / f"{label}_fee{fee}_daily.parquet")
            np.save(dest / f"{label}_fee{fee}_nav.npy", nav)
            rows.append({"year": year, "label": label, "fee_bps": fee, **m})
    pd.DataFrame(rows).to_csv(dest / "summary.csv", index=False)
    save(
        dest / "receipt.json",
        {
            "year": year,
            "symbol": "000852.SH",
            "rows": len(part),
            "max_read_year": year,
            "config": cfg,
            "source_sha256": f["minute_source_sha256"],
            "freeze_sha256": sha(OUT / "freeze.json"),
            "prior_review_sha256": None if year == 2021 else sha(OUT / f"migration_{year - 1}" / "review.json"),
            "v1_direct_signal_exact": True,
            "production_authority": False,
            "files": {p.name: sha(p) for p in dest.iterdir() if p.is_file()},
        },
    )
    print(pd.DataFrame(rows).query("fee_bps==2").to_string(index=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["freeze", "seconds", "migration"])
    p.add_argument("--year", type=int)
    a = p.parse_args()
    if a.mode == "freeze":
        freeze()
    elif a.mode == "seconds":
        seconds(a.year)
    else:
        migration(a.year)
