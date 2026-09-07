"""Read frozen measurement/account outputs, verify, and render two study reports."""

# ruff: noqa: E402, E501
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src")]
from research_resolution_transfer_v1 import EXPORT, OUT, check, save, sha
from star50_filter.slope_union_v2 import summary


def main():
    check()
    dest = OUT / "final"
    assert not dest.exists()
    dest.mkdir()
    for year in [2024, 2025]:
        root = OUT / f"seconds_{year}"
        r = json.loads((root / "receipt.json").read_text())
        for file, h in r["files"].items():
            assert sha(root / file) == h
    panels = pd.concat([pd.read_parquet(OUT / f"seconds_{year}" / "common_support.parquet") for year in [2024, 2025]], ignore_index=True)
    keys = ["day", "symbol", "session", "minute", "field", "horizon"]
    # Common ER alone is insufficient for rolling-variance comparison: require all five var60.
    counts = panels.groupby(keys).var60.transform("count")
    var_shared = panels[(counts == 5) & panels.var60.notna()].copy()
    stats = []
    for keys_, g in panels.groupby(["year", "symbol", "field", "horizon", "delta"]):
        year, symbol, field, h, delta = keys_
        v = var_shared[
            (var_shared.year == year)
            & (var_shared.symbol == symbol)
            & (var_shared.field == field)
            & (var_shared.horizon == h)
            & (var_shared.delta == delta)
        ]
        variance = float(g.er.var(ddof=1))
        stats.append(
            {
                "year": year,
                "symbol": symbol,
                "field": field,
                "horizon_minutes": h,
                "grid_seconds": delta,
                "common_er_rows": len(g),
                "common_var_rows": len(v),
                "days": g.day.nunique(),
                "mean_er": g.er.mean(),
                "variance_er": variance,
                "n_times_variance_er": variance * h * 60 / delta,
                "relative_variance_cv2": variance / g.er.mean() ** 2,
                "median_trailing_60m_variance": v.var60.median(),
                "median_scaled_trailing_variance": v.var60.median() * h * 60 / delta,
                "unchanged_price_share": g.zero_share.mean(),
                "nonoverlap_variance": g.loc[g.nonoverlap, "er"].var(ddof=1),
            }
        )
    stat = pd.DataFrame(stats)
    stat.to_csv(dest / "resolution_summary.csv", index=False)
    fine = panels[panels.delta == 3]
    road = panels.merge(fine[keys + ["road"]], on=keys, suffixes=("", "_3s"))
    road["observed_road_ratio_to_3s"] = road.road / road.road_3s
    assert road.observed_road_ratio_to_3s.max() <= 1 + 1e-8
    road.groupby(["year", "symbol", "field", "horizon", "delta"]).observed_road_ratio_to_3s.agg(["count", "median", "mean"]).to_csv(
        dest / "visible_path_ratio.csv"
    )
    shape = fine[(fine.horizon == 30) & fine.nonoverlap].copy()
    shape["shape"] = np.select(
        [shape.top1 >= 0.5, (shape.er >= 0.6) & (shape.top1 < 0.2)],
        ["single_increment_dominated", "directional_resolved_candidate"],
        default="mixed",
    )
    shape["abs_net_bp"] = shape.net.abs() * 10000
    shape.groupby(["year", "symbol", "field", "shape"]).agg(
        windows=("er", "size"), mean_er=("er", "mean"), median_abs_net_bp=("abs_net_bp", "median")
    ).to_csv(dest / "retrospective_shapes.csv")
    shape.to_parquet(dest / "retrospective_shape_windows.parquet", index=False)
    # No rereading market prices for these aggregates.
    annual = pd.concat([pd.read_csv(OUT / f"migration_{y}" / "summary.csv") for y in range(2021, 2026)], ignore_index=True)
    annual.to_csv(dest / "migration_annual.csv", index=False)
    rows = []
    days_map = {}
    errors = []
    for label in ["V1", "V2"]:
        for fee in [0, 2, 4, 7]:
            trades = []
            days = []
            curves = []
            capital = 1.0
            for year in range(2021, 2026):
                root = OUT / f"migration_{year}"
                r = json.loads((root / "receipt.json").read_text())
                review = json.loads((root / "review.json").read_text())
                assert review["receipt_sha256"] == sha(root / "receipt.json")
                for file, h in r["files"].items():
                    assert sha(root / file) == h
                if year > 2021:
                    assert r["prior_review_sha256"] == sha(OUT / f"migration_{year - 1}" / "review.json")
                t = pd.read_parquet(root / f"{label}_fee{fee}_trades.parquet")
                d = pd.read_parquet(root / f"{label}_fee{fee}_daily.parquet")
                n = np.load(root / f"{label}_fee{fee}_nav.npy")
                assert np.isclose(np.prod(1 + t.net_bp.to_numpy() / 10000), n[-1], rtol=1e-10)
                curves.append(n * capital)
                capital *= n[-1]
                trades.append(t)
                days.append(d)
            t = pd.concat(trades, ignore_index=True)
            d = pd.concat(days)
            rows.append({"label": label, "fee_bps_per_side": fee, **summary(t, d, np.concatenate(curves))})
            if fee == 2:
                days_map[label] = d
                t.to_csv(dest / f"CSI1000_{label}_trades.csv", index=False)
                d.to_csv(dest / f"CSI1000_{label}_daily.csv")
    migration = pd.DataFrame(rows)
    migration.to_csv(dest / "migration_summary.csv", index=False)
    # Independent cash/share replay of every V2 year, using fixed targets and the raw open source.
    for year in range(2021, 2026):
        root = OUT / f"migration_{year}"
        bars = pd.read_parquet(
            EXPORT / "1m_official.parquet",
            columns=["timestamp", "open"],
            filters=[("symbol", "==", "000852.SH"), ("trading_day", ">=", f"{year}-01-01"), ("trading_day", "<=", f"{year}-12-31")],
        ).sort_values("timestamp")
        t = pd.read_parquet(root / "V2_fee2_trades.parquet")
        target = np.load(root / "V2_targets.npy")
        prior = int(t.side.iloc[0]) if len(t) and t.entry_i.iloc[0] == 0 else 0
        held = np.r_[prior, target[:-1]]
        held[-1] = 0
        cash, shares, old = 1.0, 0.0, 0
        path = []
        for p, want in zip(bars.open, held, strict=True):
            if want != old:
                if old:
                    cash += shares * p - abs(shares) * p * 0.0002
                    shares = 0.0
                if want:
                    shares = want * cash / (p * 1.0002)
                    cash -= shares * p + abs(shares) * p * 0.0002
                old = want
            path.append(cash + shares * p)
        expected = np.load(root / "V2_fee2_nav.npy")
        error = float(np.max(abs(expected - np.asarray(path))))
        np.testing.assert_allclose(expected, path, rtol=1e-11, atol=1e-12)
        errors.append({"year": year, "cash_share_max_error": error})
    render(dest, stat, migration, annual, days_map)
    save(
        dest / "validation.json",
        {
            "source_sha256": sha(Path(__file__)),
            "freeze_sha256": sha(OUT / "freeze.json"),
            "all_annual_artifact_hashes_verified": True,
            "migration_cash_share_replay": errors,
            "rolling_variance_common_support_enforced": True,
            "coarse_path_never_exceeds_nested_fine_path": True,
            "seconds_is_etf_not_index": True,
            "unseen_2026_rows": 0,
            "production_authority": False,
            "files": {p.name: sha(p) for p in dest.iterdir() if p.is_file()},
        },
    )
    print(migration.to_string(index=False))
    print(stat[(stat.horizon_minutes == 30) & (stat.field == "mid")].to_string(index=False))


