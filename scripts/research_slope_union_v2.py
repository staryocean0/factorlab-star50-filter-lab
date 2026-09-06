"""One-year-at-a-time V2 freeze, blind replay, bounded family and snapshots."""

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FACTORLAB = ROOT.parent / "baylum terminal 0.4.1/factor_lab"
sys.path[:0] = [str(ROOT / "src"), str(FACTORLAB / "src")]
from star50_filter.slope_union import build_signals  # noqa: E402
from star50_filter.slope_union_v2 import Policy, account, family, features, summary, targets  # noqa: E402

from factor_lab.data.services.standard_backtest_service import resolve_execution_window  # noqa: E402
from factor_lab.data.session_offset_defaults import DataContract  # noqa: E402

OUT = ROOT / "artifacts/half_day_slope_union_v2"
DOC = ROOT / "docs/research/half_day_slope_union_v2"
DATA = ROOT / "artifacts/drawdown_material/1m_official.parquet"


def sha(p):
    with Path(p).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def sources():
    return [
        "src/star50_filter/slope_union.py",
        "src/star50_filter/slope_union_v2.py",
        "scripts/research_slope_union_v2.py",
        "tests/test_slope_union_v2.py",
        "docs/research/half_day_slope_union_v2/whitepaper.md",
        "docs/research/half_day_slope_union_v2/data_usage.json",
    ]


def freeze():
    assert not OUT.exists()
    ref = json.loads((DATA.parent / "receipt.json").read_text())
    expected = next(x["export_sha256"] for x in ref["views"] if x["view_id"] == "1m_official")
    assert sha(DATA) == expected
    window = resolve_execution_window(DataContract(
        frequency="1m", close_anchor=None, session_offset_minutes=0,
        bar_align="session_wall_clock", construction_contract="cn_a_session_wall_clock_offset_v1",
        signal_view="raw_canonical", fill_view="raw_pit"))
    assert window == "next_tradable_after_bar_close"
    save(
        OUT / "freeze.json",
        {
            "inputs": {str(DATA): expected},
            "sources": {n: sha(ROOT / n) for n in sources()},
            "policies": {p.id: asdict(p) for p in family()},
            "baseline": Policy().id,
            "execution_window": window,
            "production_authority": False,
        },
    )
    print("FROZEN 324 identities; no price values read")


def check():
    f = json.loads((OUT / "freeze.json").read_text())
    for n, d in f["sources"].items():
        assert sha(ROOT / n) == d, n
    for n, d in f["inputs"].items():
        assert sha(n) == d, n
    return f


def load(year):
    raw = pd.read_parquet(DATA, filters=[("trading_day", "<=", f"{year}-12-31")])
    assert set(raw.symbol) == {"000688.SH"}
    assert set(raw.fill_price_view) == {"raw_pit"}, set(raw.fill_price_view)
    raw["timestamp"] = pd.to_datetime(raw.timestamp.astype(str).str[:19]).dt.tz_localize("Asia/Shanghai")
    assert raw.timestamp.is_monotonic_increasing and not raw.timestamp.duplicated().any()
    assert (raw.groupby("trading_day").size() == 240).all(), "missing source minute/day"
    assert np.isfinite(raw[["open", "high", "low", "close"]].to_numpy(float)).all()
    assert (raw[["open", "high", "low", "close"]].to_numpy(float) > 0).all()
    raw["trading_minute"] = np.arange(len(raw))
    raw["year"] = raw.trading_day.astype(str).str[:4].astype(int)
    assert raw.year.max() == year and raw.year.min() == 2020
    return raw.reset_index(drop=True)


