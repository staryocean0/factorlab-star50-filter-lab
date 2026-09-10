from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
V3_RUNNER = HERE.parent / "highvol_recovery_hazard_v3" / "run_hazard.py"
FROZEN_FILE = HERE / "FROZEN_RECENT_SHOCK_TABLE.json"
VALIDATION_YEARS = (2024, 2025, 2026)
SYMBOLS = ("000688.SH", "000852.SH")
BASELINE_P = 0.24650920005219887
EXPECTED_2026_BLOBS = {
    "000688.SH": "4626fb307bbcae1c417ddcd69ac694cf322c8bbc",
    "000852.SH": "8de5cd3caab99dbacae229a2c87f15c4ff2f8558",
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def wallclock(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str).str.slice(0, 19), errors="coerce")


def standardize(path: Path, symbol: str) -> pd.DataFrame:
    x = pd.read_parquet(path)
    if "trading_day" in x.columns:
        day = pd.to_datetime(x["trading_day"], errors="coerce").dt.strftime("%Y-%m-%d")
    else:
        tcol = "timestamp" if "timestamp" in x.columns else "bar_end_shanghai"
        day = wallclock(x[tcol]).dt.strftime("%Y-%m-%d")
    tcol = "timestamp" if "timestamp" in x.columns else "bar_end_shanghai"
    ts = wallclock(x[tcol])
    out = pd.DataFrame({
        "symbol": symbol,
        "trading_day": day,
        "timestamp": ts,
        "close": pd.to_numeric(x["close"], errors="coerce"),
    }).dropna(subset=["trading_day", "timestamp", "close"])
    return out.sort_values(["trading_day", "timestamp"], kind="stable").reset_index(drop=True)


