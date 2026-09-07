from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from state_sufficiency import build_panel, state_band, SYMBOLS

CHECKPOINTS=(5,10,15)
SEED=20260907


def build_burden(panel: pd.DataFrame, year:int) -> pd.DataFrame:
    rows=[]
    for (symbol,session),z0 in panel.groupby(['symbol','session'],sort=False):
        z=z0.sort_values('minute').reset_index(drop=True)
        r=z.return_bp.to_numpy(float); first=z['first'].to_numpy(float); mins=z.minute.to_numpy(int)
        for j in np.flatnonzero(first==1):
            if mins[j]<33: continue
            sig=float(z.loc[j,'sigma_pre'])
            if not(np.isfinite(sig) and sig>0): continue
            key=f'{symbol}|{session}|{mins[j]}'
            for cp in CHECKPOINTS:
                curw=r[j+cp-4:j+cp+1]
                if len(curw)!=5 or not np.isfinite(curw).all(): continue
                cur=float(np.sqrt(np.mean(curw*curw))/sig)
                fut=[]
                for h in (1,2,3):
                    a=j+cp+1+(h-1)*5; b=a+5
                    w=r[a:b]
                    if len(w)!=5 or not np.isfinite(w).all():
                        fut=[]; break
                    fut.append(float(np.sqrt(np.mean(w*w))/sig))
                if len(fut)!=3: continue
                unsafe=np.asarray(fut)>=1.5
                rows.append({'key':key,'symbol':symbol,'year':year,'checkpoint':cp,
                    'current_ratio':cur,'current_state':state_band(cur),
                    'next5_ratio':fut[0],'next10_ratio':fut[1],'next15_ratio':fut[2],
                    'unsafe_blocks_15m':int(unsafe.sum()),'unsafe_share_15m':float(unsafe.mean()),
                    'any_unsafe_15m':int(unsafe.any()),'max_ratio_15m':float(max(fut)),
                    'mean_ratio_15m':float(np.mean(fut))})
    return pd.DataFrame(rows)


def bootstrap_event_diff(df, outcome, high='Unsafe', low='Recovering-low', repeats=10000):
    z=df[df.current_state.isin([high,low])]
    keys=z.key.unique(); ki={k:i for i,k in enumerate(keys)}
    arr=np.zeros((len(keys),2,2),float); si={high:0,low:1}
    for row in z.itertuples(index=False):
        i=ki[row.key]; s=si[row.current_state]; arr[i,s,0]+=float(getattr(row,outcome)); arr[i,s,1]+=1
    rng=np.random.default_rng(SEED); vals=[]
    for _ in range(repeats):
        idx=rng.integers(0,len(keys),size=len(keys)); a=arr[idx].sum(axis=0)
        if a[0,1] and a[1,1]: vals.append(a[0,0]/a[0,1]-a[1,0]/a[1,1])
    if not vals:return {'events':len(keys),'ci95':[None,None],'median':None}
    q=np.quantile(vals,[.025,.5,.975])
    return {'events':len(keys),'median':float(q[1]),'ci95':[float(q[0]),float(q[2])]}


def summarize(df):
    out={'rows':len(df),'events':int(df.key.nunique()),'bands':{},'bootstrap':{}}
    for st,z in df.groupby('current_state'):
        out['bands'][st]={'n':len(z),'events':int(z.key.nunique()),
            'any_unsafe_15m':float(z.any_unsafe_15m.mean()),
            'mean_unsafe_blocks_15m':float(z.unsafe_blocks_15m.mean()),
            'mean_ratio_15m':float(z.mean_ratio_15m.mean()),
            'median_max_ratio_15m':float(z.max_ratio_15m.median())}
    out['bootstrap']['unsafe_minus_low_any15']=bootstrap_event_diff(df,'any_unsafe_15m')
    out['bootstrap']['unsafe_minus_low_burden']=bootstrap_event_diff(df,'unsafe_share_15m')
    return out


def load_year(root,symbol,year):
    p=(root/f'data/cross_index_risk_gate_v1/1m/{symbol}/{year}.parquet') if year<=2025 else (root/f'data/cross_index_risk_gate_2026_v1/1m/{symbol}/2026.parquet')
    return pd.read_parquet(p)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo-root',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args();root=Path(a.repo_root);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    allrows=[];res={}
    for year in (2024,2025,2026):
        ys=[]
        for symbol in SYMBOLS:
            p=build_panel(load_year(root,symbol,year),symbol); z=build_burden(p,year); ys.append(z); res[f'{symbol}_{year}']=summarize(z)
        y=pd.concat(ys,ignore_index=True); allrows.append(y);res[f'pooled_{year}']=summarize(y)
    pd.concat(allrows,ignore_index=True).to_csv(out/'risk_burden_checkpoints.csv',index=False)
    res['guardrails']=['fixed 5m state score and 1.0/1.5 display bands','future horizon is three fixed non-overlapping 5m blocks','descriptive consumed-history only','no Clean promotion']
    (out/'risk_burden_summary.json').write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(res,ensure_ascii=False))
if __name__=='__main__':main()
