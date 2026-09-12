from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
REF_YEARS = (2020, 2021, 2022, 2023)
DEV_YEARS = (2021, 2022, 2023)
RV_WINDOW = 12
BG_WINDOW = 48
HIGHVOL_RATIO = 1.50
RECOVERY_NORMAL_RATIO = 1.10
SHOCK_SIGMA = 3.00
PRIMARY_LEAD_SECONDS = 3
FUTURE_BARS = 3
STATES = ("UNSAFE", "RECOVERING")
BUCKETS = ("LT15", "M15_25", "M30_40", "GE45")

PROB = {
    ("UNSAFE", "LT15"): 0.007067137809187279,
    ("UNSAFE", "M15_25"): 0.007751937984496124,
    ("UNSAFE", "M30_40"): 0.01340033500837521,
    ("UNSAFE", "GE45"): 0.5284210526315789,
    ("RECOVERING", "LT15"): 0.05555555555555555,
    ("RECOVERING", "M15_25"): 0.04879679144385027,
    ("RECOVERING", "M30_40"): 0.08446215139442231,
    ("RECOVERING", "GE45"): 0.7555919258046918,
}

MIN_POOLED_COVERAGE = 0.98
MIN_ANNUAL_COVERAGE = 0.95
MAX_POOLED_PROB_MAE = 0.01
MAX_POOLED_BRIER_DEGRADATION = 0.002
MAX_ANNUAL_BRIER_DEGRADATION = 0.005


def wallclock(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str).str.slice(0, 19), errors="coerce")


def transition(prev_state: str, ratio: float, is_shock: bool) -> str:
    if is_shock:
        return "UNSAFE"
    if prev_state == "UNSAFE":
        if pd.isna(ratio) or ratio >= HIGHVOL_RATIO:
            return "UNSAFE"
        if ratio > RECOVERY_NORMAL_RATIO:
            return "RECOVERING"
        return "NORMAL"
    if prev_state == "RECOVERING":
        if pd.isna(ratio):
            return "RECOVERING"
        if ratio >= HIGHVOL_RATIO:
            return "UNSAFE"
        if ratio > RECOVERY_NORMAL_RATIO:
            return "RECOVERING"
        return "NORMAL"
    return "NORMAL"


def age_bucket(bars: int) -> str:
    if bars <= 2:
        return "LT15"
    if bars <= 5:
        return "M15_25"
    if bars <= 8:
        return "M30_40"
    return "GE45"


def load_reference(root: Path, symbol: str) -> pd.DataFrame:
    base = root / "data/market/5m" / symbol
    got = sorted(p.name for p in base.glob("*.parquet"))
    expected = [f"{y}.parquet" for y in REF_YEARS]
    if got != expected:
        raise RuntimeError(f"5m physical boundary violation {symbol}: {got}")
    parts = []
    for year in REF_YEARS:
        x = pd.read_parquet(base / f"{year}.parquet")
        z = pd.DataFrame({
            "symbol": symbol,
            "trading_day": pd.to_datetime(x.trading_day, errors="coerce").dt.strftime("%Y-%m-%d"),
            "bar_end": wallclock(x.timestamp),
            "close": pd.to_numeric(x.close, errors="coerce"),
        }).dropna()
        parts.append(z)
    z = pd.concat(parts, ignore_index=True).sort_values(["trading_day", "bar_end"], kind="stable").reset_index(drop=True)
    counts = z.groupby("trading_day").size()
    if len(counts[counts != 48]):
        raise RuntimeError("reference contains non-48-row day")
    z["ret_5m"] = z.groupby("trading_day", sort=False).close.transform(lambda s: np.log(s).diff())
    valid = z.ret_5m.dropna()
    z["rv12"] = valid.rolling(RV_WINDOW, min_periods=RV_WINDOW).std(ddof=0).reindex(z.index)
    z["bg_vol48"] = valid.shift(1).rolling(BG_WINDOW, min_periods=BG_WINDOW).std(ddof=0).reindex(z.index)
    z.loc[z.bg_vol48 <= 0, "bg_vol48"] = np.nan
    z["vol_ratio"] = z.rv12 / z.bg_vol48
    z["shock_intensity"] = z.ret_5m.abs() / z.bg_vol48
    z["shock"] = z.shock_intensity >= SHOCK_SIGMA
    state = pd.Series("NORMAL", index=z.index, dtype="object")
    for _, idx in z.groupby("trading_day", sort=False).groups.items():
        mode = "NORMAL"
        for i in idx:
            mode = transition(mode, z.at[i, "vol_ratio"], bool(z.at[i, "shock"]) if pd.notna(z.at[i, "shock"]) else False)
            state.at[i] = mode
    z["risk_state"] = state
    z["prev_state"] = z.groupby("trading_day", sort=False).risk_state.shift(1).fillna("NORMAL")
    z["prev_close"] = z.groupby("trading_day", sort=False).close.shift(1)
    z["year"] = pd.to_datetime(z.trading_day).dt.year.astype(int)
    return z


