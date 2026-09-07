"""Report the frozen tail analysis with global multiplicity and severity checks."""

# ruff: noqa: E402, E501
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from research_tail_distribution_v1 import OUT, SYMBOLS, check, cube, save, sha
from star50_filter.tail_distribution import clustering_tests, holm


def main():
    check()
    dest = OUT / "final"
    assert not dest.exists()
    dest.mkdir()
    tables = {
        n: pd.concat([pd.read_csv(OUT / f"{m}m" / f"{n}.csv") for m in [1, 5]], ignore_index=True)
        for n in ["marginals", "clustering", "conditions", "tests", "forecasts", "severity", "boundaries", "coincidences"]
    }
    assert len(tables["tests"]) == 24
    tables["tests"]["p_holm"] = holm(tables["tests"].p_raw)
    for name, table in tables.items():
        table.to_csv(dest / f"{name}.csv", index=False)
    joint = []
    volumes = []
    pooled = []
    audits = []
    panels = {}
    for m in [1, 5]:
        receipt = json.loads((OUT / f"{m}m/receipt.json").read_text())
        for p, h in receipt["files"].items():
            assert sha(OUT / f"{m}m" / p) == h
        panel = pd.read_parquet(OUT / f"panel_{m}m.parquet")
        panels[m] = panel
        cut = json.loads((OUT / f"cutoffs_{m}m.json").read_text())
        for symbol, full in panel.groupby("symbol"):
            full = full.sort_values("timestamp").reset_index(drop=True)
            f = full[(full.year >= 2024) & ~full.boundary].copy()
            raw = f.r.abs() > cut["tail_cutoffs"]["raw"]
            std = f.z.abs() > cut["tail_cutoffs"]["standardized"]
            f["joint"] = np.select(
                [raw & std, raw & ~std, ~raw & std], ["large_and_unexpected", "large_only", "unexpected_only"], default="ordinary"
            )
            for label, g in f.groupby("joint"):
                joint.append(
                    {
                        "minutes": m,
                        "symbol": symbol,
                        "class": label,
                        "count": len(g),
                        "rate": len(g) / len(f),
                        "mean_abs_simple_bp": np.expm1(g.r).abs().mean() * 10000,
                        "max_abs_simple_bp": np.expm1(g.r).abs().max() * 10000,
                        "squared_return_share": (g.r**2).sum() / (f.r**2).sum(),
                        "high_vol_capture": (g.vol_bin == 2).mean(),
                        "high_vol_squared_capture": (g.loc[g.vol_bin == 2, "r"] ** 2).sum() / (g.r**2).sum(),
                    }
                )
            for basis, column in [("raw", "r"), ("standardized", "z"), ("robust", "robust_z")]:
                valid = f[column].notna()
                event = f[column].abs() > cut["tail_cutoffs"][basis]
                g = f[event]
                pooled.append(
                    {
                        "minutes": m,
                        "symbol": symbol,
                        "basis": basis,
                        "bars": int(valid.sum()),
                        "events": int(event.sum()),
                        "rate": event.sum() / valid.sum(),
                        "up": int((g.r > 0).sum()),
                        "down": int((g.r < 0).sum()),
                        "mean_abs_tail_bp": np.expm1(g.r).abs().mean() * 10000,
                        "squared_return_share": (g.r**2).sum() / (f.loc[valid, "r"] ** 2).sum(),
                    }
                )
                for vol, h in f[valid].groupby("vol_bin"):
                    e = h[column].abs() > cut["tail_cutoffs"][basis]
                    volumes.append(
                        {
                            "minutes": m,
                            "symbol": symbol,
                            "basis": basis,
                            "vol_bin": vol,
                            "bars": len(h),
                            "events": int(e.sum()),
                            "rate": e.mean(),
                            "time_share": len(h) / valid.sum(),
                            "capture": e.sum() / event.sum(),
                            "square_move_capture": (h.loc[e, "r"] ** 2).sum() / (g.r**2).sum(),
                        }
                    )
            # Independently recompute the top actual ordinary-return rows and their strictly lagged scale.
            ix = full.index[(full.year >= 2024) & ~full.boundary]
            ix = full.loc[ix, "r"].abs().nlargest(20).index
            for i in ix:
                direct = np.log(float(full.close.iloc[i]) / float(full.close.iloc[i - 1]))
                past = full.r.iloc[i - 480 // m : i].to_numpy(float)
                s = float(np.nanstd(past, ddof=1))
                assert abs(direct - full.r.iloc[i]) < 1e-13
                assert np.isclose(s, full.sigma_prior.iloc[i], rtol=1e-10, atol=1e-14)
                assert full.prediction_time.iloc[i] < full.timestamp.iloc[i]
                audits.append(
                    {
                        "minutes": m,
                        "symbol": symbol,
                        "timestamp": str(full.timestamp.iloc[i]),
                        "return_error": abs(direct - full.r.iloc[i]),
                        "sigma_error": abs(s - full.sigma_prior.iloc[i]),
                    }
                )
    pd.DataFrame(joint).to_csv(dest / "joint_size_surprise.csv", index=False)
    pd.DataFrame(volumes).to_csv(dest / "volatility_conditions.csv", index=False)
    pd.DataFrame(pooled).to_csv(dest / "repeat_tail_summary.csv", index=False)
    # Reproduce one full inference array with its declared seed, not a new hypothesis.
    f = panels[1]
    f = f[(f.symbol == "000852.SH") & (f.year >= 2024) & ~f.boundary].copy()
    cut = json.loads((OUT / "cutoffs_1m.json").read_text())
    f["event"] = f.z.abs() > cut["tail_cutoffs"]["standardized"]
    y, days = cube(f, "event")
    vol, _ = cube(f, "vol_bin")
    _, null = clustering_tests(y, vol, np.array([int(d[:4]) for d in days]), 5, seed=20260907 + 1 + 200)
    np.testing.assert_array_equal(null, np.load(OUT / "1m/000852.SH_standardized_null.npy"))
    render(dest, tables, pd.DataFrame(pooled), pd.DataFrame(volumes), panels)
    save(
        dest / "validation.json",
        {
            "source_sha256": sha(Path(__file__)),
            "freeze_sha256": sha(OUT / "freeze.json"),
            "direct_extreme_row_audits": audits,
            "null_replay_exact": True,
            "primary_test_count": 24,
            "year_clock_multiplicity": "Holm",
            "new_returns_backtest": False,
            "new_router": False,
            "fresh_oos": False,
            "production_authority": False,
            "files": {p.name: sha(p) for p in sorted(dest.iterdir()) if p.is_file()},
        },
    )
    print(pd.DataFrame(pooled).to_string(index=False))
    print(pd.DataFrame(joint).to_string(index=False))
    print(tables["tests"].to_string(index=False))


def render(dest, tables, pooled, volumes, panels):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties

    font = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
    colors = {"000852.SH": "#197b8f", "000688.SH": "#c55a27"}
    names = {"000852.SH": "CSI1000", "000688.SH": "STAR50"}
    fig, axs = plt.subplots(2, 2, figsize=(15, 9), layout="constrained")
    f = panels[1]
    f = f[(f.year >= 2024) & ~f.boundary]
    cutoff = json.loads((OUT / "cutoffs_1m.json").read_text())["tail_cutoffs"]["raw"]
    grid = np.geomspace(0.1, 400, 220)
    for symbol, g in f.groupby("symbol"):
        x = np.sort(g.r.abs().to_numpy() * 10000)
        rate = (len(x) - np.searchsorted(x, grid, side="right")) / len(x)
        axs[0, 0].loglog(grid, np.maximum(rate, 1 / len(x)), label=names[symbol], color=colors[symbol])
        for basis, style in [("raw", "-"), ("standardized", "--")]:
            q = volumes[(volumes.minutes == 1) & (volumes.symbol == symbol) & (volumes.basis == basis)].sort_values("vol_bin")
            axs[0, 1].plot(q.vol_bin, q.rate * 100, style, marker="o", label=f"{names[symbol]} {basis}", color=colors[symbol])
        daily = (g.r.abs() > cutoff).groupby(g.day).sum()
        axs[1, 0].plot(pd.to_datetime(daily.index), daily, label=names[symbol], color=colors[symbol], alpha=0.8)
    axs[0, 0].axvline(cutoff * 10000, color="gray", ls=":")
    axs[0, 0].set_xlabel("absolute log return (bp)")
    axs[0, 0].set_ylabel("exceedance probability")
    axs[0, 1].set_xticks([0, 1, 2], ["low", "medium", "high"])
    axs[0, 1].set_ylabel("tail rate (%)")
    cl = tables["clustering"]
    cl = cl[cl.minutes == 1]
    xs = np.arange(len(cl))
    axs[1, 1].bar(xs - 0.17, cl.no_recent_rate * 100, 0.34, label="no previous 5m tail")
    axs[1, 1].bar(xs + 0.17, cl.after5_rate * 100, 0.34, label="previous 5m tail")
    axs[1, 1].set_xticks(xs, [names[r.symbol] + "\n" + r.basis for r in cl.itertuples()], fontsize=9)
    axs[1, 1].set_ylabel("next bar tail rate (%)")
    titles = ["同一分钟收益的尾概率", "事前波动三桶：绝对尾部与相对异常", "绝对尾部每日计数", "已发生尾部后，与此前平静时的下一根风险"]
    for ax, title in zip(axs.flat, titles, strict=True):
        ax.set_title(title, fontproperties=font)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8)
    fig.suptitle(
        "中证1000 vs 科创50 · 2024—2025固定检验\n阈值仅2021—2023共同标定；普通连续时段，边界另列", fontproperties=font, fontsize=16
    )
    fig.savefig(dest / "tail_comparison.png", dpi=160)
    plt.close(fig)
    fig, axs = plt.subplots(2, 1, figsize=(13, 7), layout="constrained")
    full = panels[1]
    for ax, symbol in zip(axs, SYMBOLS, strict=True):
        g = full[(full.symbol == symbol) & (full.year >= 2024)].reset_index(drop=True)
        k = int(g.loc[~g.boundary, "r"].abs().idxmax())
        event = g.iloc[k]
        segment = g[(g.day == event.day) & (g.session == event.session)]
        chosen = segment[
            (segment.timestamp >= event.timestamp - pd.Timedelta(minutes=10))
            & (segment.timestamp <= event.timestamp + pd.Timedelta(minutes=15))
        ]
        x = (chosen.timestamp - event.timestamp).dt.total_seconds() / 60
        ax.plot(x, chosen.close, label=names[symbol])
        ax.axvline(0, color="red", ls="--")
        ax.set_title(f"{names[symbol]} {event.timestamp} | event = {np.expm1(event.r) * 100:.2f}%", fontsize=12)
        ax.set_xlabel("minutes relative to tail close")
        ax.grid(alpha=0.2)
    fig.suptitle("各指数最大普通一分钟尾部及相邻路径（事后案例，不是提前预警）", fontproperties=font, fontsize=14)
    fig.savefig(dest / "largest_event_paths.png", dpi=160)
    plt.close(fig)
    shown = pooled[pooled.basis != "robust"].copy()
    shown["rate_pct"] = shown.rate * 100
    shown["squared_return_pct"] = shown.squared_return_share * 100
    page = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>两指数尾部与聚集分析</title>
