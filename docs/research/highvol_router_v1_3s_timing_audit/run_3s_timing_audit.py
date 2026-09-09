from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

YEARS = (2021, 2022, 2023, 2024, 2025)
DEV_YEARS = (2021, 2022, 2023)
VAL_YEARS = (2024, 2025)
DELAYS_SEC = (0, 3, 6, 15)
PRIMARY_COST_BP_PER_LEG = 1.0
EXPECTED_TRADES = {2021: 37, 2022: 31, 2023: 36, 2024: 58, 2025: 49}

HERE = Path(__file__).resolve().parent
DEV_RUNNER = HERE.parent / "highvol_router_v1_dev" / "run_router_dev.py"


def load_dev():
    spec = importlib.util.spec_from_file_location("router_v1_dev_frozen_for_3s", DEV_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(DEV_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_native_1m(root: Path) -> pd.DataFrame:
    base = root / "data/cross_index_risk_gate_v1/1m/000852.SH"
    paths = [base / f"{year}.parquet" for year in range(2020, 2026)]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(missing)
    frames = [pd.read_parquet(p) for p in paths]
    x = pd.concat(frames, ignore_index=True)
    x["trading_day"] = x.trading_day.astype(str).str[:10]
    x["ts"] = pd.to_datetime(x.timestamp.astype(str).str[:19])
    if x.trading_day.min() < "2020-01-01" or x.trading_day.max() > "2025-12-31":
        raise RuntimeError((x.trading_day.min(), x.trading_day.max()))
    return x.sort_values(["trading_day", "ts"], kind="stable").reset_index(drop=True)


def frozen_trades(dev, native: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    minute = dev.build_minute(native)
    minute = minute[(minute.trading_day >= "2021-01-01") & (minute.trading_day <= "2025-12-31")].reset_index(drop=True)
    events = dev.build_onsets(minute)
    qualifying = dev.frozen_qualifying(events)
    trades = dev.apply_nonoverlap(qualifying)
    counts = trades.groupby("year").size().to_dict()
    if counts != EXPECTED_TRADES:
        raise RuntimeError(f"frozen trade identity drift: {counts} != {EXPECTED_TRADES}")
    return minute, trades.reset_index(drop=True)


def choose_column(names: list[str], candidates: tuple[str, ...], kind: str) -> str:
    lower = {name.lower(): name for name in names}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    raise RuntimeError(f"unable to detect {kind} column from {names}")


def parse_local_timestamp(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        out = pd.to_datetime(series, errors="coerce")
        if getattr(out.dt, "tz", None) is not None:
            out = out.dt.tz_localize(None)
        return out
    text = series.astype(str).str[:19]
    return pd.to_datetime(text, errors="coerce")


def load_3s_year(root: Path, year: int, manifest: dict) -> tuple[pd.DataFrame, dict]:
    path = root / f"data/cross_index_risk_gate_3s_v1/000852.SH_{year}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    item = next((x for x in manifest["files"] if x["path"] == path.name), None)
    if item is None:
        raise RuntimeError(f"manifest missing {path.name}")
    physical_sha = sha256(path)
    if physical_sha != item["sha256"]:
        raise RuntimeError(f"3s sha mismatch {year}: {physical_sha} != {item['sha256']}")

    names = pq.ParquetFile(path).schema.names
    time_col = choose_column(
        names,
        ("observation_datetime", "market_observed_at", "timestamp", "datetime", "observed_at", "ts"),
        "observation time",
    )
    price_col = choose_column(
        names,
        ("price", "last_price", "last", "close", "index_price", "value"),
        "price",
    )
    row_col = None
    for cand in ("row_index", "event_seq", "source_row_index", "sequence", "seq"):
        if cand in names:
            row_col = cand
            break
    cols = [time_col, price_col] + ([row_col] if row_col else [])
    z = pd.read_parquet(path, columns=cols)
    z["_ts"] = parse_local_timestamp(z[time_col])
    z["_price"] = pd.to_numeric(z[price_col], errors="coerce")
    if row_col:
        z["_row"] = pd.to_numeric(z[row_col], errors="coerce").fillna(np.inf)
    else:
        z["_row"] = np.arange(len(z), dtype=np.int64)
    z = z[np.isfinite(z._price) & (z._price > 0) & z._ts.notna()].copy()
    z = z.sort_values(["_ts", "_row"], kind="stable").reset_index(drop=True)
    if z.empty:
        raise RuntimeError(f"no valid 3s observations for {year}")
    receipt = {
        "year": year,
        "path": str(path.relative_to(root)),
        "manifest_sha256": item["sha256"],
        "physical_sha256": physical_sha,
        "rows_manifest": int(item["rows"]),
        "valid_rows_loaded": int(len(z)),
        "schema_names": names,
        "time_column": time_col,
        "price_column": price_col,
        "row_order_column": row_col,
        "first_observation": str(z._ts.min()),
        "last_observation": str(z._ts.max()),
    }
    return z[["_ts", "_price", "_row"]], receipt


def target_timestamp(row: pd.Series, minute_field: str) -> pd.Timestamp:
    half = int(str(row.session).rsplit("/", 1)[1])
    base = pd.Timestamp(f"{row.trading_day} {'09:30:00' if half == 0 else '13:00:00'}")
    minute = int(row[minute_field])
    return base + pd.Timedelta(minutes=minute - 1)


def first_after(ts_ns: np.ndarray, prices: np.ndarray, target: pd.Timestamp, delay_sec: int):
    requested = target + pd.Timedelta(seconds=delay_sec)
    requested_ns = requested.value
    end_ns = (target + pd.Timedelta(seconds=60)).value
    i = int(np.searchsorted(ts_ns, requested_ns, side="left"))
    if i >= len(ts_ns) or ts_ns[i] >= end_ns:
        return np.nan, np.nan, None
    px = float(prices[i])
    if not np.isfinite(px) or px <= 0:
        return np.nan, np.nan, None
    latency = float((ts_ns[i] - requested_ns) / 1e9)
    return px, latency, pd.Timestamp(ts_ns[i])


def map_year(trades: pd.DataFrame, obs: pd.DataFrame, year: int) -> pd.DataFrame:
    t = trades[trades.year == year].copy().reset_index(drop=True)
    ts_ns = obs._ts.astype("datetime64[ns]").astype("int64").to_numpy()
    prices = obs._price.to_numpy(float)
    rows = []
    for _, row in t.iterrows():
        entry_target = target_timestamp(row, "entry_minute")
        exit_target = target_timestamp(row, "exit_minute")
        base_gross = float(row.gross_3m_bp)
        for delay in DELAYS_SEC:
            ep, elag, ets = first_after(ts_ns, prices, entry_target, delay)
            xp, xlag, xts = first_after(ts_ns, prices, exit_target, delay)
            matched = bool(np.isfinite(ep) and np.isfinite(xp) and ep > 0 and xp > 0)
            proxy_gross = float(np.log(xp / ep) * 1e4) if matched else np.nan
            rows.append({
                "year": year,
                "trading_day": str(row.trading_day),
                "session": str(row.session),
                "onset_minute": int(row.onset_minute),
                "entry_minute": int(row.entry_minute),
                "exit_minute": int(row.exit_minute),
                "delay_sec": delay,
                "entry_target": entry_target,
                "exit_target": exit_target,
                "entry_observed_at": ets,
                "exit_observed_at": xts,
                "entry_latency_sec": elag,
                "exit_latency_sec": xlag,
                "entry_price_3s_index": ep,
                "exit_price_3s_index": xp,
                "matched": matched,
                "gross_1m_open_bp": base_gross,
                "gross_3s_index_bp": proxy_gross,
                "timing_drift_bp": proxy_gross - base_gross if matched else np.nan,
            })
    return pd.DataFrame(rows)


def stats_one(z: pd.DataFrame, label: str, year_label, delay: int) -> dict:
    q = z[(z.delay_sec == delay)].copy()
    matched = q[q.matched].copy()
    total = int(len(q))
    n = int(len(matched))
    def p95(s):
        a = pd.to_numeric(s, errors="coerce").dropna().to_numpy(float)
        return float(np.quantile(a, 0.95)) if len(a) else np.nan
    def median(s):
        a = pd.to_numeric(s, errors="coerce").dropna().to_numpy(float)
        return float(np.median(a)) if len(a) else np.nan
    base = matched.gross_1m_open_bp.to_numpy(float) if n else np.array([])
    proxy = matched.gross_3s_index_bp.to_numpy(float) if n else np.array([])
    drift = matched.timing_drift_bp.to_numpy(float) if n else np.array([])
    mean_proxy = float(np.mean(proxy)) if n else np.nan
    signs = np.sign(base) == np.sign(proxy) if n else np.array([])
    return {
        "period": label,
        "year": year_label,
        "delay_sec": delay,
        "frozen_trades": total,
        "matched_trades": n,
        "match_rate": float(n / total) if total else np.nan,
        "entry_latency_median_sec": median(matched.entry_latency_sec),
        "entry_latency_p95_sec": p95(matched.entry_latency_sec),
        "exit_latency_median_sec": median(matched.exit_latency_sec),
        "exit_latency_p95_sec": p95(matched.exit_latency_sec),
        "mean_1m_open_gross_bp": float(np.mean(base)) if n else np.nan,
        "median_1m_open_gross_bp": float(np.median(base)) if n else np.nan,
        "mean_3s_index_gross_bp": mean_proxy,
        "median_3s_index_gross_bp": float(np.median(proxy)) if n else np.nan,
        "mean_timing_drift_bp": float(np.mean(drift)) if n else np.nan,
        "median_timing_drift_bp": float(np.median(drift)) if n else np.nan,
        "timing_drift_p05_bp": float(np.quantile(drift, 0.05)) if n else np.nan,
        "timing_drift_p95_bp": float(np.quantile(drift, 0.95)) if n else np.nan,
        "mean_3s_index_net_1bp_per_leg_bp": mean_proxy - 2.0 * PRIMARY_COST_BP_PER_LEG if n else np.nan,
        "one_way_break_even_3s_index_bp": mean_proxy / 2.0 if n else np.nan,
        "gross_sign_agreement": float(np.mean(signs)) if n else np.nan,
    }


def clean_json(obj):
    if isinstance(obj, dict):
        return {str(k): clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        x = float(obj)
        return x if np.isfinite(x) else None
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def run(root: Path, out: Path) -> dict:
    dev = load_dev()
    native = load_native_1m(root)
    _, trades = frozen_trades(dev, native)
    manifest_path = root / "data/cross_index_risk_gate_3s_v1/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest["contract"]["end"] != "2025-12-31":
        raise RuntimeError("3s contract end changed")
    if "2026_rows" not in manifest["contract"]["denied"]:
        raise RuntimeError("3s contract must deny 2026 rows")

    mapped = []
    source_receipts = []
    for year in YEARS:
        obs, receipt = load_3s_year(root, year, manifest)
        source_receipts.append(receipt)
        mapped.append(map_year(trades, obs, year))
    long = pd.concat(mapped, ignore_index=True)

    rows = []
    for delay in DELAYS_SEC:
        for year in YEARS:
            period = "Development" if year in DEV_YEARS else "Validation_2024_2025"
            rows.append(stats_one(long[long.year == year], period, year, delay))
        rows.append(stats_one(long[long.year.isin(DEV_YEARS)], "Development", "pooled", delay))
        rows.append(stats_one(long[long.year.isin(VAL_YEARS)], "Validation_2024_2025", "pooled", delay))
    stats = pd.DataFrame(rows)

    primary = stats[(stats.year == "pooled") & (stats.delay_sec == 0)].copy()
    dev_primary = primary[primary.period == "Development"].iloc[0].to_dict()
    val_primary = primary[primary.period == "Validation_2024_2025"].iloc[0].to_dict()
    flags = []
    if val_primary["match_rate"] < 0.95:
        flags.append("validation_3s_match_rate_below_95pct")
    if val_primary["mean_timing_drift_bp"] < -0.25:
        flags.append("validation_mean_timing_drift_worse_than_minus_0_25bp")
    if val_primary["mean_3s_index_net_1bp_per_leg_bp"] <= 0:
        flags.append("validation_3s_index_proxy_net_nonpositive_at_1bp_per_leg")
    d15 = stats[(stats.period == "Validation_2024_2025") & (stats.year == "pooled") & (stats.delay_sec == 15)].iloc[0]
    if d15.mean_timing_drift_bp < -0.25:
        flags.append("validation_15s_delay_mean_timing_drift_worse_than_minus_0_25bp")

    summary = {
        "schema": "highvol_router_v1_3s_index_timing_audit_v1",
        "diagnostic_only": True,
        "tradable_fill_study": False,
        "candidate_changed": False,
        "routing_changed": False,
        "production_authority": False,
        "blackbox_queried": False,
        "three_second_contract_end": "2025-12-31",
        "three_second_2026_used": False,
        "delays_sec": list(DELAYS_SEC),
        "frozen_trade_counts": {str(y): int((trades.year == y).sum()) for y in YEARS},
        "source_receipts": source_receipts,
        "development_primary_delay0": dev_primary,
        "validation_2024_2025_primary_delay0": val_primary,
        "preset_timing_flags": flags,
        "interpretation": "index_timestamp_semantics_only_not_executable_fill",
    }
    clean = clean_json(summary)

    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "frozen_trades_2021_2025.csv", index=False)
    long.to_csv(out / "trade_timing_long.csv", index=False)
    stats.to_csv(out / "timing_stats.csv", index=False)
    (out / "source_receipts.json").write_text(json.dumps(clean_json(source_receipts), indent=2, allow_nan=False) + "\n")
    (out / "summary.json").write_text(json.dumps(clean, indent=2, allow_nan=False) + "\n")
    print(json.dumps(clean, allow_nan=False))
    print(stats.to_string(index=False))
    return clean


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run(Path(args.repo_root).resolve(), Path(args.out))


if __name__ == "__main__":
    main()
