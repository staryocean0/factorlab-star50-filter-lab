from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
WARMUP_YEAR = 2020
DEV_YEARS = (2021, 2022, 2023)
REF_YEARS = (2020, 2021, 2022, 2023)
STATES = ("UNSAFE", "RECOVERING")
BUCKETS = ("LT15", "M15_25", "M30_40", "GE45")
HORIZONS = (15, 30, 60)
HORIZON_BARS = {15: 3, 30: 6, 60: 12}
RV_WINDOW = 12
BG_WINDOW = 48
HIGHVOL_RATIO = 1.50
RECOVERY_NORMAL_RATIO = 1.10
SHOCK_SIGMA = 3.00
MIN_CELL_N = 100


def wallclock(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str).str.slice(0, 19), errors="coerce")


def load_symbol(root: Path, symbol: str) -> pd.DataFrame:
    base = root / "data/market/5m" / symbol
    got = sorted(p.name for p in base.glob("*.parquet"))
    exp = [f"{y}.parquet" for y in REF_YEARS]
    if got != exp:
        raise RuntimeError(f"Development physical boundary violated for {symbol}: {got} != {exp}")
    parts = []
    for year in REF_YEARS:
        p = base / f"{year}.parquet"
        x = pd.read_parquet(p)
        if "close" not in x.columns:
            raise RuntimeError(f"{p}: missing close")
        if "trading_day" in x.columns:
            day = pd.to_datetime(x.trading_day, errors="coerce")
        else:
            tcol = "timestamp" if "timestamp" in x.columns else "bar_end_shanghai"
            if tcol not in x.columns:
                raise RuntimeError(f"{p}: missing trading_day/timestamp")
            day = wallclock(x[tcol]).dt.normalize()
        if "timestamp" in x.columns:
            ts = wallclock(x.timestamp)
        elif "bar_end_shanghai" in x.columns:
            ts = wallclock(x.bar_end_shanghai)
        else:
            raise RuntimeError(f"{p}: missing timestamp/bar_end_shanghai")
        parts.append(pd.DataFrame({
            "symbol": symbol,
            "trading_day": day.dt.strftime("%Y-%m-%d"),
            "timestamp": ts,
            "close": pd.to_numeric(x.close, errors="coerce"),
        }).dropna())
    z = pd.concat(parts, ignore_index=True)
    return z.sort_values(["trading_day", "timestamp"], kind="stable").drop_duplicates(
        ["trading_day", "timestamp"], keep="last"
    ).reset_index(drop=True)


