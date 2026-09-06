"""Audit frozen V1/V2 accounts, then render reports from saved snapshots."""

# ruff: noqa: E501

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from research_slope_union_v2 import OUT, check, load, save, sha  # noqa: E402
from star50_filter.slope_union import build_signals  # noqa: E402
from star50_filter.slope_union_v2 import Policy, account, features, summary, targets  # noqa: E402


def main():
    check()
    assert (OUT / "2025/review.json").exists()
    final = Policy(**json.loads((OUT / "2023/review.json").read_text())["selected_config"])
    dest = OUT / "final"
    assert not dest.exists()
    dest.mkdir()
    bars = load(2025)
    y, s, vol = features(bars.close)
    v1_direct = build_signals(bars[["timestamp", "trading_minute", "close"]])
    baseline = targets(s, vol[240], Policy())
    np.testing.assert_array_equal(baseline, v1_direct.target_at_close)
    summaries = []
    annual = []
    replay_checks = []
    all_trades = {}
    all_days = {}
    paths = {}
    yearly = {}
    for label, p in [("V1", Policy()), ("V2", final)]:
        target = targets(s, vol[p.volatility_window], p)
        for fee in [0.0, 2.0, 4.0, 7.0]:
            all_t = []
            all_d = []
            all_nav = []
            capital = 1.0
            for year in range(2021, 2026):
                ix = np.flatnonzero(bars.year.to_numpy() == year)
                part = bars.iloc[ix].reset_index(drop=True)
                mode = "family" if year <= 2023 else "blind"
                frozen = np.load(OUT / str(year) / mode / f"{p.id}_targets.npy")
                np.testing.assert_array_equal(target[ix], frozen)
                t, d, nav, m = account(part.open, part.timestamp - pd.Timedelta(minutes=1), frozen, int(target[ix[0] - 1]), fee)
                # Independent cash/share replay, not the episode-product accounting implementation.
                if fee == 2:
                    pos = np.r_[target[ix[0] - 1], frozen[:-1]]
                    pos[-1] = 0
                    cash, shares, old = 1.0, 0.0, 0
                    independent = []
                    for price, wanted in zip(part.open.to_numpy(), pos, strict=True):
                        if wanted != old:
                            if old:
                                cash += shares * price - abs(shares) * price * 0.0002
                                shares = 0.0
                            if wanted:
                                shares = wanted * cash / (price * 1.0002)
                                cash -= shares * price + abs(shares) * price * 0.0002
                            old = wanted
                        independent.append(cash + shares * price)
                    np.testing.assert_allclose(nav, independent, rtol=1e-11, atol=1e-12)
                    stored = pd.read_parquet(OUT / str(year) / mode / f"{p.id}_trades.parquet")
                    pd.testing.assert_frame_equal(t, stored)
                    pd.testing.assert_frame_equal(d, pd.read_parquet(OUT / str(year) / mode / f"{p.id}_daily.parquet"))
                    replay_checks.append(
                        {
                            "year": year,
                            "label": label,
                            "targets_exact": True,
                            "trades_exact": True,
                            "cash_share_max_error": float(np.max(abs(nav - np.asarray(independent)))),
                        }
                    )
                    snap = part[["timestamp", "open", "high", "low", "close"]].copy()
                    snap["timestamp"] = snap.timestamp - pd.Timedelta(minutes=1)
                    snap["lowpass_known_at_open"] = np.exp(np.r_[np.nan, y[:-1]][ix] + np.log(bars.close.iloc[0]))
                    snap["target_at_close"] = frozen
                    snap["account_nav"] = nav * capital
                    snap.to_parquet(dest / f"{year}_{label}_snapshot.parquet", index=False)
                    t.to_csv(dest / f"{year}_{label}_trades.csv", index=False)
                    yearly[(year, label)] = (snap, t)
                t = t.assign(year=year)
                d = d.assign(year=year)
                annual.append({"year": year, "label": label, "fee_bps": fee, **m})
                all_t.append(t)
                all_d.append(d)
                all_nav.append(nav * capital)
                capital *= nav[-1]
            combined_t = pd.concat(all_t, ignore_index=True)
            combined_d = pd.concat(all_d)
            curve = np.concatenate(all_nav)
            m = summary(combined_t, combined_d, curve)
            summaries.append({"label": label, "fee_bps": fee, **m})
            if fee == 2:
                all_trades[label] = combined_t
                all_days[label] = combined_d
                paths[label] = curve
                combined_t.to_csv(dest / f"{label}_all_trades.csv", index=False)
                combined_d.to_csv(dest / f"{label}_daily.csv")
                for scope, years in [("design", [2021, 2022, 2023]), ("repeat", [2024, 2025])]:
                    st = combined_t[combined_t.year.isin(years)]
                    sd = combined_d[combined_d.year.isin(years)]
                    summaries.append({"label": label + "_" + scope, "fee_bps": fee, **summary(st, sd)})
    totals = pd.DataFrame(summaries)
    annual = pd.DataFrame(annual)
    totals.to_csv(dest / "summary.csv", index=False)
    annual.to_csv(dest / "annual.csv", index=False)
    # Paired changes: all other parameter coordinates fixed; only 2021..2023 design material.
    frames = [pd.read_csv(OUT / str(year) / "family/metrics.csv").assign(year=year) for year in range(2021, 2024)]
    surface = pd.concat(frames, ignore_index=True)
    axes = ["entry_alpha", "exit_alpha", "weight_power", "volatility_window", "entry_confirm", "cooldown"]
    effects = []
    for axis in axes:
        values = sorted(surface[axis].unique())
        keys = ["year"] + [k for k in axes if k != axis]
        for low, high in zip(values[:-1], values[1:], strict=True):
            paired = surface[surface[axis] == low].merge(surface[surface[axis] == high], on=keys, suffixes=("_low", "_high"))
            delta = paired.mean_net_bp_high - paired.mean_net_bp_low
            effects.append(
                {
                    "parameter": axis,
                    "from": low,
                    "to": high,
                    "pairs": len(paired),
                    "median_delta_mean_net_bp": float(delta.median()),
                    "positive_share": float((delta > 0).mean()),
                    "median_delta_sharpe": float((paired.sharpe_high - paired.sharpe_low).median()),
                    "median_delta_trades": float((paired.trades_high - paired.trades_low).median()),
                }
            )
    pd.DataFrame(effects).to_csv(dest / "parameter_effects.csv", index=False)
    render(dest, totals, annual, all_trades, all_days, yearly, final, effects)
    # Validate every annual receipt, then bind final artifacts and source identity.
    for year in range(2021, 2026):
        for mode in ["blind", "family"] if year <= 2023 else ["blind"]:
            p = OUT / str(year) / mode
            r = json.loads((p / "receipt.json").read_text())
            for name, digest in r["files"].items():
                assert sha(p / name) == digest, (year, mode, name)
            if year > 2021:
                assert r["prior_review_sha256"] == sha(OUT / str(year - 1) / "review.json")
    save(
        dest / "acceptance.json",
        {
            "scientific_status": "retrospective_comparison_not_fresh_oos",
            "final_config": final.__dict__,
            "replay": replay_checks,
            "v1_full_prefix_exact": True,
            "source_2026_rows_read": 0,
            "production_authority": False,
            "source_sha256": {
                n: sha(ROOT / n) for n in ["scripts/report_slope_union_v2.py", "tests/test_slope_union_v2_account_oracle.py"]
            },
            "files": {p.name: sha(p) for p in sorted(dest.iterdir()) if p.is_file()},
        },
    )
    print(totals.to_string(index=False))
    print(annual[annual.fee_bps == 2].to_string(index=False))
    print(pd.DataFrame(effects).to_string(index=False))