def run(year, mode):
    check()
    start = time.perf_counter()
    assert 2021 <= year <= 2025
    if year > 2021:
        assert (OUT / str(year - 1) / "review.json").exists()
    dest = OUT / str(year) / mode
    assert not dest.exists()
    if mode == "family":
        assert year <= 2023 and (OUT / str(year) / "blind_review.json").exists()
        policies = family()
    else:
        prior = Policy() if year == 2021 else Policy(**json.loads((OUT / str(year - 1) / "review.json").read_text())["selected_config"])
        policies = list({p.id: p for p in [Policy(), prior]}.values())
    bars = load(year)
    y, s, vol = features(bars.close)
    # Independently evaluate original V1 on an actual data prefix before economics.
    prefix = bars.iloc[: min(len(bars), 1500)]
    v1 = build_signals(prefix[["timestamp", "trading_minute", "close"]])
    np.testing.assert_array_equal(targets(s[: len(prefix)], vol[240][: len(prefix)], Policy()), v1.target_at_close)
    ix = np.flatnonzero(bars.year.to_numpy() == year)
    part = bars.iloc[ix].reset_index(drop=True)
    times = part.timestamp - pd.Timedelta(minutes=1)
    dest.mkdir(parents=True)
    save(
        dest / "science_gate.json",
        {
            "status": "diagnostic_signal_present_account_contract_may_open",
            "v1_prefix_equivalence": True,
            "clock": "raw_native_1m_closed_bar_to_next_open",
            "read_max_year": year,
            "financial_account": "index_direction_simulation",
            "production_authority": False,
        },
    )
    rows = []
    for p in policies:
        target = targets(s, vol[p.volatility_window], p)
        selected = target[ix]
        ledger, daily, nav, m = account(part.open, times, selected, int(target[ix[0] - 1]))
        assert target.size == len(bars)
        ledger.to_parquet(dest / f"{p.id}_trades.parquet", index=False)
        daily.to_parquet(dest / f"{p.id}_daily.parquet")
        # Compact close targets retain the complete account-policy output.
        np.save(dest / f"{p.id}_targets.npy", selected, allow_pickle=False)
        rows.append({"policy_id": p.id, **asdict(p), **m})
    pd.DataFrame(rows).to_csv(dest / "metrics.csv", index=False)
    selected_previous = None if year == 2021 else sha(OUT / str(year - 1) / "review.json")
    save(
        dest / "receipt.json",
        {
            "freeze_sha256": sha(OUT / "freeze.json"),
            "year": year,
            "mode": mode,
            "prior_review_sha256": selected_previous,
            "read_rows": len(bars),
            "year_rows": len(part),
            "elapsed_seconds": time.perf_counter() - start,
            "backend": "numpy_cpu_sparse_events",
            "files": {p.name: sha(p) for p in sorted(dest.iterdir()) if p.is_file()},
            "prior_policy": None if year == 2021 else json.loads((OUT / str(year - 1) / "review.json").read_text())["selected_config"],
        },
    )
    print(pd.DataFrame(rows).sort_values("mean_net_bp", ascending=False).head(8).to_string(index=False))
    print("runtime seconds", time.perf_counter() - start)


def rank(year):
    assert 2021 <= year <= 2023
    check()
    rows = []
    for p in family():
        frames = [pd.read_csv(OUT / str(y) / "family/metrics.csv").set_index("policy_id").loc[p.id] for y in range(2021, year + 1)]
        trades = pd.concat([pd.read_parquet(OUT / str(y) / "family" / f"{p.id}_trades.parquet") for y in range(2021, year + 1)])
        daily = pd.concat([pd.read_parquet(OUT / str(y) / "family" / f"{p.id}_daily.parquet") for y in range(2021, year + 1)])
        m = summary(trades, daily)
        rows.append({"policy_id": p.id, **asdict(p), **m, "min_year_trades": min(x.trades for x in frames)})
    result = pd.DataFrame(rows)
    base = result.loc[result.policy_id == Policy().id].iloc[0]
    result["eligible"] = (
        (result.min_year_trades >= 100)
        & (result["return"] > 0)
        & (result.sharpe >= base.sharpe)
        & (result.mdd <= base.mdd + 0.02)
        & (result.mean_net_bp > base.mean_net_bp + 1e-8)
    )
    result = result.sort_values(["eligible", "mean_net_bp", "sharpe", "trades", "policy_id"], ascending=[False, False, False, False, True])
    result.to_csv(OUT / str(year) / "ranking.csv", index=False)
    print(result.head(8).to_string(index=False))
    print("V1", base.to_json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "blind", "family", "rank"])
    parser.add_argument("--year", type=int)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze()
    elif args.mode == "rank":
        rank(args.year)
    else:
        run(args.year, args.mode)
