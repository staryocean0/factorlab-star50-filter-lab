from __future__ import annotations

from pathlib import Path
import math
import numpy as np
import pandas as pd

OUT = Path("research/highvol_state_v1/outputs")
OUT.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["000688.SH", "000852.SH"]
YEARS = list(range(2020, 2026))

# Frozen, non-optimized v1 measurement constants.
RV_WINDOW = 12
BG_WINDOW = 48
HIGHVOL_RATIO = 1.50
EXTREME_RATIO = 2.25
RECOVERY_NORMAL_RATIO = 1.10
SHOCK_SIGMA = 3.00
FORWARD_HORIZONS = (1, 3, 6)


def _wall_clock(series: pd.Series) -> pd.Series:
    """Normalize source timestamps for ordering only.

    Source annual files encode Shanghai wall clock in their displayed first 19
    characters. We intentionally do not reinterpret them as UTC here; the study
    only requires correct within-session ordering.
    """
    return pd.to_datetime(series.astype(str).str.slice(0, 19), errors="coerce")


def load_symbol(symbol: str) -> pd.DataFrame:
    root = Path("data/market/5m") / symbol
    frames = []
    missing = []
    for year in YEARS:
        p = root / f"{year}.parquet"
        if not p.exists():
            missing.append(str(p))
            continue
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
            ts = day + pd.to_timedelta(np.arange(len(x)), unit="s")

        y = pd.DataFrame(
            {
                "symbol": symbol,
                "trading_day": day.dt.strftime("%Y-%m-%d"),
                "timestamp": ts,
                "close": pd.to_numeric(x["close"], errors="coerce"),
            }
        )
        y = y.dropna(subset=["trading_day", "timestamp", "close"])
        frames.append(y)

    if missing:
        raise RuntimeError("missing required annual inputs: " + ", ".join(missing))
    if not frames:
        raise RuntimeError(f"no inputs for {symbol}")

    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["trading_day", "timestamp"]).drop_duplicates(
        ["trading_day", "timestamp"], keep="last"
    )
    df = df.reset_index(drop=True)
    return df