def render(dest, totals, annual, trades, days, yearly, final, effects):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties

    font = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
    fig, axs = plt.subplots(2, 2, figsize=(15, 9), layout="constrained")
    colors = {"V1": "#60738b", "V2": "#007f78"}
    for label in ["V1", "V2"]:
        d = days[label]
        nav = np.cumprod(1 + d["return"].to_numpy())
        dates = pd.to_datetime(d.index)
        axs[0, 0].plot(dates, nav, label=label, color=colors[label])
        dd = 1 - nav / np.maximum.accumulate(np.r_[1.0, nav])[1:]
        axs[0, 1].plot(dates, -100 * dd, label=label, color=colors[label])
        v = trades[label].net_bp.to_numpy()
        axs[1, 1].hist(v, bins=np.arange(-1200, 1501, 50), histtype="step", density=True, label=label, color=colors[label])
    a = annual[annual.fee_bps == 2]
    xs = np.arange(5)
    for i, label in enumerate(["V1", "V2"]):
        rows = a[a.label == label].sort_values("year")
        axs[1, 0].bar(xs + (i - 0.5) * 0.34, rows.mean_net_bp, 0.34, label=label, color=colors[label])
    axs[1, 0].set_xticks(xs, ["2021", "2022", "2023", "2024", "2025"])
    titles = ["净值：每边2bp费用代理", "每日权益回撤（%）", "平均每笔净简单收益（bp）", "逐笔收益分布（bp；完整尾部见CSV）"]
    for ax, title in zip(axs.flat, titles, strict=True):
        ax.set_title(title, fontproperties=font)
        ax.grid(alpha=0.2)
        ax.legend()
    axs[1, 0].axhline(0, color="black", lw=0.7)
    fig.suptitle(
        "科创50半日低通 V1 / V2 · 指数方向模拟\n2021–2023选参；2024–2025冻结后重复历史检验；非实盘ETF/期权",
        fontproperties=font,
        fontsize=17,
    )
    fig.savefig(dest / "comparison.png", dpi=170)
    plt.close(fig)
    for year in range(2021, 2026):
        snap, t = yearly[(year, "V2")]
        render_trade_html(dest / f"trades_{year}.html", snap, t, year)
    table = totals[totals.label.isin(["V1", "V2"])].copy()
    for col in ["win_rate", "short_hold_fraction", "return", "cagr", "mdd"]:
        table[col] *= 100
    columns = ["label", "fee_bps", "trades", "mean_net_bp", "median_net_bp", "sharpe", "cagr", "mdd", "win_rate", "mean_bars"]
    html = table[columns].round(4).to_html(index=False)
    detail = a[["year", "label", "trades", "mean_net_bp", "sharpe", "return", "mdd"]].copy()
    detail["return"] *= 100
    detail["mdd"] *= 100
    html_year = detail.round(4).to_html(index=False)
    links = " · ".join(f'<a href="trades_{y}.html">{y}年1分钟K线与V2交易</a>' for y in range(2021, 2026))
    page = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>科创50 V2回测</title>