def restrict_common_days(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    common = None
    for df in frames.values():
        days = set(df.trading_day.unique())
        common = days if common is None else common.intersection(days)
    if not common:
        raise RuntimeError("no common trading days")
    return {s: df[df.trading_day.isin(common)].sort_values(["trading_day", "timestamp"], kind="stable").reset_index(drop=True)
            for s, df in frames.items()}


def transition(prev: str, ratio: float, shock: bool) -> str:
    if shock:
        return "UNSAFE"
    if prev == "UNSAFE":
        if pd.isna(ratio) or ratio >= HIGHVOL_RATIO:
            return "UNSAFE"
        if ratio > RECOVERY_NORMAL_RATIO:
            return "RECOVERING"
        return "NORMAL"
    if prev == "RECOVERING":
        if pd.isna(ratio):
            return "RECOVERING"
        if ratio >= HIGHVOL_RATIO:
            return "UNSAFE"
        if ratio > RECOVERY_NORMAL_RATIO:
            return "RECOVERING"
        return "NORMAL"
    return "NORMAL"


def add_measurements(df: pd.DataFrame) -> pd.DataFrame:
    z = df.copy()
    z["ret_5m"] = z.groupby("trading_day", sort=False).close.transform(lambda s: np.log(s).diff())
    valid = z.ret_5m.dropna()
    z["rv12"] = valid.rolling(RV_WINDOW, min_periods=RV_WINDOW).std(ddof=0).reindex(z.index)
    z["bg_vol48"] = valid.shift(1).rolling(BG_WINDOW, min_periods=BG_WINDOW).std(ddof=0).reindex(z.index)
    z.loc[z.bg_vol48 <= 0, "bg_vol48"] = np.nan
    z["vol_ratio"] = z.rv12 / z.bg_vol48
    z["shock_intensity"] = z.ret_5m.abs() / z.bg_vol48
    z["shock"] = z.shock_intensity >= SHOCK_SIGMA
    risk = pd.Series("NORMAL", index=z.index, dtype="object")
    for _, idx in z.groupby("trading_day", sort=False).groups.items():
        mode = "NORMAL"
        for i in idx:
            mode = transition(mode, z.at[i, "vol_ratio"], bool(z.at[i, "shock"]) if pd.notna(z.at[i, "shock"]) else False)
            risk.at[i] = mode
    z["risk_state"] = risk
    z["year"] = pd.to_datetime(z.trading_day).dt.year.astype(int)
    return z


def age_bucket(bars: int) -> str:
    if bars <= 2:
        return "LT15"
    if bars <= 5:
        return "M15_25"
    if bars <= 8:
        return "M30_40"
    return "GE45"


def build_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    max_h = HORIZON_BARS[60]
    for day_name, z0 in df.groupby("trading_day", sort=False):
        year = int(str(day_name)[:4])
        if year not in DEV_YEARS:
            continue
        day = z0.sort_values("timestamp", kind="stable").reset_index(drop=True)
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
            last_active = occupied
            episode_no += 1
            last_shock = j
            for k in range(j + 1, last_active + 1):
                if bool(day.at[k, "shock"]) if pd.notna(day.at[k, "shock"]) else False:
                    last_shock = k
                    continue
                state = str(day.at[k, "risk_state"])
                if state not in STATES:
                    continue
                recent_age = k - last_shock
                if recent_age <= 0 or k + max_h > int(day.index.max()):
                    continue
                future = day.loc[k + 1:k + max_h]
                out = {}
                for h in HORIZONS:
                    hb = HORIZON_BARS[h]
                    out[f"normal_within_{h}m"] = bool(future.iloc[:hb].risk_state.eq("NORMAL").any())
                if not (out["normal_within_15m"] <= out["normal_within_30m"] <= out["normal_within_60m"]):
                    raise RuntimeError("row-level cumulative recovery nesting violated")
                rows.append({
                    "episode_id": f"{day.at[j, 'symbol']}|{day_name}|{episode_no}",
                    "symbol": str(day.at[j, "symbol"]),
                    "year": year,
                    "trading_day": str(day_name),
                    "timestamp": str(day.at[k, "timestamp"]),
                    "current_state": state,
                    "recent_shock_age_bars": int(recent_age),
                    "age_bucket": age_bucket(recent_age),
                    **out,
                })
    return pd.DataFrame(rows)


def fit_table(rows: pd.DataFrame) -> pd.DataFrame:
    out = []
    for state in STATES:
        for bucket in BUCKETS:
            g = rows[(rows.current_state == state) & (rows.age_bucket == bucket)]
            if g.empty:
                raise RuntimeError(f"missing cell {state}/{bucket}")
            rec = {"current_state": state, "age_bucket": bucket, "n": int(len(g))}
            for h in HORIZONS:
                y = g[f"normal_within_{h}m"].astype(int)
                s = int(y.sum())
                rec[f"success_{h}m"] = s
                rec[f"p_{h}m"] = float((s + 1) / (len(g) + 2))
            out.append(rec)
    return pd.DataFrame(out)


def predict(rows: pd.DataFrame, table: pd.DataFrame, h: int) -> np.ndarray:
    mp = {(r.current_state, r.age_bucket): getattr(r, f"p_{h}m") for r in table.itertuples()}
    return np.array([mp[(s, b)] for s, b in zip(rows.current_state, rows.age_bucket)], float)


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


def cv(rows: pd.DataFrame) -> tuple[list[dict], dict]:
    folds = []
    aggregate = {h: {"y": [], "p": [], "b": []} for h in HORIZONS}
    for held in DEV_YEARS:
        train = rows[rows.year != held]
        test = rows[rows.year == held]
        table = fit_table(train)
        fold = {"held_out_year": held, "horizons": {}}
        for h in HORIZONS:
            y = test[f"normal_within_{h}m"].astype(int).to_numpy()
            p = predict(test, table, h)
            train_y = train[f"normal_within_{h}m"].astype(int)
            base_rate = float((int(train_y.sum()) + 1) / (len(train_y) + 2))
            b = np.full(len(y), base_rate, float)
            sm = score(y, p)
            sb = score(y, b)
            fold["horizons"][str(h)] = {
                "model": sm,
                "baseline": sb,
                "baseline_rate_from_training": base_rate,
                "brier_improvement": float(sb["brier"] - sm["brier"]),
                "logloss_improvement": float(sb["log_loss"] - sm["log_loss"]),
            }
            aggregate[h]["y"].append(y); aggregate[h]["p"].append(p); aggregate[h]["b"].append(b)
        folds.append(fold)
    pooled = {}
    for h in HORIZONS:
        y = np.concatenate(aggregate[h]["y"])
        p = np.concatenate(aggregate[h]["p"])
        b = np.concatenate(aggregate[h]["b"])
        sm = score(y, p); sb = score(y, b)
        pooled[str(h)] = {
            "model": sm,
            "baseline": sb,
            "brier_improvement": float(sb["brier"] - sm["brier"]),
            "logloss_improvement": float(sb["log_loss"] - sm["log_loss"]),
        }
    return folds, pooled


def clean(v):
    if isinstance(v, dict): return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, list): return [clean(x) for x in v]
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating, float)):
        x = float(v); return x if np.isfinite(x) else None
    if isinstance(v, (np.bool_,)): return bool(v)
    return v


