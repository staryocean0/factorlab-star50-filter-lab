import numpy as np
import pandas as pd
from star50_filter.cross_scale_root_cause import components,trade_fragments,association,FEATURES


def test_future_component_is_explicit_and_causal_companion_prefix_invariant():
    x=np.sin(np.arange(5000)/17)*.01+np.arange(5000)*1e-5
    l,b=components(x)
    assert np.allclose(b.sum(axis=1),x,atol=1e-14)
    changed=x.copy();changed[2500:]+=0.1
    lc,_=components(x,causal=True);ld,_=components(changed,causal=True)
    for p in lc:assert np.array_equal(lc[p][:2500],ld[p][:2500])
    future,_=components(changed)
    assert np.max(np.abs(l[960][2300:2500]-future[960][2300:2500]))>.01


def test_trade_fragment_mfe_and_account_partition():
    f=pd.DataFrame({'exec_pos':[1,1,1,-1,-1],'pnl_log':[.02,.03,-.07,-.02,.01],
        'timestamp':pd.date_range('2021-01-01',periods=5,freq='5min')})
    t=trade_fragments(f)
    assert len(t)==2
    assert np.isclose(t.pnl_log.sum(),f.pnl_log.sum())
    assert np.isclose(t.iloc[0].mfe_log,.05)
    assert np.isclose(t.iloc[0].giveback_log,.07)
    assert t.iloc[0].losing_after_favorable
    assert t.iloc[1].losing_never_favorable


def test_multiple_testing_reference_detects_injected_synchronous_relation():
    rng=np.random.default_rng(731)
    n=240
    p=pd.DataFrame(rng.normal(size=(n,20)),columns=FEATURES)
    p['pnl_log']=p[FEATURES[0]]
    p['capture']=-p[FEATURES[0]]
    p['year']=np.repeat([2021,2022],120)
    r=association(p,permutations=49,bootstrap=20)
    selected=r.loc[r.feature==FEATURES[0]]
    assert np.allclose(selected.rho.abs(),1)
    assert (selected.circular_maxT_p==.02).all()
    assert (r.circular_maxT_p>=r.circular_p).all()
    assert (r.block20_maxT_p>=r.block20_p).all()
