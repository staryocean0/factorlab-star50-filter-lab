"""Render only the user-specified half-trading-day slope strategy."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from reproduce_historical_baseline import load_bars
from star50_filter.filters import butter_lowpass
from star50_filter.backtest import execute_next_open

OUT = ROOT / 'artifacts/half_day_chart_2025_apr_sep'

HTML = r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>科创50｜0.5交易日低通｜2025年4—9月</title>
<style>
body{margin:0;background:#f5f7fb;color:#203047;font:14px system-ui,sans-serif}header{padding:16px 24px;background:white;border-bottom:1px solid #dce2eb}h1{font-size:22px;margin:0 0 8px}.sub{color:#53657b;line-height:1.7}.controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:12px}button,input{font:inherit;border:1px solid #cbd5e1;border-radius:5px;background:white;padding:6px 10px}button{cursor:pointer}button:hover{background:#eef4ff}.buy{color:#d93e50}.sell{color:#2563d9}main{padding:12px 16px}canvas{display:block;background:white;border:1px solid #dde4ee;width:100%;touch-action:none;cursor:crosshair}#info{background:white;padding:10px 16px;min-height:22px;font-variant-numeric:tabular-nums}#scroll{box-sizing:border-box;width:100%;padding:0}footer{padding:8px 22px 18px;color:#53657b;font-size:12px;line-height:1.7}
</style><header><h1>科创50 · 0.5交易日低通与买卖点</h1>
<div class="sub">2025-04-01 — 2025-09-30｜5分钟K线｜一阶Butterworth，截止周期24根｜按低通斜率反手，无σ滞回门槛<br>
<span class="buy">▲ 红色虚线：买入／反多</span>　<span class="sell">▼ 蓝色虚线：卖出／反空</span>　虚线从下层执行点连到上层该根K线开盘价。</div>
<div class="controls"><button id="all">全区间</button><button id="week">一周细看</button><button id="zoomIn">放大＋</button><button id="zoomOut">缩小－</button><button id="prev">向前</button><button id="next">向后</button>
<span>日期</span><input id="from" type="date" value="2025-04-01"><input id="to" type="date" value="2025-09-30"><button id="apply">定位</button><label><input id="links" type="checkbox" checked>显示连接虚线</label><button id="download">保存当前视图PNG</button><span id="range"></span></div></header>
<main><canvas id="chart"></canvas><input id="scroll" type="range" min="0" step="1" value="0"><div id="info">滚轮缩放，拖动平移；悬停查看K线与交易。两层时间轴同步。</div></main>
<footer>休市时间压缩，保留全部5分钟K线，不降采样。下层为本根开盘时已知的低通值（上一根收盘计算值），交易按下一根可交易开盘定位；不使用买入之后的信息产生信号。买卖包括双向策略的反手，不是仅做多账户。<br>这是按用户指定0.5交易日参数及历史斜率／下一开盘协议重建的图，不是此前LP12＋波动率滞回版本。对应重建回撤21.05%，峰谷源行标签为2025-04-07 14:25至2025-09-26 14:10。仅展示2025年4—9月，不执行新研究。</footer>
<script>
const D=__DATA__;
const cv=document.getElementById('chart'),ctx=cv.getContext('2d'),N=D.t.length;
let start=0,count=N,W=1400,H=850,hover=-1,drag=null;
const el=id=>document.getElementById(id),buy='#d93e50',sell='#2563d9';
function bounded(){count=Math.max(24,Math.min(N,Math.round(count)));start=Math.max(0,Math.min(N-count,Math.round(start)));el('scroll').max=N-count;el('scroll').value=start;}
function resize(){W=Math.max(700,cv.clientWidth);H=Math.max(650,Math.min(1000,window.innerHeight-255));let r=window.devicePixelRatio||1;cv.width=Math.round(W*r);cv.height=Math.round(H*r);cv.style.height=H+'px';ctx.setTransform(r,0,0,r,0,0);draw();}
function draw(){bounded();ctx.clearRect(0,0,W,H);ctx.fillStyle='white';ctx.fillRect(0,0,W,H);
 let left=75,right=W-25,pw=right-left,top1=42,bot1=H*.46,top2=H*.56,bot2=H-58,end=start+count;
 let lo=Infinity,hi=-Infinity,l2=Infinity,h2=-Infinity;for(let i=start;i<end;i++){lo=Math.min(lo,D.l[i]);hi=Math.max(hi,D.h[i]);l2=Math.min(l2,D.lp[i]);h2=Math.max(h2,D.lp[i]);}
 let pad=(hi-lo)*.06||1;lo-=pad;hi+=pad;pad=(h2-l2)*.08||1;l2-=pad;h2+=pad;
 const X=i=>left+(i-start+.5)*pw/count,Y=v=>bot1-(v-lo)/(hi-lo)*(bot1-top1),Z=v=>bot2-(v-l2)/(h2-l2)*(bot2-top2);
 ctx.font='13px system-ui';ctx.lineWidth=1;
 function grid(a,b,low,high,label){ctx.fillStyle='#24344a';ctx.fillText(label,left, a-16);for(let k=0;k<=4;k++){let y=a+(b-a)*k/4;ctx.strokeStyle='#e9edf4';ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(right,y);ctx.stroke();ctx.fillStyle='#6b7a90';ctx.textAlign='right';ctx.fillText((high-(high-low)*k/4).toFixed(2),left-9,y+4);}ctx.textAlign='left';}
 grid(top1,bot1,lo,hi,'上层：原始5分钟K线（指数点）');grid(top2,bot2,l2,h2,'下层：开盘时可得的0.5交易日低通值（指数点）');
 if(el('links').checked){ctx.setLineDash([4,5]);ctx.lineWidth=.8;ctx.globalAlpha=count>1000?.19:.5;for(let i=start;i<end;i++)if(D.e[i]){ctx.strokeStyle=D.e[i]>0?buy:sell;ctx.beginPath();ctx.moveTo(X(i),Z(D.lp[i]));ctx.lineTo(X(i),Y(D.o[i]));ctx.stroke();}ctx.globalAlpha=1;ctx.setLineDash([]);}
 let bw=Math.max(.6,Math.min(12,pw/count*.65));
 for(let i=start;i<end;i++){let x=X(i),a=Y(D.o[i]),b=Y(D.c[i]);ctx.strokeStyle=ctx.fillStyle=D.c[i]>=D.o[i]?'#ca4856':'#238d78';ctx.lineWidth=.8;ctx.beginPath();ctx.moveTo(x,Y(D.h[i]));ctx.lineTo(x,Y(D.l[i]));ctx.stroke();ctx.fillRect(x-bw/2,Math.min(a,b),bw,Math.max(1,Math.abs(a-b)));}
 ctx.strokeStyle='#263b62';ctx.lineWidth=1.5;ctx.beginPath();for(let i=start;i<end;i++){if(i==start)ctx.moveTo(X(i),Z(D.lp[i]));else ctx.lineTo(X(i),Z(D.lp[i]));}ctx.stroke();
 let radius=count>1800?2:5;for(let i=start;i<end;i++)if(D.e[i]){let x=X(i),y=Z(D.lp[i]),sg=D.e[i];ctx.fillStyle=sg>0?buy:sell;ctx.beginPath();ctx.moveTo(x,y-sg*radius);ctx.lineTo(x-radius,y+sg*radius);ctx.lineTo(x+radius,y+sg*radius);ctx.closePath();ctx.fill();}
 ctx.fillStyle='#68788e';ctx.font='12px system-ui';ctx.textAlign='center';for(let k=0;k<=6;k++){let i=Math.min(end-1,start+Math.floor((count-1)*k/6));ctx.fillText(D.t[i].slice(5,16),X(i),H-31);}ctx.textAlign='left';
 if(hover>=start&&hover<end){ctx.strokeStyle='#76869b';ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(X(hover),top1);ctx.lineTo(X(hover),bot2);ctx.stroke();ctx.setLineDash([]);}
 el('range').textContent=D.t[start].slice(0,10)+' 至 '+D.t[end-1].slice(0,10)+' · '+count+'根';}
function zoom(f,at=.5){let anchor=start+count*at;count*=f;bounded();start=anchor-count*at;draw();}
el('all').onclick=()=>{start=0;count=N;draw();};el('week').onclick=()=>{count=240;draw();};el('zoomIn').onclick=()=>zoom(.5);el('zoomOut').onclick=()=>zoom(2);el('prev').onclick=()=>{start-=count*.7;draw();};el('next').onclick=()=>{start+=count*.7;draw();};el('scroll').oninput=()=>{start=+el('scroll').value;draw();};el('links').onchange=draw;
el('apply').onclick=()=>{let a=D.t.findIndex(t=>t.slice(0,10)>=el('from').value),b=D.t.findIndex(t=>t.slice(0,10)>el('to').value);if(a<0)return;if(b<0)b=N;if(b<=a)return;start=a;count=b-a;draw();};
cv.addEventListener('wheel',e=>{e.preventDefault();let r=cv.getBoundingClientRect();zoom(e.deltaY>0?1.3:1/1.3,Math.max(0,Math.min(1,(e.clientX-r.left-75)/(W-100))));},{passive:false});
cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,start};cv.setPointerCapture(e.pointerId);});cv.addEventListener('pointerup',()=>{drag=null;});
cv.addEventListener('pointermove',e=>{let r=cv.getBoundingClientRect();if(drag){start=drag.start-(e.clientX-drag.x)*count/(W-100);draw();return;}hover=Math.max(start,Math.min(start+count-1,Math.floor(start+(e.clientX-r.left-75)*count/(W-100))));let i=hover;el('info').textContent=D.t[i]+'　开 '+D.o[i].toFixed(2)+'　高 '+D.h[i].toFixed(2)+'　低 '+D.l[i].toFixed(2)+'　收 '+D.c[i].toFixed(2)+'　已知低通 '+D.lp[i].toFixed(2)+(D.e[i]?'　'+(D.e[i]>0?'买入／反多':'卖出／反空')+'，信号收盘 '+D.s[i]:'');draw();});
el('download').onclick=()=>{let a=document.createElement('a');a.download='STAR50_0.5day_current_view.png';a.href=cv.toDataURL('image/png');a.click();};window.addEventListener('resize',resize);resize();
</script></html>'''


def main():
    OUT.mkdir(exist_ok=True)
    frame=load_bars(ROOT/'artifacts/drawdown_material','5m_offset_0')
    x=np.log(frame.close.to_numpy());low=butter_lowpass(x,24,1)
    signal=np.nan_to_num(np.sign(np.r_[np.nan,np.diff(low)]))
    filled=np.r_[0,signal[:-1]]; delta=np.diff(np.r_[0,filled])
    executable,pnl=execute_next_open(signal,frame.open.to_numpy())
    dev=frame.year.to_numpy()>=2021;v=np.exp(pnl[dev].cumsum());dd=1-v/np.maximum.accumulate(np.r_[1.,v])[1:]
    trough=int(dd.argmax());peak=int(v[:trough+1].argmax());df=frame.loc[dev].reset_index(drop=True)
    assert abs(dd[trough]-.21045736566006967)<1e-10
    assert str(df.timestamp.iloc[peak]).startswith('2025-04-07') and str(df.timestamp.iloc[trough]).startswith('2025-09-26')
    known=np.r_[np.nan,np.exp(low[:-1]+x[0])]
    keep=frame.trading_day.between('2025-04-01','2025-09-30').to_numpy();ix=np.flatnonzero(keep)
    f=frame.loc[keep].copy().reset_index(drop=True)
    for c in ['open','high','low','close']:f[c]=pd.to_numeric(f[c])
    f['bar_open_time']=f.timestamp-pd.Timedelta(minutes=5)
    f['lowpass_known_at_open']=known[keep]
    f['event']=np.sign(delta[keep]).astype(int)
    f['signal_close_time']=[str(frame.timestamp.iloc[i-1]) if delta[i] else '' for i in ix]
    assert np.isfinite(f.lowpass_known_at_open).all()
    assert all(frame.timestamp.iloc[i-1]<=f.bar_open_time.iloc[k] for k,i in enumerate(ix) if delta[i])
    f[['timestamp','bar_open_time','open','high','low','close','lowpass_known_at_open','event','signal_close_time']].to_csv(OUT/'chart_data.csv',index=False)
    data={'t':f.bar_open_time.astype(str).tolist(),'o':f.open.tolist(),'h':f.high.tolist(),'l':f.low.tolist(),'c':f.close.tolist(),'lp':f.lowpass_known_at_open.tolist(),'e':f.event.tolist(),'s':f.signal_close_time.tolist()}
    (OUT/'chart.html').write_text(HTML.replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':'))))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection,PolyCollection
    from matplotlib.patches import ConnectionPatch
    from matplotlib.font_manager import FontProperties
    font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    fig,axes=plt.subplots(2,1,figsize=(50,8),sharex=True,gridspec_kw={'hspace':.15})
    points=np.arange(len(f));colors=np.where(f.close>=f.open,'#c94855','#258e79')
    axes[0].add_collection(LineCollection([[(i,l),(i,h)] for i,l,h in zip(points,f.low,f.high)],colors=colors,linewidths=.35))
    bodies=[[(i-.32,o),(i-.32,c),(i+.32,c),(i+.32,o)] for i,o,c in zip(points,f.open,f.close)]
    axes[0].add_collection(PolyCollection(bodies,facecolors=colors,edgecolors=colors,linewidths=.3))
    axes[0].set_ylim(f.low.min()*.99,f.high.max()*1.01)
    axes[1].plot(points,f.lowpass_known_at_open,color='#243b63',lw=.8)
    for sign,color,label,marker in [(1,'#d93e50','买入／反多','^'),(-1,'#2563d9','卖出／反空','v')]:
        selected=np.flatnonzero(f.event.to_numpy()==sign)
        axes[1].scatter(selected,f.lowpass_known_at_open.iloc[selected],c=color,marker=marker,s=10,label=label,zorder=4)
        for i in selected:
            fig.add_artist(ConnectionPatch((i,f.lowpass_known_at_open.iloc[i]),(i,f.open.iloc[i]),
                coordsA='data',coordsB='data',axesA=axes[1],axesB=axes[0],color=color,
                ls=(0,(3,4)),lw=.35,alpha=.18,zorder=1))
    axes[0].set_title('上层：科创50原始5分钟K线｜2025年4月至9月',fontproperties=font,fontsize=16)
    axes[1].set_title('下层：0.5交易日低通（24根、一阶、斜率反手）｜买卖点使用下一开盘时已知低通值',fontproperties=font,fontsize=14)
    axes[1].legend(prop=font,loc='upper left')
    ticks=np.flatnonzero(f.trading_day.ne(f.trading_day.shift()).to_numpy())[::5]
    axes[1].set_xticks(ticks,f.trading_day.iloc[ticks],rotation=45,ha='right',fontsize=8)
    for ax in axes:ax.grid(alpha=.18);ax.set_xlim(-1,len(f));ax.set_ylabel('Index points')
    fig.suptitle('STAR50 · 0.5 trading day LP · 2025 Apr–Sep · Buy RED / Sell BLUE',fontsize=18)
    fig.subplots_adjust(left=.035,right=.995,bottom=.14,top=.90)
    fig.savefig(OUT/'chart.png',dpi=240)
    fig.savefig(OUT/'chart.svg')
    fig.set_size_inches(16,8);fig.savefig(OUT/'preview.png',dpi=135)
    plt.close(fig)
    receipt={'purpose':'user_requested_chart_only','period_days':.5,'period_bars':24,'order':1,'signal_rule':'slope_sign_no_hysteresis',
        'execution':'next_tradable_open; lower curve is prior-close LP known at that open',
        'mdd_reconstructed':float(dd[trough]),'peak_source_end_label':str(df.timestamp.iloc[peak]),'trough_source_end_label':str(df.timestamp.iloc[trough]),
        'visible_bars':len(f),'buy_points':int((f.event>0).sum()),'sell_points':int((f.event<0).sum()),
        'data_2026_used':False,'not_the_LP12_volatility_gate_version':True,
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False,indent=2));print(OUT/'chart.html')


if __name__=='__main__':main()