def run(root: Path, out: Path) -> dict:
    frames = restrict_common_days({s: load_symbol(root, s) for s in SYMBOLS})
    frames = {s: add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([build_rows(frames[s]) for s in SYMBOLS], ignore_index=True)
    if rows.empty:
        raise RuntimeError("no V11 survival rows")
    final = fit_table(rows)
    folds, pooled_cv = cv(rows)

    monotonic = []
    ordering = []
    idx = final.set_index(["age_bucket", "current_state"])
    for state in STATES:
        for bucket in BUCKETS:
            r = idx.loc[(bucket, state)]
            ok = bool(r.p_15m <= r.p_30m <= r.p_60m)
            monotonic.append({"current_state": state, "age_bucket": bucket, "p15": float(r.p_15m), "p30": float(r.p_30m), "p60": float(r.p_60m), "ordered": ok})
    for h in HORIZONS:
        for bucket in BUCKETS:
            pu = float(idx.at[(bucket, "UNSAFE"), f"p_{h}m"])
            pr = float(idx.at[(bucket, "RECOVERING"), f"p_{h}m"])
            ordering.append({"horizon_minutes": h, "age_bucket": bucket, "unsafe_probability": pu, "recovering_probability": pr, "gap": pr - pu, "ordered": bool(pr > pu)})

    annual_brier_ok = {}
    for h in HORIZONS:
        annual_brier_ok[str(h)] = int(sum(f["horizons"][str(h)]["brier_improvement"] > 0 for f in folds))

    acceptance = {
        "all_8_base_cells_n_ge_100": bool((final.n >= MIN_CELL_N).all()),
        "all_cells_p15_le_p30_le_p60": bool(all(r["ordered"] for r in monotonic)),
        "recovering_gt_unsafe_all_12_horizon_age_views": bool(all(r["ordered"] for r in ordering)),
        "pooled_loo_brier_better_all_3_horizons": bool(all(pooled_cv[str(h)]["brier_improvement"] > 0 for h in HORIZONS)),
        "annual_brier_better_at_least_2_of_3_each_horizon": bool(all(annual_brier_ok[str(h)] >= 2 for h in HORIZONS)),
        "pooled_loo_logloss_better_all_3_horizons": bool(all(pooled_cv[str(h)]["logloss_improvement"] > 0 for h in HORIZONS)),
        "state_thresholds_unchanged": True,
        "age_buckets_unchanged": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }
    summary = {
        "schema": "highvol_recovery_survival_v11_development",
        "development_only": True,
        "development_years": list(DEV_YEARS),
        "warmup_year": WARMUP_YEAR,
        "symbols": list(SYMBOLS),
        "horizons_minutes": list(HORIZONS),
        "full_future_support_minutes": 60,
        "row_count": int(len(rows)),
        "state_thresholds_unchanged": True,
        "age_buckets": list(BUCKETS),
        "threshold_search_performed": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "production_authority": False,
        "final_table": final.to_dict(orient="records"),
        "cumulative_monotonicity": monotonic,
        "recovering_vs_unsafe": ordering,
        "leave_one_year_out": folds,
        "pooled_leave_one_year_out": pooled_cv,
        "annual_brier_improving_fold_count": annual_brier_ok,
        "acceptance": acceptance,
        "survival_curve_validation_eligible": bool(all(acceptance.values())),
    }
    out.mkdir(parents=True, exist_ok=True)
    rows.to_parquet(out / "survival_rows.parquet", index=False)
    final.to_csv(out / "final_survival_table.csv", index=False)
    (out / "summary.json").write_text(json.dumps(clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(clean(summary), sort_keys=True))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.repo_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
