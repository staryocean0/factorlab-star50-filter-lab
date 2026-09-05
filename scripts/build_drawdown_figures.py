"""Plot sealed drawdown evidence without running signals, models or accounts.

Only frozen descriptive files and annual-session CSVs are inputs. The fixed
baseline, slow_conflict_half and constant_075 daily account fragments are
concatenated across years. Retrospective matched constants vary by evaluation
interval and are deliberately never spliced into a synthetic full-period NAV.
Their full-period comparison uses the sealed 2025 cumulative metrics only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, PercentFormatter
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts/drawdown_conditions"
OUTPUT = EVIDENCE / "figures"
POLICIES = ("baseline", "slow_conflict_half", "constant_075")
LABELS = {
    "baseline": "Baseline, full exposure",
    "slow_conflict_half": "Slow-conflict rule",
    "constant_075": "Constant 75% exposure",
    "slow_conflict_half_matched_constant": "Matched constant, full period",
}
COLORS = {
    "baseline": "#334B68",
    "slow_conflict_half": "#008C82",
    "constant_075": "#D09A36",
    "slow_conflict_half_matched_constant": "#A48ABE",
}
BG = "#FAFBFD"
INK = "#25364A"
GRID = "#DCE3EC"
SHADE = "#D97965"
INPUTS: set[Path] = set()


def read_csv(path: Path) -> pd.DataFrame:
    INPUTS.add(path)
    return pd.read_csv(path)


def style_axes(ax):
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK, labelsize=10, length=0, pad=7)
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.label.set_color(INK)


def save(fig, stem):
    for suffix in ("svg", "png"):
        metadata = {"Date": None} if suffix == "svg" else {}
        fig.savefig(OUTPUT / f"{stem}.{suffix}", dpi=170, facecolor=fig.get_facecolor(), metadata=metadata)
    plt.close(fig)


def fixed_daily_paths():
    frames = []
    for year in range(2021, 2026):
        seal = EVIDENCE / "sessions" / str(year) / "sealed_receipt.json"
        if not seal.is_file():
            raise ValueError(f"Unsealed annual evidence: {year}")
        INPUTS.add(seal)
        frame = read_csv(seal.parent / "daily_accounts.csv.gz")
        frame = frame.loc[(frame.cost_bps == 0) & frame.policy.isin(POLICIES)].copy()
        frame["trading_day"] = pd.to_datetime(frame.trading_day)
        if not (frame.trading_day.dt.year == year).all():
            raise ValueError("Annual evidence has an unexpected date")
        frames.append(frame)
    daily = pd.concat(frames, ignore_index=True)
    if daily.duplicated(["trading_day", "policy"]).any():
        raise ValueError("Duplicate daily policy observations")
    matrix = daily.pivot(index="trading_day", columns="policy", values="net_log_pnl").sort_index()
    if matrix[list(POLICIES)].isna().any().any():
        raise ValueError("Fixed-policy daily paths have missing observations")
    return matrix


def overview(matrix, cumulative):
    fig, axes = plt.subplots(2, 1, figsize=(13.7, 9.8), sharex=True, gridspec_kw={"height_ratios": [1.6, 1]})
    fig.set_facecolor(BG)
    fig.subplots_adjust(left=0.08, right=0.955, top=0.802, bottom=0.16, hspace=0.15)
    fig.text(0.08, 0.949, "STAR50 | Drawdown reduction and its return cost", fontsize=21, weight="bold", color=INK)
    fig.text(0.08, 0.908, "2021-2025 · primary 5-minute view (+0) · three unchanged policies · 0 bps research account", fontsize=11, color=INK)
    for ax in axes:
        style_axes(ax)
    dates = pd.DatetimeIndex([matrix.index[0] - pd.Timedelta(days=1), *matrix.index])
    lines = []
    daily_dd = {}
    for policy in POLICIES:
        nav = np.r_[1.0, np.exp(np.cumsum(matrix[policy]))]
        drawdown = nav / np.maximum.accumulate(nav) - 1
        metric = cumulative.loc[(cumulative.view == 0) & (cumulative.policy == policy)].iloc[0]
        # Verify the plotted fragments are the same frozen full-period account.
        np.testing.assert_allclose(np.log(nav[-1]), metric.total_log_return, atol=1e-11)
        np.testing.assert_allclose(-drawdown.min(), metric.daily_mdd, atol=1e-11)
        (line,) = axes[0].plot(dates, nav, color=COLORS[policy], lw=1.75, label=f"{LABELS[policy]}  |  CAGR {metric.cagr:.1%}")
        lines.append(line)
        axes[1].plot(dates, drawdown, color=COLORS[policy], lw=1.4)
        daily_dd[policy] = -drawdown.min()
    fig.legend(handles=lines, loc="upper left", bbox_to_anchor=(0.073, 0.89), ncol=1, frameon=False, fontsize=10.5, labelcolor=INK, handlelength=3)
    axes[0].set_yscale("log")
    axes[0].set_yticks([1, 2, 4, 8, 16, 32])
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}x"))
    axes[0].set_ylabel("Growth of initial capital (log scale)", fontsize=11)
    axes[0].set_ylim(0.9, 29)
    axes[1].yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    axes[1].set_ylabel("Daily sampled drawdown", fontsize=11)
    axes[1].set_ylim(-0.135, 0.006)
    axes[1].xaxis.set_major_locator(mdates.YearLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[1].set_xlim(pd.Timestamp("2021-01-01"), pd.Timestamp("2025-12-31"))
    fig.text(0.08, 0.103, "Daily MDD: " + "  |  ".join(f"{LABELS[p]} {daily_dd[p]:.2%}" for p in POLICIES), fontsize=10.5, color=INK)
    fig.text(0.08, 0.067, "Daily sampling can hide intraday drawdowns. Bar MDD is shown separately in the offset comparison.", fontsize=10, color=INK)
    fig.text(0.08, 0.042, "Signed-log index research accounts; development evidence already consumed. No live-trading or fresh-OOS claim.", fontsize=9, color="#607086")
    save(fig, "overview")


def offset_robustness(cumulative):
    fig, ax = plt.subplots(figsize=(13.7, 8.0))
    fig.set_facecolor(BG)
    fig.subplots_adjust(left=0.08, right=0.96, top=0.75, bottom=0.28)
    fig.text(0.08, 0.94, "Five views of the same 5-minute history", fontsize=22, weight="bold", color=INK)
    fig.text(0.08, 0.899, "Full-period bar maximum drawdown · 2021-2025 · 0 bps · lower is better", fontsize=11.5, color=INK)
    fig.text(0.08, 0.861, "The slow rule beats its exposure-matched control in +0, but loses that advantage in +4.", fontsize=11.5, color=INK)
    style_axes(ax)
    x = np.arange(5)
    width = 0.18
    policies = (*POLICIES, "slow_conflict_half_matched_constant")
    for index, policy in enumerate(policies):
        data = cumulative.loc[cumulative.policy == policy].set_index("view").loc[range(5)]
        bars = ax.bar(x + (index - 1.5) * width, data.mdd, width=width, color=COLORS[policy], label=LABELS[policy], zorder=3)
        ax.bar_label(bars, labels=[f"{value:.1%}" for value in data.mdd], fontsize=9, padding=5, rotation=90, color=INK)
    ax.set_xticks(x, ["+0\nPrimary view", "+1", "+2", "+3", "+4\nCounterexample"])
    ax.set_ylim(0, 0.243)
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_ylabel("Bar maximum drawdown", fontsize=11)
    ax.set_xlabel("Minute offset of the same underlying market history", fontsize=10.5, color=INK, labelpad=10)
    fig.legend(*ax.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.073, 0.83), ncol=2, frameon=False, fontsize=10.5, labelcolor=INK)
    deltas = []
    for view in (0, 4):
        data = cumulative.loc[cumulative.view == view].set_index("policy")
        delta = 100 * (data.loc["slow_conflict_half", "mdd"] - data.loc["slow_conflict_half_matched_constant", "mdd"])
        deltas.append(f"+{view}: slow rule minus matched constant = {delta:+.2f} percentage points")
    fig.text(0.08, 0.143, "  |  ".join(deltas), fontsize=11, weight="bold", color=INK)
    fig.text(0.08, 0.097, "Matched constants come directly from each view's sealed 2025 cumulative comparison, using its full-period mean exposure.", fontsize=10, color=INK)
    fig.text(0.08, 0.063, "Offsets are sensitivity views, not independent markets. Matched constants are retrospective comparators, not causal policies.", fontsize=9.5, color="#607086")
    save(fig, "offset_robustness")


def annual_figures(daily, episodes):
    daily = daily.copy()
    daily["trading_day"] = pd.to_datetime(daily.trading_day)
    for field in ("peak", "trough"):
        episodes[field] = pd.to_datetime(episodes[field], errors="raise")
    for year in range(2021, 2026):
        sample = daily.loc[daily.trading_day.dt.year == year].copy()
        dates = pd.DatetimeIndex(sample.trading_day)
        # Both visible lines start at the first plotted daily mark. This is a
        # visual normalization, not an annual-return calculation.
        price = sample.open.to_numpy() / sample.open.iloc[0]
        strategy = np.exp(sample.pnl_log.cumsum().to_numpy())
        strategy /= strategy[0]
        fig, ax = plt.subplots(figsize=(13.7, 7.4))
        fig.set_facecolor(BG)
        fig.subplots_adjust(left=0.08, right=0.96, top=0.74, bottom=0.24)
        fig.text(0.08, 0.94, f"{year} | Market path and baseline account", fontsize=22, weight="bold", color=INK)
        fig.text(0.08, 0.891, "Primary +0 view · daily samples of the historical carried-position, zero-cost bar baseline", fontsize=11.5, color=INK)
        style_axes(ax)
        ax.plot(dates, price, color="#8492A7", lw=1.8, label="STAR50: last available open mark each day")
        ax.plot(dates, strategy, color=COLORS["baseline"], lw=2, label="Baseline NAV: daily samples of bar PnL")
        local = episodes.loc[(episodes.peak.dt.year <= year) & (episodes.trough.dt.year >= year)]
        for number, event in enumerate(local.itertuples()):
            start = max(event.peak.normalize(), dates[0])
            end = min(event.trough.normalize() + pd.Timedelta(days=1), dates[-1])
            ax.axvspan(start, end, color=SHADE, alpha=0.13, lw=0)
            middle = start + (end - start) / 2
            ax.text(middle, 0.97 - 0.075 * (number % 2), f"#{event.rank}  {event.drawdown:.2%}\nbar drawdown", transform=ax.get_xaxis_transform(), ha="center", va="top", color="#A24433", fontsize=9.5)
        ax.set_ylabel("Rebased to first plotted daily mark = 1", fontsize=11)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}x"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax.set_xlim(pd.Timestamp(year=year, month=1, day=1), pd.Timestamp(year=year, month=12, day=31))
        ymax = max(price.max(), strategy.max())
        ymin = min(price.min(), strategy.min())
        ax.set_ylim(ymin * 0.96, ymax + 0.24 * (ymax - ymin))
        handles, labels = ax.get_legend_handles_labels()
        handles.append(Patch(facecolor=SHADE, alpha=0.2))
        labels.append("Dates spanning a top-10 bar peak-to-trough episode")
        fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.073, 0.855), ncol=1, frameon=False, fontsize=10, labelcolor=INK)
        fig.text(0.08, 0.152, "Shading and labels use the frozen full-history bar peak/trough records. Daily lines do not locate exact intraday extrema.", fontsize=10.5, color=INK)
        fig.text(0.08, 0.111, "The price series is a daily sample of the last open mark, not the exchange's official daily close.", fontsize=10, color=INK)
        fig.text(0.08, 0.071, "Both lines are normalized to the first plotted mark; read annual returns from the sealed metrics, not these endpoints.", fontsize=9.5, color="#607086")
        save(fig, f"annual_{year}")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "svg.hashsalt": "star50-drawdown-evidence-v1"})
    matrix = fixed_daily_paths()
    metrics = read_csv(EVIDENCE / "sessions/2025/policy_metrics.csv")
    cumulative = metrics.loc[(metrics.scope == "cumulative") & (metrics.cost_bps == 0)].copy()
    overview(matrix, cumulative)
    offset_robustness(cumulative)
    annual_figures(read_csv(EVIDENCE / "descriptive/daily_baseline.csv"), read_csv(EVIDENCE / "descriptive/top10_drawdowns.csv"))
    manifest = {
        "schema": "star50_frozen_drawdown_figures@1",
        "reads_sealed_evidence_only": True,
        "signal_or_account_replay_calls": 0,
        "daily_paths": list(POLICIES),
        "matched_constant_usage": "Only sealed 2025 full-period metrics; never concatenate year-matched policies",
        "inputs": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(INPUTS)},
        "figure_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "svg_outputs": [path.name for path in sorted(OUTPUT.glob("*.svg"))],
        "png_usage": "Local visual QA; SVG files are the versioned figure sources",
        "limits": ["Daily sampling hides intraday extremes", "Annual lines normalize at first plotted mark", "Offsets are not independent markets"],
    }
    (OUTPUT / "figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output_dir": str(OUTPUT), "svg_outputs": manifest["svg_outputs"]}, indent=2))


if __name__ == "__main__":
    main()
