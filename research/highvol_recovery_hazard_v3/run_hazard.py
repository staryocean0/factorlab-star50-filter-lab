from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
WARMUP_YEAR = 2020
DEV_YEARS = (2021, 2022, 2023)
RV_WINDOW = 12
BG_WINDOW = 48
HIGHVOL_RATIO = 1.50
EXTREME_RATIO = 2.25
RECOVERY_NORMAL_RATIO = 1.10
SHOCK_SIGMA = 3.00
LANDMARKS = (1, 3, 6, 9)
FUTURE_BARS = 3


def _wall_clock(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series.astype(str).str.slice(0, 19), errors="coerce")


def load_symbol(root: Path, symbol: str) -> pd.DataFrame:
    base = root / "data/market/5m" / symbol
    expected = [f"{y}.parquet" for y in (WARMUP_YEAR, *DEV_YEARS)]
    present = sorted(p.name for p in base.glob("*.parquet"))
    if present != expected:
        raise RuntimeError(f"Development physical boundary violated for {symbol}: {present}")
    frames: list[pd.DataFrame] = []
    for year in (WARMUP_YEAR, *DEV_YEARS):
        p = base / f"{year}.parquet"
        x = pd.read_parquet(p)
        if "close" not in x.columns:
            raise RuntimeError(f"{p}: missing close")
        if "trading_day" in x.columns:
            day = pd.to_datetime(x["trading_day"], errors="coerce")
        else:
            tcol = "timestamp" if "timestamp" in x.columns else "bar_end_shanghai"
            if tcol not in x.columns:
                raise RuntimeError(f"{p}: missing trading_day/timestamp")
            day = _wall_clock(x[tcol]).dt.normalize()
        if "timestamp" in x.columns:
            ts = _wall_clock(x["timestamp"])
        elif "bar_end_shanghai" in x.columns:
            ts = _wall_clock(x["bar_end_shanghai"])
        else:
            raise RuntimeError(f"{p}: missing timestamp/bar_end_shanghai")
        y = pd.DataFrame(
            {
                "symbol": symbol,
                "trading_day": day.dt.strftime("%Y-%m-%d"),
                "timestamp": ts,
                "close": pd.to_numeric(x["close"], errors="coerce"),
            }
        ).dropna(subset=["trading_day", "timestamp", "close"])
        frames.append(y)
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(["trading_day", "timestamp"], kind="stable")
    out = out.drop_duplicates(["trading_day", "timestamp"], keep="last").reset_index(drop=True)
    return out


