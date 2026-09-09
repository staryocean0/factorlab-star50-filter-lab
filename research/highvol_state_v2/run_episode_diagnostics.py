from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from research.highvol_state_v1.run_analysis import (
    SYMBOLS,
    YEARS,
    add_measurements,
    load_symbol,
    restrict_common_days,
)

OUT = Path("research/highvol_state_v2/outputs")
OUT.mkdir(parents=True, exist_ok=True)
SURVIVAL_HORIZONS = tuple(range(1, 13))


def build_episode_ledger(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for day, day_df in df.groupby("trading_day", sort=False):
        x = day_df.sort_values("timestamp").copy().reset_index()
        prev_unsafe = x["risk_state"].shift(1).eq("UNSAFE").fillna(False)
        starts = x.index[x["shock"].fillna(False).astype(bool) & ~prev_unsafe]
        occupied_until = -1
        for j in starts:
            # If a prior episode is still active, this shock is recurrence, not a new episode.
            if j <= occupied_until:
                continue
            normal_after = x.index[(x.index > j) & x["risk_state"].eq("NORMAL")]
            if len(normal_after):
                end_j = int(normal_after[0])
                recovered = True
            else:
                end_j = int(x.index.max())
                recovered = False
            occupied_until = end_j - 1 if recovered else end_j

            path = x.loc[j:end_j].copy()
            pre_normal = path.iloc[:-1] if recovered and len(path) > 1 else path
            recurrence = pre_normal.iloc[1:]["shock"].fillna(False).astype(bool) if len(pre_normal) > 1 else pd.Series(dtype=bool)

            leave_unsafe = x.index[(x.index > j) & ~x["risk_state"].eq("UNSAFE")]
            leave_unsafe = leave_unsafe[leave_unsafe <= end_j]
            bars_to_leave = int(leave_unsafe[0] - j) if len(leave_unsafe) else np.nan
            bars_to_normal = int(end_j - j) if recovered else np.nan
            available_bars = int(end_j - j)

            rows.append(
                {
                    "symbol": str(x.at[j, "symbol"]),
                    "year": int(pd.Timestamp(day).year),
                    "trading_day": str(day),
                    "start_timestamp": x.at[j, "timestamp"],
                    "start_shock_intensity": float(x.at[j, "shock_intensity"]),
                    "start_vol_ratio": float(x.at[j, "vol_ratio"]) if pd.notna(x.at[j, "vol_ratio"]) else np.nan,
                    "same_session_normal_recovered": bool(recovered),
                    "right_censored": bool(not recovered),
                    "bars_to_leave_unsafe": bars_to_leave,
                    "bars_to_normal": bars_to_normal,
                    "available_bars_after_start": available_bars,
                    "recurrent_shock_before_normal": bool(recurrence.any()) if len(recurrence) else False,
                    "recurrent_shock_count_before_normal": int(recurrence.sum()) if len(recurrence) else 0,
                    "peak_vol_ratio_before_normal": float(pre_normal["vol_ratio"].max()) if pre_normal["vol_ratio"].notna().any() else np.nan,
                    "peak_shock_intensity_before_normal": float(pre_normal["shock_intensity"].max()) if pre_normal["shock_intensity"].notna().any() else np.nan,
                }
            )
    return pd.DataFrame(rows)


def summarize(ledger: pd.DataFrame, symbol: str, year: str | int) -> dict:
    x = ledger[ledger["symbol"].eq(symbol)]
    if year != "pooled":
        x = x[x["year"].eq(int(year))]
    rec = x[x["same_session_normal_recovered"]]
    return {
        "symbol": symbol,
        "year": year,
        "episodes": int(len(x)),
        "normal_recovery_fraction": float(x["same_session_normal_recovered"].mean()) if len(x) else np.nan,
        "recurrence_before_normal_fraction": float(x["recurrent_shock_before_normal"].mean()) if len(x) else np.nan,
        "median_bars_to_normal": float(rec["bars_to_normal"].median()) if len(rec) else np.nan,
        "p90_bars_to_normal": float(rec["bars_to_normal"].quantile(0.9)) if len(rec) else np.nan,
        "median_bars_to_leave_unsafe": float(x["bars_to_leave_unsafe"].median()) if x["bars_to_leave_unsafe"].notna().any() else np.nan,
        "censor_fraction": float(x["right_censored"].mean()) if len(x) else np.nan,
        "median_peak_vol_ratio": float(x["peak_vol_ratio_before_normal"].median()) if x["peak_vol_ratio_before_normal"].notna().any() else np.nan,
        "median_peak_shock_intensity": float(x["peak_shock_intensity_before_normal"].median()) if x["peak_shock_intensity_before_normal"].notna().any() else np.nan,
    }


def survival_curve(ledger: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for symbol in SYMBOLS:
        x = ledger[ledger["symbol"].eq(symbol)].copy()
        for h in SURVIVAL_HORIZONS:
            # An episode is evaluable at h if it is observed through h, or if it
            # already reached Normal by h. Use a union so episodes recovering
            # exactly at h are never counted twice in the denominator.
            observed_at_h = x["available_bars_after_start"] >= h
            recovered_by_h = x["same_session_normal_recovered"] & x["bars_to_normal"].le(h)
            evaluable = observed_at_h | recovered_by_h
            denom = int(evaluable.sum())
            not_normal = int((evaluable & ~recovered_by_h).sum())
            rows.append(
                {
                    "symbol": symbol,
                    "horizon_bars": h,
                    "horizon_minutes": 5 * h,
                    "episodes_observable_or_recovered": denom,
                    "not_normal_count": not_normal,
                    "not_normal_fraction": (not_normal / denom) if denom else np.nan,
                }
            )
    return pd.DataFrame(rows)


def direction_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "normal_recovery_fraction",
        "recurrence_before_normal_fraction",
        "median_bars_to_normal",
        "median_bars_to_leave_unsafe",
        "censor_fraction",
        "median_peak_vol_ratio",
    ]
    pooled = metrics[metrics["year"].astype(str).eq("pooled")].set_index("symbol")
    annual = metrics[~metrics["year"].astype(str).eq("pooled")]
    rows = []
    for field in fields:
        a = float(pooled.at["000688.SH", field])
        b = float(pooled.at["000852.SH", field])
        p = annual.pivot(index="year", columns="symbol", values=field).dropna()
        d = p["000688.SH"] - p["000852.SH"] if len(p) else pd.Series(dtype=float)
        rows.append(
            {
                "metric": field,
                "000688_pooled": a,
                "000852_pooled": b,
                "pooled_difference_000688_minus_000852": a - b,
                "annual_years_compared": int(len(d)),
                "annual_000688_gt_000852": int((d > 0).sum()),
                "annual_000688_lt_000852": int((d < 0).sum()),
                "annual_equal": int((d == 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def pct(x: float) -> str:
    return "NA" if pd.isna(x) else f"{100*x:.2f}%"


def num(x: float, digits: int = 2) -> str:
    return "NA" if pd.isna(x) else f"{x:.{digits}f}"


def main() -> None:
    frames = {s: load_symbol(s) for s in SYMBOLS}
    frames = restrict_common_days(frames)
    frames = {s: add_measurements(df) for s, df in frames.items()}

    ledgers = [build_episode_ledger(df) for df in frames.values()]
    ledger = pd.concat(ledgers, ignore_index=True)
    if ledger.empty:
        raise RuntimeError("no shock-triggered Unsafe episodes found")
    ledger.to_csv(OUT / "episode_ledger.csv", index=False)

    rows = []
    for symbol in SYMBOLS:
        for year in ["pooled"] + YEARS:
            rows.append(summarize(ledger, symbol, year))
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "annual_episode_metrics.csv", index=False)

    survival = survival_curve(ledger)
    survival.to_csv(OUT / "unsafe_survival_curve.csv", index=False)

    directions = direction_summary(metrics)
    directions.to_csv(OUT / "cross_index_direction_summary.csv", index=False)

    pooled = metrics[metrics["year"].astype(str).eq("pooled")].set_index("symbol")
    s60 = survival[survival["horizon_bars"].eq(12)].set_index("symbol")
    common_days = sorted(set(frames[SYMBOLS[0]]["trading_day"]))

    report = [
        "# HighVol / Unsafe recovery dynamics v2",
        "",
        "## Scope",
        "",
        "- Continues the current cross-index K-line risk-state mainline.",
        "- Inherits every HighVol/Unsafe threshold from v1 unchanged; no threshold search or retuning.",
        "- Shock-triggered episodes are de-overlapped; recurrent shocks before Normal remain inside the same episode.",
        f"- Common trading days: {len(common_days)} ({common_days[0]} to {common_days[-1]}).",
        "- Historical consumed development evidence only; fresh_oos=false; no 2026, BLACKBOX, PnL, or trading authority.",
        "",
        "## Pooled episode dynamics",
        "",
        "| metric | 000688.SH | 000852.SH |",
        "|---|---:|---:|",
        f"| shock-triggered Unsafe episodes | {int(pooled.at['000688.SH','episodes'])} | {int(pooled.at['000852.SH','episodes'])} |",
        f"| same-session Normal recovery | {pct(pooled.at['000688.SH','normal_recovery_fraction'])} | {pct(pooled.at['000852.SH','normal_recovery_fraction'])} |",
        f"| recurrent shock before Normal | {pct(pooled.at['000688.SH','recurrence_before_normal_fraction'])} | {pct(pooled.at['000852.SH','recurrence_before_normal_fraction'])} |",
        f"| median bars to Normal (recovered only) | {num(pooled.at['000688.SH','median_bars_to_normal'])} | {num(pooled.at['000852.SH','median_bars_to_normal'])} |",
        f"| p90 bars to Normal (recovered only) | {num(pooled.at['000688.SH','p90_bars_to_normal'])} | {num(pooled.at['000852.SH','p90_bars_to_normal'])} |",
        f"| median bars to leave Unsafe | {num(pooled.at['000688.SH','median_bars_to_leave_unsafe'])} | {num(pooled.at['000852.SH','median_bars_to_leave_unsafe'])} |",
        f"| session censor fraction | {pct(pooled.at['000688.SH','censor_fraction'])} | {pct(pooled.at['000852.SH','censor_fraction'])} |",
        f"| not Normal by 60m among observable/recovered | {pct(s60.at['000688.SH','not_normal_fraction'])} | {pct(s60.at['000852.SH','not_normal_fraction'])} |",
        f"| median episode peak vol ratio | {num(pooled.at['000688.SH','median_peak_vol_ratio'],3)} | {num(pooled.at['000852.SH','median_peak_vol_ratio'],3)} |",
        "",
        "## Interpretation rule",
        "",
        "Cross-index pooled differences are accompanied by calendar-year direction counts in `cross_index_direction_summary.csv`. No new binary promotion gate is created here. A difference is treated as descriptive unless its direction is visible across annual rows as well.",
        "",
        "The migrated RMR material is used only as a guardrail: state/mechanism evidence is not converted into a payoff or trading rule in this diagnostic.",
        "",
        "`production_authority=false`.",
    ]
    (OUT / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(metrics[metrics["year"].astype(str).eq("pooled")].to_string(index=False))
    print(directions.to_string(index=False))


if __name__ == "__main__":
    main()
