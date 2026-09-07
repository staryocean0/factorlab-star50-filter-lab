import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from state_sufficiency import build_panel, build_checkpoints, state_band, summarize


def native_one(day='2024-01-02'):
    ts=pd.date_range(day+' 09:30:00',periods=120,freq='1min')
    p=100*np.exp(np.cumsum(np.r_[0,np.repeat(.0001,119)]))
    return pd.DataFrame({'symbol':'000688.SH','timestamp':ts.astype(str),'trading_day':day,'close':p,
        'causal_flat_fill':False,'high_frequency_analysis_eligible':True})


def test_state_band():
    assert state_band(.9)=='Recovering-low' and state_band(1.2)=='Recovering-high' and state_band(1.5)=='Unsafe'


def test_panel_no_cross_session():
    x=native_one(); p=build_panel(x,'000688.SH'); assert len(p)==240
    pm=p[p.session.str.endswith('/1')]; assert pm.return_bp.isna().all()


def test_checkpoint_history_is_causal():
    r=np.zeros(120); sig=np.repeat(5.,120); first=np.zeros(120); first[39]=1
    r[40:45]=10; r[45:50]=2; r[50:55]=2
    panel=pd.DataFrame({'symbol':'000688.SH','session':'d/0','day':'d','minute':np.arange(1,121),'return_bp':r,'sigma_pre':sig,'first':first})
    a=build_checkpoints(panel,2024)
    x=a[a.checkpoint==10].iloc[0]
    assert x.recover_age>0
    panel2=panel.copy(); panel2.loc[60:,'return_bp']=99
    b=build_checkpoints(panel2,2024)
    y=b[b.checkpoint==10].iloc[0]
    assert x.current_ratio==y.current_ratio and x.recover_age==y.recover_age


def test_summarize_models():
    rows=[]
    for year in [2024,2025,2026]:
      for e in range(30):
       for cp in [5,10,15,20]:
        ratio=.7+0.05*(e%10)+.03*(cp/5)
        y=int(ratio>1.05)
        rows.append({'key':f'{year}-{e}','symbol':'x','year':year,'checkpoint':cp,'current_ratio':ratio,'next_ratio':1.6 if y else .8,'next_unsafe':y,
          'current_state':state_band(ratio),'log_ratio':np.log(ratio),'elapsed10':cp/10,'recover_age':cp,'recover_age10':cp/10})
    df=pd.DataFrame(rows)
    res,_=summarize(df[df.year==2024],df[df.year==2025],df[df.year==2026])
    assert '2025' in res['evaluation'] and 'bootstrap' in res['evaluation']['2025']