def prior_windows(z: pd.DataFrame) -> dict[int, np.ndarray]:
    valid = z.ret_5m.dropna()
    vals = valid.to_numpy(float)
    ids = list(valid.index)
    out: dict[int, np.ndarray] = {}
    for pos, idx in enumerate(ids):
        if pos >= RV_WINDOW - 1:
            out[int(idx)] = vals[pos - (RV_WINDOW - 1):pos].copy()
    return out


def load_3s(root: Path, symbol: str, year: int) -> pd.DataFrame:
    p = root / "data/cross_index_risk_gate_3s_v1" / f"{symbol}_{year}.parquet"
    if not p.exists():
        raise RuntimeError(f"missing 3s {p}")
    x = pd.read_parquet(p, columns=["trading_day", "observation_time", "price", "row_index"])
    x["trading_day"] = pd.to_datetime(x.trading_day, errors="coerce").dt.strftime("%Y-%m-%d")
    x["obs_dt"] = pd.to_datetime(x.trading_day + " " + x.observation_time.astype(str), errors="coerce")
    x["price"] = pd.to_numeric(x.price, errors="coerce")
    x["row_index"] = pd.to_numeric(x.row_index, errors="coerce")
    x = x.dropna(subset=["trading_day", "obs_dt", "price", "row_index"])
    return x.sort_values(["trading_day", "obs_dt", "row_index"], kind="stable").reset_index(drop=True)


def select_checkpoint(obs: pd.DataFrame, start: pd.Timestamp, target: pd.Timestamp):
    if obs.empty:
        return None
    times = obs.obs_dt.to_numpy(dtype="datetime64[ns]")
    pos = int(np.searchsorted(times, np.datetime64(target.to_datetime64()), side="right") - 1)
    if pos < 0:
        return None
    row = obs.iloc[pos]
    if row.obs_dt < start:
        return None
    return float(row.price), pd.Timestamp(row.obs_dt)


def future_outcome(day: pd.DataFrame, k: int):
    last = int(day.index.max())
    horizon_end = k + FUTURE_BARS
    if horizon_end > last:
        return None
    future = day.loc[k + 1:horizon_end]
    return bool(future.risk_state.eq("NORMAL").any())


