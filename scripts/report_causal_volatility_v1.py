"""Assess level forecasting separately from session-opening and interior surges."""

# ruff: noqa: E402, E501
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from research_causal_volatility_v1 import INPUT, OUT, SYMBOLS, check, regression_metrics, save, sha
from star50_filter.causal_volatility import FLOOR, VolatilityModel, event_metrics, forecast_latest


def block_interval(frame):
    y = np.log(np.maximum(frame.actual_sigma.to_numpy(), np.sqrt(FLOOR)))
    a = (np.log(frame.forecast_sigma.to_numpy()) - y) ** 2
    b = (np.log(np.maximum(frame.past_sigma.to_numpy(), np.sqrt(FLOOR))) - y) ** 2
    f = pd.DataFrame({"day": frame.day, "delta": a - b})
    daily = f.groupby("day").delta.mean()
    years = pd.Index(daily.index).str[:4]
    rng = np.random.default_rng(20260907)
    draws = []
    for _ in range(999):
        parts = []
        for year in ["2024", "2025"]:
            values = daily[years == year].to_numpy()
            n = len(values)
            starts = rng.integers(0, n - 4, size=int(np.ceil(n / 5)))
            indices = (starts[:, None] + np.arange(5)).reshape(-1)[:n]
            parts.append(values[indices])
        draws.append(np.concatenate(parts).mean())
    lo, hi = np.quantile(draws, [0.0125, 0.9875])
    return {
        "mean_squared_log_error_difference": float((a - b).mean()),
        "ci97_5_low": float(lo),
        "ci97_5_high": float(hi),
        "block_trading_days": 5,
        "bootstrap_replicates": 999,
    }