def restrict_common_days(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    common = None
    for df in frames.values():
        days = set(df["trading_day"].unique())
        common = days if common is None else common.intersection(days)
    if not common:
        raise RuntimeError("no common trading days across symbols")
    common = sorted(common)
    for symbol in list(frames):
        frames[symbol] = frames[symbol][frames[symbol]["trading_day"].isin(common)].copy()
        frames[symbol] = frames[symbol].sort_values(["trading_day", "timestamp"]).reset_index(drop=True)
    return frames


def add_measurements(df: pd.DataFrame) -> pd.DataFrame:
    z = df.copy()
    # Explicitly exclude overnight returns.
    z["ret_5m"] = z.groupby("trading_day", sort=False)["close"].transform(
        lambda s: np.log(s).diff()
    )

    valid = z["ret_5m"].dropna()
    rv = valid.rolling(RV_WINDOW, min_periods=RV_WINDOW).std(ddof=0)
    bg = valid.shift(1).rolling(BG_WINDOW, min_periods=BG_WINDOW).std(ddof=0)
    z["rv12"] = rv.reindex(z.index)
    z["bg_vol48"] = bg.reindex(z.index)
    z.loc[z["bg_vol48"] <= 0, "bg_vol48"] = np.nan
    z["vol_ratio"] = z["rv12"] / z["bg_vol48"]
    z["shock_intensity"] = z["ret_5m"].abs() / z["bg_vol48"]
    z["shock"] = z["shock_intensity"] >= SHOCK_SIGMA

    z["vol_state"] = "UNKNOWN"
    eligible = z["vol_ratio"].notna()
    z.loc[eligible & (z["vol_ratio"] < HIGHVOL_RATIO), "vol_state"] = "NORMAL"
    z.loc[
        eligible & (z["vol_ratio"] >= HIGHVOL_RATIO) & (z["vol_ratio"] < EXTREME_RATIO),
        "vol_state",
    ] = "HIGHVOL"
    z.loc[eligible & (z["vol_ratio"] >= EXTREME_RATIO), "vol_state"] = "EXTREMEVOL"

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
    z["is_highvol"] = z["vol_state"].isin(["HIGHVOL", "EXTREMEVOL"])
    return z


def episode_lengths(state: pd.Series) -> pd.DataFrame:
    if len(state) == 0:
        return pd.DataFrame(columns=["state", "duration"])
    gid = state.ne(state.shift()).cumsum()
    out = pd.DataFrame({"state": state, "gid": gid}).groupby("gid", sort=False).agg(
        state=("state", "first"), duration=("state", "size")
    )
    return out.reset_index(drop=True)


def vol_summary(df: pd.DataFrame) -> pd.DataFrame:
    eligible = df[df["vol_state"] != "UNKNOWN"].copy()
    eps = episode_lengths(eligible["vol_state"])
    rows = []
    for st in ["NORMAL", "HIGHVOL", "EXTREMEVOL"]:
        sub = eligible[eligible["vol_state"] == st]
        dur = eps.loc[eps["state"] == st, "duration"]
        same_day_next = eligible["trading_day"].eq(eligible["trading_day"].shift(-1))
        mask = (eligible["vol_state"] == st) & same_day_next
        denom = int(mask.sum())
        self_p = float((eligible.loc[mask, "vol_state"].values == eligible["vol_state"].shift(-1).loc[mask].values).mean()) if denom else np.nan
        rows.append(
            {
                "symbol": eligible["symbol"].iloc[0],
                "state": st,
                "count": int(len(sub)),
                "percentage": float(len(sub) / len(eligible)) if len(eligible) else np.nan,
                "episodes": int(len(dur)),
                "avg_duration_bars": float(dur.mean()) if len(dur) else np.nan,
                "median_duration_bars": float(dur.median()) if len(dur) else np.nan,
                "p90_duration_bars": float(dur.quantile(0.9)) if len(dur) else np.nan,
                "self_transition_probability": self_p,
            }
        )
    return pd.DataFrame(rows)


def risk_transitions(df: pd.DataFrame) -> pd.DataFrame:
    same_day_next = df["trading_day"].eq(df["trading_day"].shift(-1))
    cur = df.loc[same_day_next, "risk_state"]
    nxt = df["risk_state"].shift(-1).loc[same_day_next]
    tab = pd.DataFrame({"from_state": cur.values, "to_state": nxt.values})
    counts = tab.value_counts().rename("count").reset_index()
    counts["probability"] = counts["count"] / counts.groupby("from_state")["count"].transform("sum")
    counts.insert(0, "symbol", df["symbol"].iloc[0])
    return counts.sort_values(["from_state", "to_state"]).reset_index(drop=True)


def recovery_failure_probability(df: pd.DataFrame) -> float:
    same_day_next = df["trading_day"].eq(df["trading_day"].shift(-1))
    cur = df["risk_state"]
    nxt = df["risk_state"].shift(-1)
    exits = same_day_next & (cur == "RECOVERING") & (nxt != "RECOVERING")
    n = int(exits.sum())
    if n == 0:
        return np.nan
    return float((nxt[exits] == "UNSAFE").mean())


def core_metrics(df: pd.DataFrame, year: int | str) -> dict:
    x = df if year == "pooled" else df[df["year"] == int(year)]
    eligible = x[x["vol_state"] != "UNKNOWN"].copy()
    if len(eligible) == 0:
        return {"year": year}
    same_day_next = eligible["trading_day"].eq(eligible["trading_day"].shift(-1))
    hv = eligible["is_highvol"]
    hv_denom = int((hv & same_day_next).sum())
    hv_persist = float((eligible["is_highvol"].shift(-1)[hv & same_day_next]).mean()) if hv_denom else np.nan
    shock_eligible = eligible["shock_intensity"].notna()
    return {
        "year": year,
        "highvol_share": float(hv.mean()),
        "extreme_share": float((eligible["vol_state"] == "EXTREMEVOL").mean()),
        "highvol_persistence": hv_persist,
        "shock_rate": float(eligible.loc[shock_eligible, "shock"].mean()) if shock_eligible.any() else np.nan,
        "recovery_failure_probability": recovery_failure_probability(eligible),
        "eligible_bars": int(len(eligible)),
        "shock_count": int(eligible["shock"].sum()),
    }


def structural_assessment(metrics: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    # Frozen pre-result rule: a core metric is materially different if its pooled
    # symmetric relative gap >=20% and >=80% of comparable annual differences
    # have the same sign. Two or more such metrics => different structure.
    core = ["highvol_share", "highvol_persistence", "shock_rate", "recovery_failure_probability"]
    pooled = metrics[metrics["year"].astype(str) == "pooled"].set_index("symbol")
    annual = metrics[metrics["year"].astype(str) != "pooled"].copy()
    rows = []
    material_count = 0
    for m in core:
        a = float(pooled.at["000688.SH", m])
        b = float(pooled.at["000852.SH", m])
        scale = (abs(a) + abs(b)) / 2.0
        rel_gap = abs(a - b) / scale if scale > 0 else np.nan
        piv = annual.pivot(index="year", columns="symbol", values=m).dropna()
        diffs = piv["000688.SH"] - piv["000852.SH"]
        if len(diffs):
            pos = int((diffs > 0).sum())
            neg = int((diffs < 0).sum())
            same_sign_fraction = max(pos, neg) / len(diffs)
            direction = "000688>000852" if pos >= neg else "000688<000852"
        else:
            same_sign_fraction = np.nan
            direction = "insufficient"
        material = bool(pd.notna(rel_gap) and rel_gap >= 0.20 and pd.notna(same_sign_fraction) and same_sign_fraction >= 0.80)
        material_count += int(material)
        rows.append(
            {
                "metric": m,
                "000688_pooled": a,
                "000852_pooled": b,
                "symmetric_relative_gap": rel_gap,
                "annual_same_sign_fraction": same_sign_fraction,
                "direction": direction,
                "material_by_frozen_rule": material,
            }
        )
    label = "different_structure" if material_count >= 2 else "similar_structure"
    return label, pd.DataFrame(rows)


def forward_sum_same_day(df: pd.DataFrame, horizon: int) -> pd.Series:
    out = pd.Series(np.nan, index=df.index, dtype=float)
    for _, idx in df.groupby("trading_day", sort=False).groups.items():
        vals = df.loc[idx, "ret_5m"].to_numpy(dtype=float)
        arr = np.full(len(vals), np.nan)
        for j in range(len(vals)):
            fut = vals[j + 1 : j + 1 + horizon]
            if len(fut) == horizon and np.isfinite(fut).all():
                arr[j] = float(fut.sum())
        out.loc[idx] = arr
    return out


def highvol_module_difference(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for symbol, df in frames.items():
        x = df.copy()
        # Fixed 3-bar impulse direction, reset within each day.
        x["impulse3"] = x.groupby("trading_day", sort=False)["ret_5m"].transform(
            lambda s: s.rolling(3, min_periods=3).sum()
        )
        prev_hv = x.groupby("trading_day", sort=False)["is_highvol"].shift(1).fillna(False).astype(bool)
        entry = x["is_highvol"] & ~prev_hv & x["impulse3"].notna() & (x["impulse3"] != 0)
        for h in FORWARD_HORIZONS:
            fwd = forward_sum_same_day(x, h)
            aligned = np.sign(x["impulse3"]) * fwd
            for yr in ["pooled"] + YEARS:
                mask = entry if yr == "pooled" else entry & (x["year"] == yr)
                vals = aligned[mask].dropna()
                rows.append(
                    {
                        "symbol": symbol,
                        "year": yr,
                        "horizon_bars": h,
                        "n_entries": int(len(vals)),
                        "mean_aligned_forward_log_return": float(vals.mean()) if len(vals) else np.nan,
                        "median_aligned_forward_log_return": float(vals.median()) if len(vals) else np.nan,
                        "continuation_fraction": float((vals > 0).mean()) if len(vals) else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def common_mechanism(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for symbol, df in frames.items():
        x = df.copy()
        fwd3 = forward_sum_same_day(x, 3).abs()
        ratio_bin = pd.cut(
            x["vol_ratio"],
            [-np.inf, 1.0, HIGHVOL_RATIO, EXTREME_RATIO, np.inf],
            labels=["<1.0", "1.0-1.5", "1.5-2.25", ">=2.25"],
            right=False,
        )
        shock_bin = pd.cut(
            x["shock_intensity"],
            [-np.inf, 1.0, 2.0, SHOCK_SIGMA, np.inf],
            labels=["<1sigma", "1-2sigma", "2-3sigma", ">=3sigma"],
            right=False,
        )
        tmp = pd.DataFrame({"ratio_bin": ratio_bin, "shock_bin": shock_bin, "future_abs_ret_3": fwd3})
        g = tmp.dropna().groupby(["ratio_bin", "shock_bin"], observed=True)["future_abs_ret_3"]
        for (rb, sb), vals in g:
            rows.append(
                {
                    "symbol": symbol,
                    "vol_ratio_bin": str(rb),
                    "shock_intensity_bin": str(sb),
                    "n": int(len(vals)),
                    "mean_future_abs_log_return_3": float(vals.mean()),
                    "median_future_abs_log_return_3": float(vals.median()),
                }
            )
    return pd.DataFrame(rows)


def fmt_pct(x: float) -> str:
    return "NA" if pd.isna(x) else f"{100*x:.3f}%"


def main() -> None:
    frames = {s: load_symbol(s) for s in SYMBOLS}
    frames = restrict_common_days(frames)
    frames = {s: add_measurements(df) for s, df in frames.items()}

    states = pd.concat(frames.values(), ignore_index=True)
    states[[
        "symbol", "trading_day", "timestamp", "close", "ret_5m", "rv12", "bg_vol48",
        "vol_ratio", "shock_intensity", "shock", "vol_state", "risk_state"
    ]].to_parquet(OUT / "state_sequence.parquet", index=False)

    highvol = pd.concat([vol_summary(df) for df in frames.values()], ignore_index=True)
    highvol.to_csv(OUT / "HighVol_State_Comparison.csv", index=False)

    transitions = pd.concat([risk_transitions(df) for df in frames.values()], ignore_index=True)
    transitions.to_csv(OUT / "Unsafe_Recovery_Transition.csv", index=False)

    metric_rows = []
    for symbol, df in frames.items():
        for yr in ["pooled"] + YEARS:
            r = core_metrics(df, yr)
            r["symbol"] = symbol
            metric_rows.append(r)
    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(OUT / "annual_core_metrics.csv", index=False)

    classification, assessment = structural_assessment(metrics)
    assessment.to_csv(OUT / "structural_assessment.csv", index=False)

    if classification == "different_structure":
        next_stage = highvol_module_difference(frames)
        next_name = "next_stage_highvol_module_difference.csv"
        next_stage.to_csv(OUT / next_name, index=False)
    else:
        next_stage = common_mechanism(frames)
        next_name = "next_stage_common_mechanism.csv"
        next_stage.to_csv(OUT / next_name, index=False)

    pooled = metrics[metrics["year"].astype(str) == "pooled"].set_index("symbol")
    common_days = sorted(set(frames[SYMBOLS[0]]["trading_day"]))
    report = [
        "# HighVol state analysis v1",
        "",
        "## Execution contract",
        "",
        f"- Common trading-day interval: {common_days[0]} to {common_days[-1]}",
        f"- Common trading days: {len(common_days)}",
        f"- rv window: {RV_WINDOW} bars",
        f"- background window: preceding {BG_WINDOW} valid intraday 5m returns",
        f"- HighVol ratio threshold: {HIGHVOL_RATIO}",
        f"- ExtremeVol ratio threshold: {EXTREME_RATIO}",
        f"- Shock threshold: {SHOCK_SIGMA} sigma",
        "- Overnight returns excluded; risk state resets each trading day.",
        "- No trading rule, PnL optimization, position sizing, BLACKBOX, or 2026 data used.",
        "",
        "## Pooled core measurements",
        "",
        "| metric | 000688.SH | 000852.SH |",
        "|---|---:|---:|",
        f"| eligible bars | {int(pooled.at['000688.SH','eligible_bars'])} | {int(pooled.at['000852.SH','eligible_bars'])} |",
        f"| HighVol+Extreme share | {fmt_pct(pooled.at['000688.SH','highvol_share'])} | {fmt_pct(pooled.at['000852.SH','highvol_share'])} |",
        f"| Extreme share | {fmt_pct(pooled.at['000688.SH','extreme_share'])} | {fmt_pct(pooled.at['000852.SH','extreme_share'])} |",
        f"| HighVol persistence | {fmt_pct(pooled.at['000688.SH','highvol_persistence'])} | {fmt_pct(pooled.at['000852.SH','highvol_persistence'])} |",
        f"| shock rate | {fmt_pct(pooled.at['000688.SH','shock_rate'])} | {fmt_pct(pooled.at['000852.SH','shock_rate'])} |",
        f"| recovery failure probability | {fmt_pct(pooled.at['000688.SH','recovery_failure_probability'])} | {fmt_pct(pooled.at['000852.SH','recovery_failure_probability'])} |",
        "",
        "## Frozen structural adjudication",
        "",
        f"**{classification}**",
        "",
        "Rule fixed before observing outputs: at least two of four core metrics must have >=20% pooled symmetric relative gap and >=80% same-sign annual differences.",
        "",
        f"Automatic next-stage output: `{next_name}`.",
        "",
        "This is mechanism measurement, not a trading recommendation.",
    ]
    (OUT / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print("classification:", classification)
    print(metrics[metrics["year"].astype(str) == "pooled"].to_string(index=False))
    print("outputs:", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