def reference_rows(ref: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for day_name, z0 in ref.groupby("trading_day", sort=False):
        year = int(str(day_name)[:4])
        if year not in DEV_YEARS:
            continue
        day = z0.sort_values("bar_end", kind="stable").reset_index().rename(columns={"index": "global_idx"})
        prev_unsafe = day.risk_state.shift(1).eq("UNSAFE").fillna(False)
        starts = list(day.index[day.shock.fillna(False).astype(bool) & ~prev_unsafe])
        occupied = -1
        episode_no = 0
        for j0 in starts:
            j = int(j0)
            if j <= occupied:
                continue
            normals = day.index[(day.index > j) & day.risk_state.eq("NORMAL")]
            end = int(normals[0]) if len(normals) else None
            occupied = (end - 1) if end is not None else int(day.index.max())
            episode_no += 1
            last_shock = j
            last_active = (end - 1) if end is not None else int(day.index.max())
            for k in range(j + 1, last_active + 1):
                if bool(day.at[k, "shock"]) if pd.notna(day.at[k, "shock"]) else False:
                    last_shock = k
                    continue
                state = str(day.at[k, "risk_state"])
                if state not in STATES:
                    continue
                y = future_outcome(day, k)
                if y is None:
                    continue
                age = k - last_shock
                if age <= 0:
                    continue
                b = age_bucket(age)
                rows.append({
                    "symbol": str(day.at[k, "symbol"]),
                    "year": year,
                    "trading_day": str(day_name),
                    "episode_no": episode_no,
                    "global_idx": int(day.at[k, "global_idx"]),
                    "bar_end": pd.Timestamp(day.at[k, "bar_end"]),
                    "reference_state": state,
                    "reference_shock": False,
                    "recent_shock_age_bars": age,
                    "age_bucket": b,
                    "reference_probability": PROB[(state, b)],
                    "normal_within_next15": bool(y),
                })
    return pd.DataFrame(rows)


def attach_realtime(root: Path, ref: pd.DataFrame, rows: pd.DataFrame, symbol: str) -> pd.DataFrame:
    windows = prior_windows(ref)
    obs_by_year = {y: load_3s(root, symbol, y) for y in DEV_YEARS}
    obs_day = {}
    for y, sec in obs_by_year.items():
        for d, g in sec.groupby("trading_day", sort=False):
            obs_day[(y, d)] = g.reset_index(drop=True)
    out = []
    for r in rows.itertuples(index=False):
        idx = int(r.global_idx)
        rr = ref.loc[idx]
        row = r._asdict()
        if idx not in windows or pd.isna(rr.prev_close) or pd.isna(rr.bg_vol48):
            row.update({"realtime_probability": np.nan, "realtime_reason": "missing_reference_window"})
            out.append(row)
            continue
        sec = obs_day.get((int(r.year), str(r.trading_day)), pd.DataFrame())
        target = pd.Timestamp(r.bar_end) - pd.Timedelta(seconds=PRIMARY_LEAD_SECONDS)
        start = pd.Timestamp(r.bar_end) - pd.Timedelta(minutes=5)
        sel = select_checkpoint(sec, start, target)
        if sel is None:
            row.update({"realtime_probability": np.nan, "realtime_reason": "missing_3s_checkpoint"})
            out.append(row)
            continue
        price, obs_time = sel
        pret = float(np.log(price) - np.log(float(rr.prev_close)))
        prv = float(np.std(np.concatenate([windows[idx], [pret]]), ddof=0))
        ratio = prv / float(rr.bg_vol48)
        pint = abs(pret) / float(rr.bg_vol48)
        pshock = bool(pint >= SHOCK_SIGMA)
        pstate = transition(str(rr.prev_state), ratio, pshock)
        row.update({
            "selected_observation_time": obs_time,
            "staleness_seconds": float((target - obs_time).total_seconds()),
            "partial_state": pstate,
            "partial_shock": pshock,
            "partial_vol_ratio": ratio,
            "partial_shock_intensity": pint,
        })
        if pshock:
            row.update({"realtime_probability": np.nan, "realtime_reason": "fresh_shock"})
        elif pstate not in STATES:
            row.update({"realtime_probability": np.nan, "realtime_reason": "partial_normal"})
        else:
            row.update({"realtime_probability": PROB[(pstate, str(r.age_bucket))], "realtime_reason": "scored"})
        out.append(row)
    return pd.DataFrame(out)


def score(y, p):
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    q = np.clip(p, 1e-12, 1 - 1e-12)
    return {
        "n": int(len(y)),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))),
        "observed_rate": float(np.mean(y)),
        "mean_prediction": float(np.mean(p)),
    }


