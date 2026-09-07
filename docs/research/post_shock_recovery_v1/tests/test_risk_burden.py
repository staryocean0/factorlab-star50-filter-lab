import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from risk_burden import build_burden, summarize


def test_fixed_three_blocks_and_state():
    r=np.zeros(120); sig=np.repeat(5.,120); first=np.zeros(120); first[39]=1
    r[40:45]=10
    r[45:50]=2; r[50:55]=10; r[55:60]=2
    p=pd.DataFrame({'symbol':'x','session':'d/0','day':'d','minute':np.arange(1,121),'return_bp':r,'sigma_pre':sig,'first':first})
    z=build_burden(p,2024);x=z[z.checkpoint==5].iloc[0]
    assert x.current_state=='Unsafe' and x.unsafe_blocks_15m==1 and x.any_unsafe_15m==1


def test_future_mutation_does_not_change_current():
    r=np.ones(120);sig=np.repeat(5.,120);first=np.zeros(120);first[39]=1
    p=pd.DataFrame({'symbol':'x','session':'d/0','day':'d','minute':np.arange(1,121),'return_bp':r,'sigma_pre':sig,'first':first})
    a=build_burden(p,2024);v=a[a.checkpoint==5].current_ratio.iloc[0]
    p2=p.copy();p2.loc[50:,'return_bp']=20
    b=build_burden(p2,2024);w=b[b.checkpoint==5].current_ratio.iloc[0]
    assert v==w


def test_summary_has_bands():
    r=[]
    for e in range(10):
      for st,cur in [('Recovering-low',.8),('Unsafe',2.0)]:
       r.append({'key':f'{e}-{st}','current_state':st,'any_unsafe_15m':int(st=='Unsafe'),'unsafe_share_15m':1.0 if st=='Unsafe' else 0.0,'unsafe_blocks_15m':3 if st=='Unsafe' else 0,'mean_ratio_15m':cur,'max_ratio_15m':cur})
    s=summarize(pd.DataFrame(r));assert s['bands']['Unsafe']['any_unsafe_15m']==1