def render(dest, stat, migration, annual, days_map):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties

    font = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
    fig, axs = plt.subplots(2, 2, figsize=(13, 8), layout="constrained")
    for (year, symbol), g in stat[(stat.horizon_minutes == 30) & (stat.field == "mid")].groupby(["year", "symbol"]):
        g = g.sort_values("grid_seconds")
        label = f"{symbol[:6]} / {year}"
        for ax, field in zip(
            axs.flat, ["median_trailing_60m_variance", "median_scaled_trailing_variance", "mean_er", "unchanged_price_share"], strict=True
        ):
            ax.plot(g.grid_seconds, g[field], marker="o", label=label)
            ax.set_xscale("log")
            ax.set_xticks([3, 15, 30, 60, 300], ["3s", "15s", "30s", "1m", "5m"])
            ax.grid(alpha=0.2)
    titles = ["路径效率60分钟滚动方差中位数", "乘以窗口增量数后的方差（随机游走参照）", "30分钟路径效率均值", "价格不变的增量比例"]
    for ax, title in zip(axs.flat, titles, strict=True):
        ax.set_title(title, fontproperties=font)
        ax.legend(fontsize=8)
    fig.suptitle(
        "科创50ETF真实秒观测 · 固定30分钟路径、60分钟变化窗口\n同日同会话同结束时刻共同支持；不是交易频率优选",
        fontproperties=font,
        fontsize=14,
    )
    fig.savefig(dest / "resolution_comparison.png", dpi=160)
    plt.close(fig)
    fig, axs = plt.subplots(2, 1, figsize=(13, 8), layout="constrained")
    for label, d in days_map.items():
        nav = np.cumprod(1 + d["return"].to_numpy())
        dates = pd.to_datetime(d.index)
        axs[0].plot(dates, nav, label="CSI1000 " + label)
        axs[1].plot(dates, 100 * (nav / np.maximum.accumulate(np.r_[1.0, nav])[1:] - 1), label="CSI1000 " + label)
    star = pd.read_csv(ROOT / "artifacts/half_day_slope_union_v2/final/V2_daily.csv", index_col=0)
    nv = np.cumprod(1 + star["return"].to_numpy())
    dates = pd.to_datetime(star.index)
    axs[0].plot(dates, nv, label="STAR50 V2", ls="--", alpha=0.7)
    axs[1].plot(dates, 100 * (nv / np.maximum.accumulate(np.r_[1.0, nv])[1:] - 1), label="STAR50 V2", ls="--", alpha=0.7)
    for ax, title in zip(axs, ["固定迁移净值：每边2bp费用代理", "每日权益回撤（%）；汇总表为逐分钟MDD"], strict=True):
        ax.set_title(title, fontproperties=font)
        ax.legend()
        ax.grid(alpha=0.2)
    fig.suptitle(
        "半日低通120分钟 · 中证1000 1m · 2021–2025\nV2全部参数原样迁移，未重新选参；指数方向模拟", fontproperties=font, fontsize=15
    )
    fig.savefig(dest / "migration_comparison.png", dpi=160)
    plt.close(fig)
    table = migration.copy()
    for c in ["return", "cagr", "mdd", "win_rate"]:
        table[c] *= 100
    shown = table[["label", "fee_bps_per_side", "trades", "mean_net_bp", "sharpe", "cagr", "mdd", "win_rate"]].round(4)
    page = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>分辨率与中证1000迁移</title>
