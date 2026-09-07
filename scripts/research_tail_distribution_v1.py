"""Frozen two-index, matched-time tail calibration and repeat-audit analysis."""

# ruff: noqa: E402
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from star50_filter.tail_distribution import (
    calibrate,
    cluster_episodes,
    clustering_tests,
    prepare_instrument,
    previous_any,
    probability_scores,
    tail_statistics,
)

OUT = ROOT / "artifacts/tail_distribution_v1"
EXPORT = ROOT.parent / "unified_datahub/.runtime/live/exports/factorlab_unified_index_kline_v3_20260824"
SYMBOLS = ["000852.SH", "000688.SH"]
VIEWS = {1: "1m_official.parquet", 5: "5m_offset_0.parquet"}
EXPECTED = {
    1: "aeacff04b268c166faac333ec7ab9d840abcd347d82cb3bcee0218d058fc7423",
    5: "d3101e6adf7a3e85b11f7c3503a6161f3ab363f7edd90ac8cba451ffe409c46a",
}


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=str) + "\n")


def freeze():
    assert not OUT.exists()
    sources = [
        "src/star50_filter/tail_distribution.py",
        "scripts/research_tail_distribution_v1.py",
        "tests/test_tail_distribution.py",
        "docs/research/tail_distribution_v1/protocol.md",
        "docs/research/tail_distribution_v1/data_usage.json",
    ]
    manifest = json.loads((EXPORT / "manifest.json").read_text())
    for m, name in VIEWS.items():
        assert sha(EXPORT / name) == manifest["artifacts"][name]["sha256"] == EXPECTED[m]
    save(
        OUT / "freeze.json",
        {
            "sources": {n: sha(ROOT / n) for n in sources},
            "inputs": {name: EXPECTED[m] for m, name in VIEWS.items()},
            "manifest_sha256": sha(EXPORT / "manifest.json"),
            "symbols": SYMBOLS,
            "parameter_search": False,
            "fresh_oos": False,
            "production_authority": False,
        },
    )


def check():
    f = json.loads((OUT / "freeze.json").read_text())
    for p, h in f["sources"].items():
        assert sha(ROOT / p) == h, p
    return f


def prepare():
    frozen = check()
    assert not (OUT / "prepared.json").exists()
    receipts = []
    for minutes, name in VIEWS.items():
        assert sha(EXPORT / name) == frozen["inputs"][name]
        raw = pd.read_parquet(
            EXPORT / name, filters=[("symbol", "in", SYMBOLS), ("trading_day", ">=", "2020-07-23"), ("trading_day", "<=", "2025-12-31")]
        )
        frames = [prepare_instrument(raw[raw.symbol == symbol], minutes) for symbol in SYMBOLS]
        common = set(frames[0].timestamp) & set(frames[1].timestamp)
        frames = [f[f.timestamp.isin(common)].reset_index(drop=True) for f in frames]
        assert np.array_equal(frames[0].timestamp, frames[1].timestamp)
        cut = calibrate(frames)
        save(OUT / f"cutoffs_{minutes}m.json", cut)
        data = pd.concat(frames, ignore_index=True)
        data = data[data.year >= 2021].copy()
        assert data.year.max() == 2025
        for symbol, bins in cut["volatility_terciles"].items():
            ix = data.symbol == symbol
            data.loc[ix, "vol_bin"] = np.searchsorted(bins, data.loc[ix, "sigma_prior"], side="right")
        data["vol_bin"] = data.vol_bin.astype(int)
        assert np.isfinite(data.loc[~data.boundary, ["r", "sigma_prior", "z"]].to_numpy()).all()
        data.to_parquet(OUT / f"panel_{minutes}m.parquet", index=False)
        receipts.append(
            {
                "minutes": minutes,
                "rows": len(data),
                "days_per_symbol": data.groupby("symbol").day.nunique().to_dict(),
                "min_day": data.day.min(),
                "max_day": data.day.max(),
                "panel_sha256": sha(OUT / f"panel_{minutes}m.parquet"),
                "cutoffs_sha256": sha(OUT / f"cutoffs_{minutes}m.json"),
            }
        )
        print(minutes, "minute calibration", cut, flush=True)
    save(OUT / "prepared.json", {"freeze_sha256": sha(OUT / "freeze.json"), "views": receipts, "no_strategy_returns": True})


