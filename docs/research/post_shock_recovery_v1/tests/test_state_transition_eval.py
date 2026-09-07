import pathlib,sys
import numpy as np
import pandas as pd

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1] / "code"))
from state_transition_eval import *


def panel():
    rows=[]
    for sym in ['A','B']:
        for sess in ['d/0','d/1']:
            for m in range(1,121):
                r=1.0
                first=0.0
                sigma=10.0
                if m==40:
                    r=50.0; first=1.0
                if 41<=m<=50: r=20.0
                if 51<=m<=70: r=5.0
                rows.append({'symbol':sym,'session':sess,'minute':m,'return_bp':r,'first':first,'sigma_pre':sigma})
    return pd.DataFrame(rows)


def test_state_boundaries():
    assert state_band(.9)=='Recovering-low'
    assert state_band(1.0)=='Recovering-high'
    assert state_band(1.5)=='Unsafe'


def test_builds_only_frozen_checkpoints():
    cp=build_checkpoints(panel())
    assert set(cp.checkpoint)=={5,10,15,20}
    assert cp.key.nunique()==4


def test_causal_future_mutation_does_not_change_earlier_checkpoint_current_ratio():
    p=panel(); a=build_checkpoints(p)
    v=a[(a.key=='A|d/0|40') & (a.checkpoint==5)].current_ratio.iloc[0]
    p.loc[(p.symbol=='A')&(p.session=='d/0')&(p.minute>=46),'return_bp']=999
    b=build_checkpoints(p)
    w=b[(b.key=='A|d/0|40') & (b.checkpoint==5)].current_ratio.iloc[0]
    assert v==w


def test_transition_matrix_and_metrics():
    cp=build_checkpoints(panel())
    c,p=transition_matrix(cp)
    assert c.values.sum()==len(cp)
    m=continuous_metrics(cp)
    assert m['n']==len(cp)
    assert np.isfinite(m['log_rmse'])


def test_bootstrap_resamples_event_keys():
    cp=build_checkpoints(panel())
    b=cluster_bootstrap_unsafe_minus_low(cp,repeats=100)
    assert b['repeats']>0
    assert len(b['ci95'])==2


def test_missing_future_is_unknown_not_zero():
    p=panel()
    p.loc[(p.symbol=='A')&(p.session=='d/0')&(p.minute==46),'return_bp']=np.nan
    cp=build_checkpoints(p)
    assert not ((cp.key=='A|d/0|40') & (cp.checkpoint==5)).any()
