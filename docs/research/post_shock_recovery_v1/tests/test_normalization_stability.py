import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from normalization_stability import checkpoints, summarize


def test_checkpoint_uses_fixed_sigma():
    r=np.ones(120);first=np.zeros(120);first[39]=1;sig=np.repeat(5.,120)
    p=pd.DataFrame({'symbol':'x','session':'d/0','day':'d','minute':np.arange(1,121),'return_bp':r,'sigma_pre':sig,'first':first})
    z=checkpoints(p,2024);assert (z.sigma_pre==5).all()


def test_summarize_models():
    rows=[]
    for y in [2024,2025,2026]:
      for e in range(30):
       for cp in [5,10,15,20]:
        sig=3+(e%5);ratio=.8+.1*(e%7);yy=int(ratio>1.1)
        lr=np.log(ratio);ls=np.log(sig);rows.append({'key':f'{y}-{e}','year':y,'checkpoint':cp,'sigma_pre':sig,'log_sigma':ls,'current_ratio':ratio,'current_state':'Unsafe' if ratio>=1.5 else ('Recovering-high' if ratio>=1 else 'Recovering-low'),'log_ratio':lr,'ratio_x_sigma':lr*ls,'next_unsafe':yy})
    x=pd.DataFrame(rows);r=summarize(x[x.year==2024],x[x.year==2025],x[x.year==2026]);assert 'bootstrap' in r['evaluation']['2025']