<style>body{{max-width:1200px;margin:30px auto;padding:0 20px;font:16px system-ui;color:#243347}}img{{width:100%}}table{{border-collapse:collapse;font-size:12px}}td,th{{padding:7px;border:1px solid #ddd}}p{{line-height:1.8}}</style>
<h1>科创50ETF秒级路径效率与中证1000固定迁移</h1><p>秒级数据来自588000/588080 ETF，不是科创50指数。固定物理回看时长并统一观察点；原始方差下降不能单独认定更平稳或更适合交易。</p>
<p><a href="../../../docs/research/resolution_transfer_v1/result.md">中文结果解释</a> · <a href="../../../docs/research/resolution_transfer_v1/protocol.md">结果前合同</a></p>
<img src="resolution_comparison.png"><h2>固定参数迁移</h2><p>1m / 120分钟低通；2021—2025。下表cagr、mdd、win_rate为%，单笔mean_net_bp单位bp。手续费为每边代理，不是IM/MO实际盘口回测。</p>{shown.to_html(index=False)}
<img src="migration_comparison.png"><p><a href="resolution_summary.csv">全部分辨率/价格/窗口结果</a> · <a href="visible_path_ratio.csv">粗细路程比</a> · <a href="retrospective_shapes.csv">完成窗后验形态</a> · <a href="migration_annual.csv">迁移年度表</a> · <a href="migration_summary.csv">迁移汇总</a> · <a href="validation.json">对账和来源验证</a></p></html>"""
    (dest / "report.html").write_text(page)


if __name__ == "__main__":
    main()