def main():
    check()
    assert (OUT / "2025/review.json").exists()
    fit = json.loads((OUT / "fit_receipt.json").read_text())
    assert fit["freeze_sha256"] == sha(OUT / "freeze.json")
    for entry in fit["models"]:
        root = OUT / "models" / f"{entry['symbol']}_{entry['horizon']}"
        assert sha(root / "model.json") == entry["metadata_sha256"]
        assert sha(root / "parameters.npz") == entry["parameters_sha256"]
    dest = OUT / "final"
    assert not dest.exists()
    dest.mkdir()
    for year in [2024, 2025]:
        root = OUT / str(year)
        r = json.loads((root / "receipt.json").read_text())
        assert r["fit_receipt_sha256"] == sha(OUT / "fit_receipt.json")
        for name, h in r["files"].items():
            assert sha(root / name) == h, name
        assert json.loads((root / "review.json").read_text())["receipt_sha256"] == sha(root / "receipt.json")
        if year == 2025:
            assert r["prior_review_sha256"] == sha(OUT / "2024/review.json")
    summaries = []
    events = []
    intervals = []
    phases = []
    boot = []
    frames = {}
    audit = []
    for symbol in SYMBOLS:
        original = (
            pd.read_parquet(INPUT, filters=[("symbol", "==", symbol), ("year", "<=", 2025)]).sort_values("timestamp").reset_index(drop=True)
        )
        for h in [5, 15, 30]:
            model = VolatilityModel.load(OUT / "models" / f"{symbol}_{h}")
            f = pd.concat(
                [pd.read_parquet(OUT / str(y) / f"{symbol}_{h}_predictions.parquet").assign(year=y) for y in [2024, 2025]],
                ignore_index=True,
            )
            frames[(symbol, h)] = f
            for sampling, chosen in [("dense", f), ("nonoverlap", f[f.nonoverlap])]:
                for name, column in [("multiscale", "forecast_sigma"), ("persistence", "past_sigma"), ("clock_only", "clock_sigma")]:
                    metrics, cm = regression_metrics(chosen.actual_sigma, chosen[column], model.state_edges)
                    summaries.append({"symbol": symbol, "horizon": h, "sampling": sampling, "model": name, **metrics})
                    save(
                        dest / f"{symbol}_{h}_{sampling}_{name}_confusion.json",
                        {"states": ["low", "medium", "high"], "rows_actual_columns_predicted": cm.tolist()},
                    )
                intervals.append(
                    {
                        "symbol": symbol,
                        "horizon": h,
                        "sampling": sampling,
                        "rows": len(chosen),
                        "coverage_80": float(
                            ((chosen.actual_sigma >= chosen.sigma_p10) & (chosen.actual_sigma <= chosen.sigma_p90)).mean()
                        ),
                        "median_interval_ratio": float((chosen.sigma_p90 / chosen.sigma_p10).median()),
                    }
                )
                segments = {
                    "all": chosen,
                    "first_decision": chosen[chosen.session_slot == 1],
                    "first_30min": chosen[chosen.session_slot <= 30],
                    "after_30min": chosen[chosen.session_slot > 30],
                    "quiet_after_30min": chosen[(chosen.session_slot > 30) & chosen.quiet_context],
                }
                for segment, g in segments.items():
                    for factor in [2, 3, 4]:
                        events.append(
                            {
                                "symbol": symbol,
                                "horizon": h,
                                "sampling": sampling,
                                "segment": segment,
                                "factor": factor,
                                **event_metrics(g[f"actual_amplify_{factor}"], g[f"p_amplify_{factor}"] >= 0.5),
                            }
                        )
            for phase in range(h):
                g = f[(f.session_slot - 1) % h == phase]
                phases.append({"symbol": symbol, "horizon": h, "phase": phase, **event_metrics(g.actual_amplify_2, g.p_amplify_2 >= 0.5)})
            if h == 15:
                boot.append({"symbol": symbol, **block_interval(f)})
            # Direct future-window arithmetic on actual prices/returns, independent of the rolling implementation.
            loc = pd.Index(original.timestamp).get_indexer(f.timestamp)
            for j in np.linspace(0, len(f) - 1, 25, dtype=int):
                i = loc[j]
                window = original.iloc[i + 1 : i + h + 1]
                assert len(window) == h and window.day.nunique() == 1 and window.session.nunique() == 1
                direct = float(np.sqrt(np.mean(window.r.to_numpy() ** 2)))
                assert abs(direct - f.actual_sigma.iloc[j]) < 1e-12
                audit.append(
                    {
                        "symbol": symbol,
                        "horizon": h,
                        "timestamp": str(f.timestamp.iloc[j]),
                        "target_error": abs(direct - f.actual_sigma.iloc[j]),
                    }
                )
        # Past-only historical call example, deliberately not a live-market quote.
        model = VolatilityModel.load(OUT / "models" / f"{symbol}_15")
        final_day = original.day.max()
        prefix = original[original.timestamp <= pd.Timestamp(final_day + " 14:45", tz="Asia/Shanghai")]
        example = forecast_latest(prefix, model)
        assert "actual_sigma" not in example
        save(dest / f"{symbol}_historical_api_example.json", {"example_type": "historical_prefix_not_live_market", **example})
    metrics = pd.DataFrame(summaries)
    event_table = pd.DataFrame(events)
    metrics.to_csv(dest / "metrics.csv", index=False)
    event_table.to_csv(dest / "surge_events.csv", index=False)
    pd.DataFrame(intervals).to_csv(dest / "intervals.csv", index=False)
    pd.DataFrame(phases).to_csv(dest / "phase_sensitivity.csv", index=False)
    pd.DataFrame(boot).to_csv(dest / "block_bootstrap.csv", index=False)
    render(dest, metrics, event_table, pd.DataFrame(intervals), frames)
    save(
        dest / "validation.json",
        {
            "source_sha256": sha(Path(__file__)),
            "freeze_sha256": sha(OUT / "freeze.json"),
            "fit_receipt_sha256": sha(OUT / "fit_receipt.json"),
            "future_window_direct_audits": audit,
            "all_model_and_evaluation_receipts_verified": True,
            "new_router": False,
            "production_authority": False,
            "status": "level_forecast_progress_opening_dominated_surge_detection_interior_warning_insufficient",
            "files": {p.name: sha(p) for p in sorted(dest.iterdir()) if p.is_file()},
        },
    )
    print(metrics.query('horizon==15 and sampling=="dense"').to_string(index=False))
    print(event_table.query('horizon==15 and sampling=="dense" and factor==2').to_string(index=False))
    print(pd.DataFrame(intervals).query("horizon==15").to_string(index=False))
    print(pd.DataFrame(boot).to_string(index=False))