<style>body{{max-width:1250px;margin:30px auto;padding:0 20px;font:16px system-ui;color:#213043}}table{{border-collapse:collapse;font-size:13px;width:100%}}td,th{{padding:8px;border:1px solid #dde3e9}}th{{background:#edf5f3}}img{{width:100%}}a{{color:#007f78}}p{{line-height:1.8}}code{{background:#f0f3f6}}</style>
<h1>科创50半日低通 · V2回测报告</h1><p>首要目标：平均每笔净收益。固定1分钟、半日低通、五窗并集、多空镜像。2021—2023的324组有界参数研究后冻结V2；2024—2025只检验，不再排名或改参。全部历史已消费，非新鲜样本。</p>
<p>账户：指数方向模拟，下一根原始开盘价、单笔固定入场份额、年度账户隔离并顺次复投。费用是每边bp代理，非ETF/期权真实成交。CAGR / MDD / win_rate以百分数展示，mean_net_bp以bp展示。净值图回撤为每日口径，下表全期MDD为逐分钟。</p>
<p>V2参数：<code>{final.id}</code>。<a href="../../../docs/research/half_day_slope_union_v2/whitepaper.md">结果前白皮书</a> · <a href="../../../docs/research/half_day_slope_union_v2/selection_amendment.md">开发结果后选择规则修订</a>。原AI自加的每年100笔硬门在开发后撤销，此修订已在2024读取前冻结；不是全程纯预注册。</p>
<p>{links}</p><img src="comparison.png" alt="V1与V2净值回撤单笔质量对照"><h2>完整五年与成本压力</h2>{html}<h2>逐年结果：每边2bp</h2>{html_year}
<h2>参数配对影响（只使用2021—2023）</h2>{pd.DataFrame(effects).round(4).to_html(index=False)}
<p>更多：<a href="summary.csv">汇总CSV</a> · <a href="annual.csv">年度CSV</a> · <a href="V1_all_trades.csv">V1逐笔</a> · <a href="V2_all_trades.csv">V2逐笔</a> · <a href="parameter_effects.csv">参数配对表</a> · <a href="acceptance.json">复核收据</a></p></html>"""
    (dest / "report.html").write_text(page)


def render_trade_html(path, snap, trades, year):
    data = {
        "t": snap.timestamp.dt.strftime("%Y-%m-%d %H:%M").tolist(),
        "v": np.round(snap[["open", "high", "low", "close", "lowpass_known_at_open"]].to_numpy(), 5).tolist(),
        "trades": trades[["entry_i", "exit_i", "side", "net_bp"]].round(4).values.tolist(),
    }
    html = TRADE_HTML.replace("__YEAR__", str(year)).replace("__DATA__", json.dumps(data, separators=(",", ":")))
    path.write_text(html)


TRADE_HTML = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>科创50 __YEAR__ V2交易</title>
<style>body{margin:20px;font:15px system-ui;color:#203347}button,input,select{padding:8px;margin:4px;font:inherit}canvas{width:100%;height:700px;border:1px solid #ddd}#info{min-height:30px}a{color:#007f78}</style>
<h1>科创50 __YEAR__ · V2 1分钟交易图</h1><p>上层原始1分钟K线，下层开盘时已知低通值。红线=买入方向，蓝线=卖出方向；反手同时包含平仓和开仓。休市压缩。指数模拟，非ETF/期权实际成交。</p>
<p><a href="report.html">返回回测总览</a></p><button onclick="zoom(.5)">放大</button><button onclick="zoom(2)">缩小</button><button onclick="start-=count;draw()">前移</button><button onclick="start+=count;draw()">后移</button><input type="date" id="date"><button onclick="goDate()">定位日期</button><select id="trade" onchange="goTrade()"></select><button onclick="savePNG()">保存视图PNG</button>
<p id="info"></p><canvas id="chart"></canvas><script>
const D=__DATA__,cv=document.getElementById('chart'),ctx=cv.getContext('2d');let start=0,count=720,W=1200,H=700;
const select=document.getElementById('trade');D.trades.forEach((t,i)=>{let o=document.createElement('option');o.value=i;o.textContent=(i+1)+' '+D.t[t[0]]+' '+(t[2]>0?'多':'空')+' '+t[3].toFixed(2)+'bp';select.appendChild(o)});
function draw(){count=Math.max(30,Math.min(D.t.length,Math.round(count)));start=Math.max(0,Math.min(D.t.length-count,Math.round(start)));W=cv.clientWidth;let r=devicePixelRatio||1;cv.width=W*r;cv.height=H*r;ctx.setTransform(r,0,0,r,0,0);ctx.fillStyle='white';ctx.fillRect(0,0,W,H);
let end=start+count,L=65,R=W-20,lo=Infinity,hi=-Infinity,yl=Infinity,yh=-Infinity;for(let i=start;i<end;i++){lo=Math.min(lo,D.v[i][2]);hi=Math.max(hi,D.v[i][1]);yl=Math.min(yl,D.v[i][4]);yh=Math.max(yh,D.v[i][4])}let pad=(hi-lo)*.05||1;lo-=pad;hi+=pad;pad=(yh-yl)*.05||1;yl-=pad;yh+=pad;
const X=i=>L+(i-start+.5)*(R-L)/count,Y=v=>310-(v-lo)/(hi-lo)*270,Z=v=>630-(v-yl)/(yh-yl)*250;
ctx.font='12px sans-serif';for(let k=0;k<=4;k++){ctx.fillStyle='#567';ctx.fillText((hi-(hi-lo)*k/4).toFixed(2),4,40+k*67.5);ctx.fillText((yh-(yh-yl)*k/4).toFixed(2),4,380+k*62.5);ctx.strokeStyle='#edf0f4';ctx.beginPath();ctx.moveTo(L,40+k*67.5);ctx.lineTo(R,40+k*67.5);ctx.moveTo(L,380+k*62.5);ctx.lineTo(R,380+k*62.5);ctx.stroke()}
let bw=Math.max(.6,Math.min(10,(R-L)/count*.65));for(let i=start;i<end;i++){let v=D.v[i],x=X(i);ctx.strokeStyle=ctx.fillStyle=v[3]>=v[0]?'#c74755':'#17866f';ctx.beginPath();ctx.moveTo(x,Y(v[1]));ctx.lineTo(x,Y(v[2]));ctx.stroke();ctx.fillRect(x-bw/2,Math.min(Y(v[0]),Y(v[3])),bw,Math.max(1,Math.abs(Y(v[0])-Y(v[3]))))}
ctx.strokeStyle='#334b6e';ctx.lineWidth=1.4;ctx.beginPath();for(let i=start;i<end;i++){if(i===start)ctx.moveTo(X(i),Z(D.v[i][4]));else ctx.lineTo(X(i),Z(D.v[i][4]))}ctx.stroke();ctx.lineWidth=1;
for(let t of D.trades){for(let [i,side,kind] of [[t[0],t[2],'开'],[t[1],-t[2],'平']]){if(i<start||i>=end)continue;let x=X(i),z=Z(D.v[i][4]);ctx.strokeStyle=ctx.fillStyle=side>0?'#d84050':'#2563cf';ctx.setLineDash([4,5]);ctx.beginPath();ctx.moveTo(x,Y(D.v[i][0]));ctx.lineTo(x,z);ctx.stroke();ctx.setLineDash([]);ctx.beginPath();ctx.arc(x,z,4,0,Math.PI*2);ctx.fill();if(count<1600)ctx.fillText(kind,x+4,z-8)}}
ctx.fillStyle='#456';for(let k=0;k<=5;k++){let i=start+Math.floor((count-1)*k/5);ctx.fillText(D.t[i].slice(5),Math.min(R-95,X(i)),675)}document.getElementById('info').textContent=D.t[start]+' 至 '+D.t[end-1]+' · '+count+'根';}
function zoom(f){let center=start+count/2;count*=f;start=center-count/2;draw()}function goDate(){let i=D.t.findIndex(t=>t.slice(0,10)>=document.getElementById('date').value);if(i>=0){start=i;count=720;draw()}}function goTrade(){let t=D.trades[+select.value];start=t[0]-80;count=t[1]-t[0]+160;draw()}function savePNG(){let a=document.createElement('a');a.download='STAR50_V2___YEAR__.png';a.href=cv.toDataURL();a.click()}
cv.addEventListener('wheel',e=>{e.preventDefault();zoom(e.deltaY>0?1.2:1/1.2)},{passive:false});window.onresize=draw;draw();</script></html>"""


if __name__ == "__main__":
    main()