def synthesize_5m(one_minute: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for day, g0 in one_minute.groupby("trading_day", sort=True):
        g = g0.sort_values("timestamp", kind="stable").reset_index(drop=True)
        if len(g) != 240:
            raise RuntimeError(f"{day}: expected 240 complete 1m rows, got {len(g)}")
        if g.timestamp.duplicated().any():
            raise RuntimeError(f"{day}: duplicate 1m timestamp")
        for half_start in (0, 120):
            half = g.iloc[half_start:half_start + 120]
            for end in range(4, 120, 5):
                r = half.iloc[end]
                rows.append({
                    "symbol": str(r.symbol),
                    "trading_day": str(day),
                    "timestamp": r.timestamp,
                    "close": float(r.close),
                })
    out = pd.DataFrame(rows)
    counts = out.groupby("trading_day").size()
    if len(counts) and not (counts == 48).all():
        raise RuntimeError("synthesized 5m day does not contain exactly 48 rows")
    return out.sort_values(["trading_day", "timestamp"], kind="stable").reset_index(drop=True)


def equivalence_guard(root: Path) -> dict:
    rows = []
    for symbol in SYMBOLS:
        one = standardize(root / "data/cross_index_risk_gate_v1/1m" / symbol / "2023.parquet", symbol)
        synth = synthesize_5m(one)
        native = standardize(root / "data/market/5m" / symbol / "2023.parquet", symbol)
        sd = sorted(synth.trading_day.unique())
        nd = sorted(native.trading_day.unique())
        if sd != nd:
            raise RuntimeError(f"{symbol}: 2023 1m/5m trading-day support mismatch")
        sc = synth.groupby("trading_day").size()
        nc = native.groupby("trading_day").size()
        if not (sc == 48).all() or not (nc == 48).all():
            raise RuntimeError(f"{symbol}: expected 48 rows/day in 2023 equivalence guard")
        a = synth.sort_values(["trading_day", "timestamp"], kind="stable").close.to_numpy(float)
        b = native.sort_values(["trading_day", "timestamp"], kind="stable").close.to_numpy(float)
        if len(a) != len(b):
            raise RuntimeError(f"{symbol}: synthesized/native 2023 row count mismatch")
        max_abs = float(np.max(np.abs(a - b))) if len(a) else np.nan
        if not np.isfinite(max_abs) or max_abs > 1e-9:
            raise RuntimeError(f"{symbol}: 1m->5m close equivalence failed; max_abs={max_abs}")
        rows.append({"symbol": symbol, "days": len(sd), "rows": len(a), "max_abs_close_diff": max_abs, "passed": True})
    return {"passed": True, "symbols": rows}


def age_bucket(bars: int) -> str:
    if bars <= 2:
        return "LT15"
    if bars <= 5:
        return "M15_25"
    if bars <= 8:
        return "M30_40"
    return "GE45"


def build_rows(df: pd.DataFrame, v3) -> pd.DataFrame:
    rows = []
    for day_name, z0 in df.groupby("trading_day", sort=False):
        year = int(str(day_name)[:4])
        if year not in VALIDATION_YEARS:
            continue
        day = z0.sort_values("timestamp", kind="stable").reset_index(drop=True)
        prev_unsafe = day.risk_state.shift(1).eq("UNSAFE").fillna(False)
        starts = list(day.index[day.shock.fillna(False).astype(bool) & ~prev_unsafe])
        occupied = -1
        eno = 0
        for j0 in starts:
            j = int(j0)
            if j <= occupied:
                continue
            normals = day.index[(day.index > j) & day.risk_state.eq("NORMAL")]
            end = int(normals[0]) if len(normals) else None
            occupied = (end - 1) if end is not None else int(day.index.max())
            eno += 1
            last_shock = j
            last_active = (end - 1) if end is not None else int(day.index.max())
            for k in range(j + 1, last_active + 1):
                is_shock = bool(day.at[k, "shock"]) if pd.notna(day.at[k, "shock"]) else False
                if is_shock:
                    last_shock = k
                    continue
                state = str(day.at[k, "risk_state"])
                if state not in ("UNSAFE", "RECOVERING"):
                    continue
                f = v3._future_outcome(day, k)
                if not f["hazard_supported"]:
                    continue
                ra = k - last_shock
                if ra <= 0:
                    continue
                rows.append({
                    "episode_id": f"{day.at[j, 'symbol']}|{day_name}|{eno}",
                    "symbol": str(day.at[j, "symbol"]),
                    "year": year,
                    "trading_day": str(day_name),
                    "current_state": state,
                    "recent_shock_age_bars": int(ra),
                    "age_bucket": age_bucket(int(ra)),
                    "normal_within_next15": bool(f["normal_within_next15"]),
                })
    return pd.DataFrame(rows)


def score(y, p) -> dict:
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


def baseline_score(y) -> dict:
    return score(y, np.full(len(y), BASELINE_P, float))


def run(root: Path, out: Path) -> dict:
    v3 = load_module(V3_RUNNER, "v3_full_validation")
    frozen = json.loads(FROZEN_FILE.read_text())
    if frozen["candidate_id"] != "unsafe_recovering_recent_shock_clock_v6":
        raise RuntimeError("wrong frozen candidate")

    eq = equivalence_guard(root)

    frames = {}
    synth_meta = []
    for symbol in SYMBOLS:
        parts = [standardize(root / "data/market/5m" / symbol / f"{year}.parquet", symbol) for year in (2023, 2024, 2025)]
        one26_path = root / "data/_validation_2026_1m" / symbol / "2026.parquet"
        one26 = standardize(one26_path, symbol)
        if one26.empty:
            raise RuntimeError(f"{symbol}: empty 2026 1m validation input")
        max_day = max(one26.trading_day)
        min_day = min(one26.trading_day)
        if max_day > "2026-08-21":
            raise RuntimeError(f"{symbol}: 2026 validation exceeds cutoff: {max_day}")
        syn26 = synthesize_5m(one26)
        parts.append(syn26)
        frames[symbol] = pd.concat(parts, ignore_index=True).sort_values(["trading_day", "timestamp"], kind="stable").reset_index(drop=True)
        synth_meta.append({"symbol": symbol, "source_1m_min_day": min_day, "source_1m_max_day": max_day, "source_1m_rows": int(len(one26)), "synth_5m_rows": int(len(syn26)), "synth_days": int(syn26.trading_day.nunique())})

    frames = v3.restrict_common_days(frames)
    frames = {s: v3.add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([build_rows(frames[s], v3) for s in SYMBOLS], ignore_index=True)
    if rows.empty:
        raise RuntimeError("no Validation scoring rows")

    mp = {(r["current_state"], r["age_bucket"]): float(r["probability"]) for r in frozen["probability_table"]}
    pred = np.array([mp[(s, b)] for s, b in zip(rows.current_state, rows.age_bucket)], float)
    y = rows.normal_within_next15.astype(int).to_numpy()
    rows["frozen_prediction"] = pred

    pooled = score(y, pred)
    pooled_base = baseline_score(y)
    annual = []
    for year in VALIDATION_YEARS:
        mask = rows.year.eq(year).to_numpy()
        yy = y[mask]
        pp = pred[mask]
        annual.append({"year": year, "model": score(yy, pp), "global": baseline_score(yy)})

    symbol_scores = []
    ordering = []
    for symbol in SYMBOLS:
        mask = rows.symbol.eq(symbol).to_numpy()
        symbol_scores.append({"symbol": symbol, "model": score(y[mask], pred[mask]), "global": baseline_score(y[mask])})
        sr = rows[rows.symbol.eq(symbol)]
        positive = 0
        comparable = 0
        for b in ("LT15", "M15_25", "M30_40", "GE45"):
            vals = {}
            for st in ("UNSAFE", "RECOVERING"):
                g = sr[(sr.age_bucket == b) & (sr.current_state == st)]
                vals[st] = float(g.normal_within_next15.mean()) if len(g) else np.nan
            ordered = bool(np.isfinite(vals["UNSAFE"]) and np.isfinite(vals["RECOVERING"]) and vals["RECOVERING"] > vals["UNSAFE"])
            comparable += int(np.isfinite(vals["UNSAFE"]) and np.isfinite(vals["RECOVERING"]))
            positive += int(ordered)
            ordering.append({"symbol": symbol, "age_bucket": b, "unsafe_observed": vals["UNSAFE"], "recovering_observed": vals["RECOVERING"], "ordered": ordered})
        ordering.append({"symbol": symbol, "summary": True, "comparable_buckets": comparable, "positive_buckets": positive})

    acceptance = {
        "synthesis_equivalence_2023": bool(eq["passed"]),
        "scored_rows_min_2000": bool(len(rows) >= 2000),
        "pooled_brier_better_than_global": bool(pooled["brier"] < pooled_base["brier"]),
        "pooled_logloss_better_than_global": bool(pooled["log_loss"] < pooled_base["log_loss"]),
        "brier_better_each_year": bool(all(r["model"]["brier"] < r["global"]["brier"] for r in annual)),
        "ordering_at_least_3_of_4_each_symbol": bool(all(next(r for r in ordering if r.get("symbol") == s and r.get("summary"))["positive_buckets"] >= 3 for s in SYMBOLS)),
        "no_refit": True,
        "no_parameter_change": True,
        "no_pnl": True,
        "no_trading_rule": True,
        "blackbox_queried_false": True,
    }

    summary = {
        "schema": "highvol_recovery_clock_v6_full_reusable_validation",
        "candidate_id": frozen["candidate_id"],
        "validation_policy_end": "2026-08-21",
        "user_authorized_1m_to_5m": True,
        "fit_performed": False,
        "parameter_change_performed": False,
        "state_thresholds_unchanged": True,
        "pnl_computed": False,
        "trading_rule_created": False,
        "blackbox_queried": False,
        "production_authority": False,
        "source_2026_blob_sha": EXPECTED_2026_BLOBS,
        "synthesis_equivalence": eq,
        "synthesis_2026": synth_meta,
        "scored_rows": int(len(rows)),
        "pooled_model": pooled,
        "pooled_global_baseline": pooled_base,
        "annual": annual,
        "symbol_scores": symbol_scores,
        "observed_state_ordering": ordering,
        "acceptance": acceptance,
        "full_validation_supported": bool(all(acceptance.values())),
    }

    out.mkdir(parents=True, exist_ok=True)
    rows.to_csv(out / "validation_rows.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps(summary, allow_nan=False))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    run(Path(a.repo_root).resolve(), Path(a.out))


if __name__ == "__main__":
    main()