def render(dest, metrics, events, intervals, frames):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties

    font = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
    names = {"000852.SH": "CSI1000", "000688.SH": "STAR50"}
    colors = {"000852.SH": "#167f93", "000688.SH": "#c06522"}
    fig, axs = plt.subplots(2, 2, figsize=(14, 9), layout="constrained")
    for symbol in SYMBOLS:
        f = frames[(symbol, 15)]
        sample = f[f.nonoverlap]
        axs[0, 0].scatter(
            sample.actual_sigma * 10000, sample.forecast_sigma * 10000, s=4, alpha=0.22, label=names[symbol], color=colors[symbol]
        )
    axs[0, 0].plot([0.5, 100], [0.5, 100], "k--", lw=0.8)
    axs[0, 0].set_xscale("log")
    axs[0, 0].set_yscale("log")
    axs[0, 0].set_xlabel("actual future sigma (bp / 1m return)")
    axs[0, 0].set_ylabel("predicted sigma (bp)")
    x = np.arange(2)
    for i, name in enumerate(["persistence", "clock_only", "multiscale"]):
        vals = [
            metrics.loc[
                (metrics.symbol == s) & (metrics.horizon == 15) & (metrics.sampling == "dense") & (metrics.model == name), "log_sigma_rmse"
            ].iloc[0]
            for s in SYMBOLS
        ]
        axs[0, 1].bar(x + (i - 1) * 0.24, vals, 0.24, label=name)
    axs[0, 1].set_xticks(x, ["CSI1000", "STAR50"])
    for i, symbol in enumerate(SYMBOLS):
        q = events.query('symbol==@symbol and horizon==15 and sampling=="dense" and factor==2').set_index("segment")
        seg = ["all", "first_decision", "after_30min"]
        r = [q.loc[k, "recall"] * 100 for k in seg]
        bars = axs[1, 0].bar(np.arange(3) + (i - 0.5) * 0.35, r, 0.35, label=names[symbol], color=colors[symbol])
        for b, value in zip(bars, r, strict=True):
            axs[1, 0].text(b.get_x() + b.get_width() / 2, b.get_height() + 1, f"{value:.1f}", ha="center", fontsize=9)
        q = intervals.query('symbol==@symbol and sampling=="dense"').sort_values("horizon")
        axs[1, 1].plot(q.horizon, q.coverage_80 * 100, "o-", label=names[symbol], color=colors[symbol])
    axs[1, 0].set_xticks([0, 1, 2], ["all times", "first session decision", "after first 30min"])
    axs[1, 0].set_ylim(0, 110)
    axs[1, 1].axhline(80, color="gray", ls="--")
    axs[1, 1].set_xticks([5, 15, 30])
    axs[1, 1].set_xlabel("forecast horizon (minutes)")
    titles = [
        "未来15分钟波动水平：非重叠点展示",
        "逐分钟波动预测误差（越低越好）",
        "翻倍告警召回率：必须拆开开市效应（%）",
        "名义80%预测区间的实际覆盖率（%）",
    ]
    for ax, title in zip(axs.flat, titles, strict=True):
        ax.set_title(title, fontproperties=font)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8)
    fig.suptitle("因果未来波动工具 V1 · 2024—2025固定检验\n预测波动水平有进展；普通时段突变预警仍不足", fontproperties=font, fontsize=16)
    fig.savefig(dest / "forecast_evaluation.png", dpi=160)
    plt.close(fig)
    m = metrics.query('horizon==15 and sampling=="dense"').copy()
    for c in ["bucket_accuracy", "balanced_accuracy", "actual_high_share", "high_precision", "high_recall", "predicted_high_time_share"]:
        m[c] *= 100
    e = events.query('horizon==15 and sampling=="dense" and factor==2').copy()
    for c in ["precision", "recall", "alert_time_share", "false_positive_rate"]:
        e[c] *= 100
    page = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>因果未来波动三桶工具</title>
<style>body{{max-width:1250px;margin:30px auto;padding:0 20px;font:16px system-ui;color:#24374a}}img{{width:100%}}p{{line-height:1.8}}table{{border-collapse:collapse;font-size:12px}}td,th{{border:1px solid #ddd;padding:7px}}</style>
<h1>因果未来波动三桶工具 V1</h1><p>2021—2022拟合，2023校准，2024—2025固定重复检验。目标是未来5/15/30分钟的实现波动，而非涨跌方向。过去窗口与未来窗口不重叠，跨午休/隔夜不输出。</p>
<p><a href="../../../docs/research/causal_volatility_tool_v1/result.md">中文结论</a> · <a href="../../../docs/research/causal_volatility_tool_v1/protocol.md">结果前协议</a> · <a href="../../../docs/research/causal_volatility_tool_v1/workflow.md">接口工作流</a></p>
<img src="forecast_evaluation.png"><h2>15分钟主结果：实际逐分钟运行口径</h2><p>准确率、precision、recall与时间占比以下均为百分数；log误差为无量纲。三桶准确率不等于高桶召回率。</p>{m.round(4).to_html(index=False)}
<h2>未来翻倍且进入高波动的告警</h2><p>阈值为预测概率≥50%；first_decision是9:31/13:01，其余条件不能与它混为任意时刻突发预测。密集窗口重叠，计数是预测时点，不是独立冲击次数。</p>{e.round(4).to_html(index=False)}
<p><a href="metrics.csv">5/15/30分钟全部指标</a> · <a href="surge_events.csv">2/3/4倍及普通时段</a> · <a href="phase_sensitivity.csv">非重叠全相位敏感性</a> · <a href="block_bootstrap.csv">误差区块复核</a> · <a href="intervals.csv">预测区间覆盖</a> · <a href="validation.json">来源与公式核验</a></p></html>"""
    (dest / "report.html").write_text(page)


if __name__ == "__main__":
    main()
