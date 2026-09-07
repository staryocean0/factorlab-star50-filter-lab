import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from direction_stability import checkpoints, summarize


def test_direction_is_event_sign():
    r=np.ones(120);r[39]=-40;first=np.zeros(120);first[39]=1;sig=np.repeat(5.,120)
    p=pd.DataFrame({'symbol':'x','session':'d/0','day':'d','minute':np.arange(1,121),'return_bp':r,'sigma_pre':sig,'first':first})
    z=checkpoints(p,2024);assert (z.direction==-1).all()


def test_summarize():
    rows=[]
    for y in [2024,2025,2026]:
      for e in range(30):
       d=1 if e%2 else -1
       for cp in [5,10,15,20]:
        ratio=.8+.1*(e%7);yy=int(ratio>1.1);lr=np.log(ratio);rows.append({'key':f'{y}-{e}','year':y,'direction':d,'current_ratio':ratio,'current_state':'Unsafe' if ratio>=1.5 else ('Recovering-high' if ratio>=1 else 'Recovering-low'),'log_ratio':lr,'ratio_x_direction':lr*d,'next_unsafe':yy})
    x=pd.DataFrame(rows);r=summarize(x[x.year==2024],x[x.year==2025],x[x.year==2026]);assert 'bootstrap' in r['evaluation']['2025']