def cube(frame, column):
    p = frame.pivot(index="day", columns=["session", "clock"], values=column).sort_index(axis=1)
    assert p.notna().all().all(), "incomplete matched intraday grid"
    assert p.shape[1] % 2 == 0
    return p.to_numpy().reshape(len(p), 2, p.shape[1] // 2), p.index.to_numpy()


def marginal(g, basis, threshold):
    x = g[{"raw": "r", "standardized": "z", "robust": "robust_z"}[basis]]
    valid = x.notna()
    event = x.abs() > threshold
    tail = g[event]
    simple = np.expm1(g.r) * 10000
    return {
        "observations": int(valid.sum()),
        "events": int(event.sum()),
        "rate": float(event.sum() / valid.sum()),
        "up_events": int((event & (g.r > 0)).sum()),
        "down_events": int((event & (g.r < 0)).sum()),
        "mean_abs_tail_simple_bp": float(np.expm1(tail.r).abs().mean() * 10000) if len(tail) else 0.0,
        "max_up_simple_bp": float(simple.max()),
        "max_down_simple_bp": float(simple.min()),
        "squared_return_share": float((tail.r**2).sum() / (g.r**2).sum()),
    }


def analyze(minutes):
    check()
    started = time.perf_counter()
    dest = OUT / f"{minutes}m"
    assert not dest.exists()
    dest.mkdir()
    prep = json.loads((OUT / "prepared.json").read_text())
    receipt = next(r for r in prep["views"] if r["minutes"] == minutes)
    assert sha(OUT / f"panel_{minutes}m.parquet") == receipt["panel_sha256"]
    assert sha(OUT / f"cutoffs_{minutes}m.json") == receipt["cutoffs_sha256"]
    data = pd.read_parquet(OUT / f"panel_{minutes}m.parquet")
    cut = json.loads((OUT / f"cutoffs_{minutes}m.json").read_text())
    margins = []
    conditions = []
    clustering = []
    tests = []
    forecasts = []
    events = []
    severity = []
    boundary = []
    coincidences = []
    for symbol in SYMBOLS:
        full = data[data.symbol == symbol].copy()
        f = full[~full.boundary].copy().sort_values("timestamp").reset_index(drop=True)
        for year, g in f.groupby("year"):
            r = np.expm1(g.r)
            for absolute in [0.001, 0.002, 0.005, 0.01]:
                severity.append(
                    {
                        "minutes": minutes,
                        "symbol": symbol,
                        "year": year,
                        "absolute_simple_cutoff": absolute,
                        "bars": len(g),
                        "up_count": int((r > absolute).sum()),
                        "down_count": int((r < -absolute).sum()),
                    }
                )
        for year, g in full[full.boundary].groupby("year"):
            for session, h in g.groupby("session"):
                for component in ["gap", "body", "return_all"]:
                    v = np.expm1(h[component]) * 10000
                    boundary.append(
                        {
                            "minutes": minutes,
                            "symbol": symbol,
                            "year": year,
                            "session": session,
                            "component": component,
                            "count": v.notna().sum(),
                            "median_abs_bp": v.abs().median(),
                            "max_up_bp": v.max(),
                            "max_down_bp": v.min(),
                            "abs_over_50bp": int((v.abs() > 50).sum()),
                            "abs_over_100bp": int((v.abs() > 100).sum()),
                        }
                    )
        for basis in ["raw", "standardized", "robust"]:
            threshold = cut["tail_cutoffs"][basis]
            for year, g in f.groupby("year"):
                margins.append(
                    {
                        "minutes": minutes,
                        "symbol": symbol,
                        "year": year,
                        "basis": basis,
                        "threshold": threshold,
                        **marginal(g, basis, threshold),
                    }
                )
            if basis == "robust":
                continue
            column = "r" if basis == "raw" else "z"
            g = f.copy()
            g["event"] = g[column].abs() > threshold
            y, _ = cube(g, "event")
            g["prior5"] = previous_any(y, 5 // minutes).reshape(-1)
            g["prior30"] = previous_any(y, 30 // minutes).reshape(-1)
            train = g[g.year <= 2023].copy()
            test = g[g.year >= 2024].copy()
            y, days = cube(test, "event")
            v, _ = cube(test, "vol_bin")
            year_ids = np.array([int(day[:4]) for day in days])
            s = tail_statistics(y, v, 5 // minutes)
            episodes = cluster_episodes(y, minutes)
            episodes["day"] = days[episodes.day_index.to_numpy(int)]
            episodes.to_csv(dest / f"{symbol}_{basis}_episodes.csv", index=False)
            s["clusters"] = len(episodes)
            s["single_event_clusters"] = int((episodes.events == 1).sum())
            s["events_in_multi_event_clusters"] = int(episodes.loc[episodes.events > 1, "events"].sum())
            s["max_cluster_events"] = int(episodes.events.max())
            s["after30_rate"] = float(test.loc[test.prior30, "event"].mean())
            clustering.append({"minutes": minutes, "symbol": symbol, "basis": basis, **s})
            p5 = test.groupby(["vol_bin", "prior5"]).event.agg(["sum", "size"]).reset_index()
            p5["rate"] = p5["sum"] / p5["size"]
            p5["time_share"] = p5["size"] / len(test)
            p5["tail_capture"] = p5["sum"] / test.event.sum()
            p5["symbol"] = symbol
            p5["basis"] = basis
            p5["minutes"] = minutes
            conditions.append(p5)
            forecast, pred = probability_scores(train, test)
            forecasts.extend([{"minutes": minutes, "symbol": symbol, "basis": basis, **row} for row in forecast])
            model = train.groupby(["vol_bin", "prior5"]).event.agg(["sum", "size"])
            model["probability"] = (model["sum"] + 0.5) / (model["size"] + 1)
            model.to_csv(dest / f"{symbol}_{basis}_frozen_probability_cells.csv")
            test["predicted_tail_probability"] = pred
            test["first_event"] = test.event & ~test.prior5
            ev = test[test.event].copy()
            ev["basis"] = basis
            events.append(ev)
            rows, null = clustering_tests(
                y,
                v,
                year_ids,
                5 // minutes,
                seed=20260907 + minutes + (0 if symbol == SYMBOLS[0] else 100) + (0 if basis == "raw" else 200),
            )
            tests.extend([{"minutes": minutes, "symbol": symbol, "basis": basis, **row} for row in rows])
            np.save(dest / f"{symbol}_{basis}_null.npy", null)
            print(minutes, symbol, basis, "events", s["events"], "raw p", [r["p_raw"] for r in rows], flush=True)
    for basis, col in [("raw", "r"), ("standardized", "z")]:
        a = data[(data.symbol == SYMBOLS[0]) & ~data.boundary & (data.year >= 2024)].set_index("timestamp")
        b = data[(data.symbol == SYMBOLS[1]) & ~data.boundary & (data.year >= 2024)].set_index("timestamp")
        assert a.index.equals(b.index)
        ea = a[col].abs() > cut["tail_cutoffs"][basis]
        eb = b[col].abs() > cut["tail_cutoffs"][basis]
        both = ea & eb
        coincidences.append(
            {
                "minutes": minutes,
                "basis": basis,
                "CSI_events": int(ea.sum()),
                "STAR_events": int(eb.sum()),
                "simultaneous": int(both.sum()),
                "STAR_given_CSI": float(both.sum() / ea.sum()),
                "CSI_given_STAR": float(both.sum() / eb.sum()),
                "same_sign_given_both": float((np.sign(a.loc[both, "r"]) == np.sign(b.loc[both, "r"])).mean()),
            }
        )
    for name, rows in [
        ("marginals", margins),
        ("clustering", clustering),
        ("tests", tests),
        ("forecasts", forecasts),
        ("severity", severity),
        ("boundaries", boundary),
        ("coincidences", coincidences),
    ]:
        pd.DataFrame(rows).to_csv(dest / f"{name}.csv", index=False)
    pd.concat(conditions, ignore_index=True).to_csv(dest / "conditions.csv", index=False)
    ev = pd.concat(events, ignore_index=True)
    ev.to_parquet(dest / "tail_events.parquet", index=False)
    ev.loc[ev.basis == "raw"].assign(abs_r=lambda x: x.r.abs()).sort_values("abs_r", ascending=False).head(40).to_csv(
        dest / "largest_events.csv", index=False
    )
    save(
        dest / "receipt.json",
        {
            "freeze_sha256": sha(OUT / "freeze.json"),
            "minutes": minutes,
            "elapsed_seconds": time.perf_counter() - started,
            "evaluation_years": [2024, 2025],
            "files": {p.name: sha(p) for p in sorted(dest.iterdir()) if p.is_file()},
            "routing_authority": False,
            "production_authority": False,
        },
    )
    print(pd.DataFrame(clustering).to_string(index=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["freeze", "prepare", "analyze"])
    p.add_argument("--minutes", type=int, choices=[1, 5])
    a = p.parse_args()
    if a.mode == "freeze":
        freeze()
    elif a.mode == "prepare":
        prepare()
    else:
        analyze(a.minutes)