def restrict_common_days(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    common: set[str] | None = None
    for df in frames.values():
        days = set(df["trading_day"].unique())
        common = days if common is None else common.intersection(days)
    if not common:
        raise RuntimeError("no common trading days")
    keep = sorted(common)
    return {
        s: df[df["trading_day"].isin(keep)].sort_values(["trading_day", "timestamp"], kind="stable").reset_index(drop=True)
        for s, df in frames.items()
    }


def add_measurements(df: pd.DataFrame) -> pd.DataFrame:
    z = df.copy()
    z["ret_5m"] = z.groupby("trading_day", sort=False)["close"].transform(lambda s: np.log(s).diff())
    valid = z["ret_5m"].dropna()
    rv = valid.rolling(RV_WINDOW, min_periods=RV_WINDOW).std(ddof=0)
    bg = valid.shift(1).rolling(BG_WINDOW, min_periods=BG_WINDOW).std(ddof=0)
    z["rv12"] = rv.reindex(z.index)
    z["bg_vol48"] = bg.reindex(z.index)
    z.loc[z["bg_vol48"] <= 0, "bg_vol48"] = np.nan
    z["vol_ratio"] = z["rv12"] / z["bg_vol48"]
    z["shock_intensity"] = z["ret_5m"].abs() / z["bg_vol48"]
    z["shock"] = z["shock_intensity"] >= SHOCK_SIGMA

    risk = pd.Series("NORMAL", index=z.index, dtype="object")
    for _, idx in z.groupby("trading_day", sort=False).groups.items():
        mode = "NORMAL"
        for i in idx:
            ratio = z.at[i, "vol_ratio"]
            is_shock = bool(z.at[i, "shock"]) if pd.notna(z.at[i, "shock"]) else False
            if is_shock:
                mode = "UNSAFE"
            elif mode == "UNSAFE":
                if pd.isna(ratio) or ratio >= HIGHVOL_RATIO:
                    mode = "UNSAFE"
                elif ratio > RECOVERY_NORMAL_RATIO:
                    mode = "RECOVERING"
                else:
                    mode = "NORMAL"
            elif mode == "RECOVERING":
                if pd.isna(ratio):
                    mode = "RECOVERING"
                elif ratio >= HIGHVOL_RATIO:
                    mode = "UNSAFE"
                elif ratio > RECOVERY_NORMAL_RATIO:
                    mode = "RECOVERING"
                else:
                    mode = "NORMAL"
            else:
                mode = "NORMAL"
            risk.at[i] = mode
    z["risk_state"] = risk
    z["year"] = pd.to_datetime(z["trading_day"]).dt.year.astype(int)
    return z


def _future_outcome(day: pd.DataFrame, k: int) -> dict:
    last = int(day.index.max())
    horizon_end = k + FUTURE_BARS
    future = day.loc[k + 1 : min(horizon_end, last)] if k < last else day.iloc[0:0]
    normal_idx = future.index[future["risk_state"].eq("NORMAL")]
    if len(normal_idx):
        first_normal = int(normal_idx[0])
        before_normal = day.loc[k + 1 : first_normal - 1] if first_normal > k + 1 else day.iloc[0:0]
        recurrence = bool(before_normal["shock"].fillna(False).astype(bool).any()) if len(before_normal) else False
        return {
            "hazard_supported": True,
            "normal_within_next15": True,
            "shock_before_normal_next15": recurrence,
            "non_normal_after15": False,
        }
    if horizon_end <= last:
        full = day.loc[k + 1 : horizon_end]
        recurrence = bool(full["shock"].fillna(False).astype(bool).any())
        return {
            "hazard_supported": True,
            "normal_within_next15": False,
            "shock_before_normal_next15": recurrence,
            "non_normal_after15": bool(day.at[horizon_end, "risk_state"] != "NORMAL"),
        }
    return {
        "hazard_supported": False,
        "normal_within_next15": None,
        "shock_before_normal_next15": None,
        "non_normal_after15": None,
    }


def build_landmarks(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    episode_rows: list[dict] = []
    landmark_rows: list[dict] = []
    for day_name, z0 in df.groupby("trading_day", sort=False):
        year = int(str(day_name)[:4])
        if year not in DEV_YEARS:
            continue
        day = z0.sort_values("timestamp", kind="stable").reset_index(drop=True)
        prev_unsafe = day["risk_state"].shift(1).eq("UNSAFE").fillna(False)
        starts = list(day.index[day["shock"].fillna(False).astype(bool) & ~prev_unsafe])
        occupied_until = -1
        episode_no = 0
        for j in starts:
            j = int(j)
            if j <= occupied_until:
                continue
            normals = day.index[(day.index > j) & day["risk_state"].eq("NORMAL")]
            if len(normals):
                end_j = int(normals[0])
                recovered = True
            else:
                end_j = int(day.index.max())
                recovered = False
            occupied_until = end_j - 1 if recovered else end_j
            episode_no += 1
            episode_id = f"{day.at[j, 'symbol']}|{day_name}|{episode_no}"
            path_pre_normal = day.loc[j : end_j - 1] if recovered and end_j > j else day.loc[j:end_j]
            recurrent = path_pre_normal.iloc[1:]["shock"].fillna(False).astype(bool) if len(path_pre_normal) > 1 else pd.Series(dtype=bool)
            episode_rows.append(
                {
                    "episode_id": episode_id,
                    "symbol": str(day.at[j, "symbol"]),
                    "year": year,
                    "trading_day": str(day_name),
                    "start_timestamp": str(day.at[j, "timestamp"]),
                    "start_vol_ratio": float(day.at[j, "vol_ratio"]) if pd.notna(day.at[j, "vol_ratio"]) else np.nan,
                    "start_shock_intensity": float(day.at[j, "shock_intensity"]) if pd.notna(day.at[j, "shock_intensity"]) else np.nan,
                    "same_day_normal_recovered": bool(recovered),
                    "bars_to_normal": int(end_j - j) if recovered else np.nan,
                    "right_censored": bool(not recovered),
                    "recurrent_shock_before_normal": bool(recurrent.any()) if len(recurrent) else False,
                }
            )
            for lm in LANDMARKS:
                k = j + lm
                if k > int(day.index.max()):
                    continue
                already_normal = bool(recovered and end_j <= k)
                row = {
                    "episode_id": episode_id,
                    "symbol": str(day.at[j, "symbol"]),
                    "year": year,
                    "trading_day": str(day_name),
                    "landmark_bars": lm,
                    "landmark_minutes": 5 * lm,
                    "landmark_observable": True,
                    "already_normal_by_landmark": already_normal,
                    "active_at_landmark": not already_normal,
                    "current_state": "NORMAL" if already_normal else str(day.at[k, "risk_state"]),
                    "current_vol_ratio": float(day.at[k, "vol_ratio"]) if pd.notna(day.at[k, "vol_ratio"]) else np.nan,
                    "current_shock": bool(day.at[k, "shock"]) if pd.notna(day.at[k, "shock"]) else False,
                }
                if already_normal:
                    row.update(
                        {
                            "hazard_supported": False,
                            "normal_within_next15": None,
                            "shock_before_normal_next15": None,
                            "non_normal_after15": None,
                        }
                    )
                else:
                    if row["current_state"] not in {"UNSAFE", "RECOVERING"}:
                        raise RuntimeError(f"active episode has invalid state {row['current_state']}")
                    row.update(_future_outcome(day, k))
                landmark_rows.append(row)
    return pd.DataFrame(episode_rows), pd.DataFrame(landmark_rows)


def _frac(x: pd.Series) -> float:
    return float(x.mean()) if len(x) else np.nan


def summarize_landmarks(landmarks: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for symbol in SYMBOLS:
        for lm in LANDMARKS:
            base = landmarks[(landmarks.symbol == symbol) & (landmarks.landmark_bars == lm)]
            for year in ("pooled", *DEV_YEARS):
                x = base if year == "pooled" else base[base.year == int(year)]
                if not len(x):
                    continue
                rows.append(
                    {
                        "symbol": symbol,
                        "landmark_bars": lm,
                        "landmark_minutes": lm * 5,
                        "year": year,
                        "observable_landmarks": int(len(x)),
                        "already_normal_fraction": _frac(x.already_normal_by_landmark.astype(bool)),
                        "active_landmarks": int(x.active_at_landmark.sum()),
                    }
                )
    return pd.DataFrame(rows)


def summarize_hazard(landmarks: pd.DataFrame) -> pd.DataFrame:
    active = landmarks[landmarks.active_at_landmark & landmarks.hazard_supported].copy()
    rows: list[dict] = []
    for symbol in SYMBOLS:
        for lm in LANDMARKS:
            base = active[(active.symbol == symbol) & (active.landmark_bars == lm)]
            for state in ("UNSAFE", "RECOVERING"):
                sbase = base[base.current_state == state]
                for year in ("pooled", *DEV_YEARS):
                    x = sbase if year == "pooled" else sbase[sbase.year == int(year)]
                    rows.append(
                        {
                            "symbol": symbol,
                            "landmark_bars": lm,
                            "landmark_minutes": lm * 5,
                            "current_state": state,
                            "year": year,
                            "hazard_n": int(len(x)),
                            "normal_within_next15_fraction": _frac(x.normal_within_next15.astype(bool)) if len(x) else np.nan,
                            "shock_before_normal_next15_fraction": _frac(x.shock_before_normal_next15.astype(bool)) if len(x) else np.nan,
                            "non_normal_after15_fraction": _frac(x.non_normal_after15.astype(bool)) if len(x) else np.nan,
                            "median_current_vol_ratio": float(x.current_vol_ratio.median()) if len(x) and x.current_vol_ratio.notna().any() else np.nan,
                        }
                    )
    return pd.DataFrame(rows)


def separation_table(hazard: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    metrics = {
        "recovery_gap_recovering_minus_unsafe": ("normal_within_next15_fraction", "RECOVERING", "UNSAFE"),
        "recurrence_gap_unsafe_minus_recovering": ("shock_before_normal_next15_fraction", "UNSAFE", "RECOVERING"),
        "persistence_gap_unsafe_minus_recovering": ("non_normal_after15_fraction", "UNSAFE", "RECOVERING"),
    }
    for symbol in SYMBOLS:
        for lm in LANDMARKS:
            h = hazard[(hazard.symbol == symbol) & (hazard.landmark_bars == lm)]
            for label, (field, lhs, rhs) in metrics.items():
                pooled = h[h.year.astype(str) == "pooled"].set_index("current_state")
                if lhs not in pooled.index or rhs not in pooled.index:
                    pgap = np.nan
                else:
                    a = pooled.at[lhs, field]
                    b = pooled.at[rhs, field]
                    pgap = float(a - b) if pd.notna(a) and pd.notna(b) else np.nan
                annual_gaps = []
                for year in DEV_YEARS:
                    y = h[h.year.astype(str) == str(year)].set_index("current_state")
                    if lhs in y.index and rhs in y.index:
                        a = y.at[lhs, field]
                        b = y.at[rhs, field]
                        if pd.notna(a) and pd.notna(b):
                            annual_gaps.append(float(a - b))
                rows.append(
                    {
                        "symbol": symbol,
                        "landmark_bars": lm,
                        "landmark_minutes": lm * 5,
                        "metric": label,
                        "pooled_gap": pgap,
                        "annual_years_comparable": len(annual_gaps),
                        "annual_positive": int(sum(v > 0 for v in annual_gaps)),
                        "annual_negative": int(sum(v < 0 for v in annual_gaps)),
                        "annual_zero": int(sum(v == 0 for v in annual_gaps)),
                    }
                )
    return pd.DataFrame(rows)


def finite_or_none(v):
    if isinstance(v, (float, np.floating)) and not np.isfinite(v):
        return None
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    return v


def row_records(df: pd.DataFrame) -> list[dict]:
    return [{k: finite_or_none(v) for k, v in r.items()} for r in df.to_dict(orient="records")]


def run(root: Path, out: Path) -> dict:
    frames = restrict_common_days({s: load_symbol(root, s) for s in SYMBOLS})
    frames = {s: add_measurements(df) for s, df in frames.items()}
    episodes_all = []
    landmarks_all = []
    for s in SYMBOLS:
        e, l = build_landmarks(frames[s])
        episodes_all.append(e)
        landmarks_all.append(l)
    episodes = pd.concat(episodes_all, ignore_index=True)
    landmarks = pd.concat(landmarks_all, ignore_index=True)
    landmark_summary = summarize_landmarks(landmarks)
    hazard = summarize_hazard(landmarks)
    separation = separation_table(hazard)

    pooled_sep = separation[separation.metric.isin([
        "recovery_gap_recovering_minus_unsafe",
        "persistence_gap_unsafe_minus_recovering",
    ])].copy()
    positive_pooled = int((pooled_sep.pooled_gap > 0).sum())
    annual_consistent = int(((pooled_sep.pooled_gap > 0) & (pooled_sep.annual_positive >= 2)).sum())

    summary = {
        "schema": "highvol_unsafe_recovery_hazard_v3_dev",
        "development_only": True,
        "development_period": ["2021-01-01", "2023-12-31"],
        "warmup_year": 2020,
        "symbols": list(SYMBOLS),
        "state_thresholds_unchanged": True,
        "landmarks_bars": list(LANDMARKS),
        "future_hazard_bars": FUTURE_BARS,
        "pnl_computed": False,
        "trading_rule_created": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "production_authority": False,
        "episode_count": {s: int((episodes.symbol == s).sum()) for s in SYMBOLS},
        "active_supported_landmark_rows": int((landmarks.active_at_landmark & landmarks.hazard_supported).sum()),
        "expected_ordering_rows_recovery_plus_persistence": int(len(pooled_sep)),
        "positive_pooled_ordering_rows": positive_pooled,
        "positive_pooled_and_at_least_2_of_3_years": annual_consistent,
        "landmark_summary": row_records(landmark_summary),
        "hazard_summary": row_records(hazard),
        "separation_summary": row_records(separation),
    }

    out.mkdir(parents=True, exist_ok=True)
    episodes.to_csv(out / "episode_ledger.csv", index=False)
    landmarks.to_csv(out / "landmark_ledger.csv", index=False)
    landmark_summary.to_csv(out / "landmark_summary.csv", index=False)
    hazard.to_csv(out / "hazard_by_state.csv", index=False)
    separation.to_csv(out / "state_separation.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run(Path(args.repo_root).resolve(), Path(args.out))


if __name__ == "__main__":
    main()