def summarize(x: pd.DataFrame, group_type: str, group_value: str) -> dict:
    matched = x[x.realtime_probability.notna()].copy()
    n = int(len(x)); m = int(len(matched))
    ref_all = score(x.normal_within_next15.astype(int), x.reference_probability)
    ref_match = score(matched.normal_within_next15.astype(int), matched.reference_probability) if m else None
    rt = score(matched.normal_within_next15.astype(int), matched.realtime_probability) if m else None
    return {
        "group_type": group_type,
        "group_value": group_value,
        "reference_rows": n,
        "realtime_scored_rows": m,
        "realtime_probability_coverage": float(m / n) if n else None,
        "exact_state_agreement": float(matched.partial_state.eq(matched.reference_state).mean()) if m else None,
        "exact_probability_cell_agreement": float(np.isclose(matched.realtime_probability, matched.reference_probability, rtol=0, atol=1e-15).mean()) if m else None,
        "probability_mae_vs_reference": float(np.mean(np.abs(matched.realtime_probability - matched.reference_probability))) if m else None,
        "reference_all": ref_all,
        "reference_matched": ref_match,
        "realtime_matched": rt,
        "brier_degradation_matched": float(rt["brier"] - ref_match["brier"]) if m else None,
        "logloss_degradation_matched": float(rt["log_loss"] - ref_match["log_loss"]) if m else None,
        "fresh_shock_unscorable": int((x.realtime_reason == "fresh_shock").sum()),
        "partial_normal_unscorable": int((x.realtime_reason == "partial_normal").sum()),
        "missing_checkpoint_unscorable": int((x.realtime_reason == "missing_3s_checkpoint").sum()),
    }


def clean(v):
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        x = float(v)
        return x if np.isfinite(x) else None
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def run(root: Path, out: Path) -> dict:
    pieces = []
    for symbol in SYMBOLS:
        ref = load_reference(root, symbol)
        rr = reference_rows(ref)
        pieces.append(attach_realtime(root, ref, rr, symbol))
    detail = pd.concat(pieces, ignore_index=True)
    summaries = [summarize(detail, "pooled", "pooled")]
    for y in DEV_YEARS:
        summaries.append(summarize(detail[detail.year.eq(y)], "year", str(y)))
    for s in SYMBOLS:
        summaries.append(summarize(detail[detail.symbol.eq(s)], "symbol", s))
    pooled = summaries[0]
    annual = [r for r in summaries if r["group_type"] == "year"]
    acceptance = {
        "pooled_coverage_ge_098": pooled["realtime_probability_coverage"] >= MIN_POOLED_COVERAGE,
        "each_year_coverage_ge_095": all(r["realtime_probability_coverage"] >= MIN_ANNUAL_COVERAGE for r in annual),
        "pooled_probability_mae_le_001": pooled["probability_mae_vs_reference"] <= MAX_POOLED_PROB_MAE,
        "pooled_brier_degradation_le_0002": pooled["brier_degradation_matched"] <= MAX_POOLED_BRIER_DEGRADATION,
        "each_year_brier_degradation_le_0005": all(r["brier_degradation_matched"] <= MAX_ANNUAL_BRIER_DEGRADATION for r in annual),
        "v6_probability_table_unchanged": True,
        "v8_state_thresholds_unchanged": True,
        "primary_checkpoint_is_E_minus_3s": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }
    summary = {
        "schema": "highvol_realtime_risk_object_v9_development",
        "development_only": True,
        "development_period": ["2021-01-01", "2023-12-31"],
        "symbols": list(SYMBOLS),
        "primary_lead_seconds": PRIMARY_LEAD_SECONDS,
        "probability_target": "Normal within next 15 minutes",
        "frozen_v6_probability_table": [{"state": s, "age_bucket": b, "probability": PROB[(s, b)]} for s in STATES for b in BUCKETS],
        "threshold_search_performed": False,
        "state_thresholds_unchanged": True,
        "probability_fit_performed": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "production_authority": False,
        "summary_rows": summaries,
        "acceptance": acceptance,
        "realtime_risk_object_validation_eligible": bool(all(acceptance.values())),
    }
    out.mkdir(parents=True, exist_ok=True)
    detail.to_parquet(out / "detail.parquet", index=False)
    (out / "summary.json").write_text(json.dumps(clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(clean(summary), sort_keys=True))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    run(a.repo_root.resolve(), a.out.resolve())


if __name__ == "__main__":
    main()
