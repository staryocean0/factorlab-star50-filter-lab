#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, os, sys
from pathlib import Path
import numpy as np
import pandas as pd

SYMBOLS=("000688.SH","000852.SH")
YEARS=(2022,2023,2024,2025)
VAL_YEARS=(2024,2025)
M3_ORDER=["<=0","(0,1]","(1,2]",">2"]


def load_parent(root: Path):
    path=root/'docs/research/fine_activity_future_risk_v1/run_study.py'
    spec=importlib.util.spec_from_file_location('parent_v1',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def build_fine_years(root: Path, panel: pd.DataFrame, symbol: str, p) -> pd.DataFrame:
    sys.path.insert(0,str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    rows=[]
    for year in YEARS:
        sec=load_market_data(symbol,'3s',f'{year}-01-01',f'{year}-12-31',root=root)
        ts=sec.market_time_shanghai.dt.tz_localize(None)
        s=sec[['trading_day','row_index','price']].copy()
        s['second_day']=(ts.dt.hour*3600+ts.dt.minute*60+ts.dt.second).to_numpy()
        s['afternoon']=(s.second_day>=13*3600).astype(int)
        s['session']=s.trading_day.astype(str)+'/'+s.afternoon.astype(str)
        s['second']=s.second_day-np.where(s.afternoon==1,13*3600,9*3600+30*60)
        s=s[s.second.between(0,7200)].copy()
        groups={k:z for k,z in s.groupby('session',sort=False)}
        pyear=panel[pd.to_datetime(panel.day).dt.year==year]
        for session,part in pyear.groupby('session',sort=False):
            raw=groups.get(session)
            sample=p.sample_session([],[],[]) if raw is None else p.sample_session(raw.second.to_numpy(float),raw.price.to_numpy(float),raw.row_index.to_numpy())
            price=sample['price']; r15=sample['return_bp']; part=part.sort_values('minute')
            coarse=part.return_bp.to_numpy(float); elig=part.eligible.to_numpy(bool)
            for minute in range(1,121):
                item={'symbol':symbol,'session':session,'day':str(part.day.iloc[0]),'afternoon':int(part.afternoon.iloc[0]),'minute':minute,'fine_complete5':False,'pre5m_range_bp':np.nan,'A5':np.nan,'M1':np.nan,'rms1m5':np.nan}
                if minute>=5:
                    j=minute*4; fine=r15[j-19:j+1]; px=price[j-20:j+1]; c=coarse[minute-5:minute]; e=elig[minute-5:minute]
                    complete=(len(fine)==20 and len(px)==21 and np.isfinite(fine).all() and np.isfinite(px).all() and (px>0).all() and len(c)==5 and np.isfinite(c).all() and bool(e.all()))
                    item['fine_complete5']=bool(complete)
                    if complete:
                        rel=np.log(px/px[0])*1e4
                        item['pre5m_range_bp']=float(rel.max()-rel.min())
                        item['A5']=float(np.sqrt(np.mean(fine*fine)))
                        rvf=float(np.sum(fine*fine)); rvc=float(np.sum(c*c))
                        item['M1']=float(np.log((rvf+p.EPS)/(rvc+p.EPS)))
                        item['rms1m5']=float(np.sqrt(np.mean(c*c)))
                rows.append(item)
        del sec,s,groups
    return pd.DataFrame(rows)


def prepare(root: Path,p):
    sys.path.insert(0,str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    panels=[]; fines=[]
    for symbol in SYMBOLS:
        native=load_market_data(symbol,'1m','2022-05-16','2025-12-31',root=root)
        panel=p.minute_panel(native,symbol)
        panels.append(panel); fines.append(build_fine_years(root,panel,symbol,p))
    panel=pd.concat(panels,ignore_index=True); fine=pd.concat(fines,ignore_index=True)
    target=p.attach_future_targets(panel)
    keys=['symbol','session','day','afternoon','minute']
    frame=target.merge(fine,on=keys,how='inner',validate='one_to_one')
    frame=p.attach_clock_z(frame,'A5','M3')
    day=pd.to_datetime(frame.day); year=day.dt.year
    eligible=(year.isin(VAL_YEARS)&frame.fine_complete5&(frame.pre5m_range_bp<p.RANGE_BP)&frame.minute.between(35,105)&np.isfinite(frame.M3)&np.isfinite(frame.current_vol_ratio)&np.isfinite(frame.future_rms15_bp)&np.isfinite(frame.future_mean_abs15_bp)&np.isfinite(frame.future_any_unsafe15))
    q=frame.loc[eligible].copy(); q['year']=pd.to_datetime(q.day).dt.year
    q['current_state']=np.where(q.current_vol_ratio>=1.5,'Unsafe','NonUnsafe'); q['m3_band']=q.M3.map(p.band_label)
    return q


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[3]); ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); root=a.repo_root.resolve(); out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False); p=load_parent(root); q=prepare(root,p)
    rows=[]
    for symbol in SYMBOLS:
      for year in VAL_YEARS:
       for state in ('NonUnsafe','Unsafe'):
        s=q[(q.symbol==symbol)&(q.year==year)&(q.current_state==state)]
        for band in M3_ORDER:
         z=s[s.m3_band==band]
         rows.append({'symbol':symbol,'year':year,'current_state':state,'m3_band':band,'n':int(len(z)),'median_future_rms15_bp':float(z.future_rms15_bp.median()) if len(z) else None,'mean_future_rms15_bp':float(z.future_rms15_bp.mean()) if len(z) else None,'mean_future_abs15_bp':float(z.future_mean_abs15_bp.mean()) if len(z) else None,'future_any_unsafe15_prob':float(z.future_any_unsafe15.mean()) if len(z) else None,'median_current_vol_ratio':float(z.current_vol_ratio.median()) if len(z) else None})
    cube=pd.DataFrame(rows)
    pooled=q.groupby(['symbol','year','current_state']).agg(n=('M3','size'),median_future_rms15_bp=('future_rms15_bp','median'),future_any_unsafe15_prob=('future_any_unsafe15','mean'),median_current_vol_ratio=('current_vol_ratio','median')).reset_index()
    checks={}
    all_pass=True
    for symbol in SYMBOLS:
      checks[symbol]={}
      for year in VAL_YEARS:
        amp={}
        for state in ('NonUnsafe','Unsafe'):
          s=cube[(cube.symbol==symbol)&(cube.year==year)&(cube.current_state==state)].set_index('m3_band').loc[M3_ORDER]
          bot=s.loc['<=0']; top=s.loc['>2']
          vals={'bottom_n_ge_100':bool(bot.n>=100),'top_n_ge_30':bool(top.n>=30),'top_bottom_rms_ratio_ge_1_10':bool(top.median_future_rms15_bp/bot.median_future_rms15_bp>=1.10) if bot.median_future_rms15_bp and pd.notna(top.median_future_rms15_bp) else False}
          amp[state]=vals
        amp_pass=all(all(v.values()) for v in amp.values())
        st=pooled[(pooled.symbol==symbol)&(pooled.year==year)].set_index('current_state')
        delta=float(st.loc['Unsafe','future_any_unsafe15_prob']-st.loc['NonUnsafe','future_any_unsafe15_prob']) if set(st.index)=={'NonUnsafe','Unsafe'} else float('nan')
        pers={'both_state_n_ge_500':bool(len(st)==2 and (st.n>=500).all()),'unsafe_minus_nonunsafe_ge_30pp':bool(np.isfinite(delta) and delta>=0.30),'unsafe_minus_nonunsafe_pp':delta*100 if np.isfinite(delta) else None}
        pers_pass=bool(pers['both_state_n_ge_500'] and pers['unsafe_minus_nonunsafe_ge_30pp'])
        cell_pass=bool(amp_pass and pers_pass); all_pass=all_pass and cell_pass
        checks[symbol][str(year)]={'amplitude_axis':amp,'amplitude_axis_present':amp_pass,'state_persistence_axis':pers,'state_persistence_axis_present':pers_pass,'pass':cell_pass}
    verdict='validation_diagnostic_replicates_two_axis_structure' if all_pass else 'validation_diagnostic_does_not_fully_replicate'
    cube.to_csv(out/'validation_risk_coordinate_cube.csv',index=False); pooled.to_csv(out/'validation_pooled_state_summary.csv',index=False)
    summary={'schema':'risk_coordinate_validation_v1','validation_years':[2024,2025],'validation_rows':int(len(q)),'verdict':verdict,'checks':checks,'validation_queried':True,'read_2026':False,'blackbox_queried':False,'fresh_oos':False,'returns_or_pnl_evaluated':False,'candidate_nominated':False,'production_authority':False,'git_sha':os.getenv('GITHUB_SHA'),'run_id':os.getenv('GITHUB_RUN_ID')}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2)); print(cube.to_string(index=False)); print(pooled.to_string(index=False))

if __name__=='__main__': main()