<style>body{{max-width:1280px;margin:30px auto;padding:0 18px;font:16px system-ui;color:#23364a}}img{{width:100%}}p{{line-height:1.8}}table{{border-collapse:collapse;font-size:12px}}td,th{{border:1px solid #ddd;padding:7px}}</style>
<h1>中证1000与科创50：尾部涨跌和事前风险状态</h1><p>2021—2023共同标定，2024—2025固定重复历史检验；1m主分析、5m复核。绝对尾部和相对事前波动的异常分别统计，开盘/午休边界单列。没有新策略或交易路由。</p>
<p><a href="../../../docs/research/tail_distribution_v1/result.md">中文结论与限制</a> · <a href="../../../docs/research/tail_distribution_v1/protocol.md">结果前方案</a></p>
<img src="tail_comparison.png"><h2>尾部占比和严重度</h2>{shown[["minutes", "symbol", "basis", "bars", "events", "rate_pct", "up", "down", "mean_abs_tail_bp", "squared_return_pct"]].round(4).to_html(index=False)}
<img src="largest_event_paths.png"><h2>24项共同Holm校正</h2>{tables["tests"].round(5).to_html(index=False)}
<p><a href="volatility_conditions.csv">事前波动条件</a> · <a href="joint_size_surprise.csv">幅度×异常交叉表</a> · <a href="clustering.csv">聚集与首个事件</a> · <a href="forecasts.csv">固定概率预测</a> · <a href="severity.csv">经济幅度阈值计数</a> · <a href="boundaries.csv">边界跳变</a> · <a href="validation.json">核验回执</a></p></html>"""
    (dest / "report.html").write_text(page)


if __name__ == "__main__":
    main()
