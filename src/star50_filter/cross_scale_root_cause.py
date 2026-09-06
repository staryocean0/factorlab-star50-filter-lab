"""Fixed-strategy retrospective price attribution. No trading policy added.

Forward/backward components use future observations. They are deliberately kept
out of the original signal generator. Original sealed modules are imported only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import signal, stats

FEATURES = ['eff_1d','eff_5d','eff_20d','rv_1d','rv_5d','rv_20d',
            'rv_ratio_1_20','drift_disagree_1_20','acf1_5d','acf3_5d','acf12_5d',
            'fast_share_1d','fast_share_5d','fast_share_20d','work_turns_5d',
            'slow_work_velocity_5d','slow_work_opposition_5d','wick_1d',
            'gap_share_1d','threshold_work_amplitude_5d']
PERIODS = (12,48,240,960)


def divide(a, b):
    return a / np.maximum(b, 1e-15)


def components(x, causal=False):
    x = np.asarray(x, dtype=float)
    z = x - x[0]
    lps = {}
    for p in PERIODS:
        sos = signal.butter(1, 1 / p, fs=1, output='sos')
        # z[0] = 0, so zero steady-state initialization is exact.
        y = signal.sosfilt(sos, z) if causal else signal.sosfiltfilt(sos, z)
        lps[p] = y + x[0]
    bands = np.column_stack([x-lps[12],lps[12]-lps[48],lps[48]-lps[240],
                             lps[240]-lps[960],lps[960]])
    return lps, bands


def properties(frame, causal=False):
    """Trailing daily snapshots; causal=False has two-sided price components."""
    f = frame.reset_index(drop=True)
    counts = f.groupby('trading_day').size()
    if counts.nunique() != 1:
        raise ValueError('Native carrier day counts are not constant')
    nday = int(counts.iloc[0])
    x = np.log(f.close.to_numpy(float))
    o = np.log(f.open.to_numpy(float))
    r = pd.Series(x).diff()
    lps, b = components(x, causal)
    db = pd.DataFrame(b).diff()
    work = pd.Series(b[:,1])
    slowd = pd.Series(lps[240]).diff()
    wd = work.diff()
    a = pd.DataFrame(index=f.index)
    for h in (1,5,20):
        w = nday * h
        a[f'eff_{h}d'] = divide(r.rolling(w).sum().abs(),r.abs().rolling(w).sum())
        a[f'rv_{h}d'] = np.sqrt(r.pow(2).rolling(w).mean()) * 1e4
        a[f'fast_share_{h}d'] = divide(db[0].pow(2).rolling(w).sum(),db.pow(2).sum(axis=1).rolling(w).sum())
    a['rv_ratio_1_20'] = divide(a.rv_1d,a.rv_20d)
    a['drift_disagree_1_20'] = (np.sign(r.rolling(nday).sum()) != np.sign(r.rolling(20*nday).sum())).astype(float)
    for lag in (1,3,12):
        a[f'acf{lag}_5d'] = r.rolling(nday*5).corr(r.shift(lag))
    a['work_turns_5d'] = (np.sign(wd) != np.sign(wd.shift())).rolling(nday*5).sum() / 5
    a['slow_work_velocity_5d'] = np.sqrt(divide(slowd.pow(2).rolling(nday*5).mean(),wd.pow(2).rolling(nday*5).mean()))
    a['slow_work_opposition_5d'] = (slowd * wd < 0).rolling(nday*5).mean()
    high = np.log(pd.to_numeric(f.high).to_numpy())
    low = np.log(pd.to_numeric(f.low).to_numpy())
    wick = np.clip(divide(high-low-np.abs(x-o),high-low),0,1)
    a['wick_1d'] = pd.Series(wick).rolling(nday).mean()
    gap = pd.Series(o).sub(pd.Series(x).shift())
    body = pd.Series(x-o)
    a['gap_share_1d'] = divide(gap.pow(2).rolling(nday).sum(),(gap.pow(2)+body.pow(2)).rolling(nday).sum())
    a['threshold_work_amplitude_5d'] = divide(f.sigma.rolling(nday*5).mean(),work.rolling(nday*5).std(ddof=0))
    a['trading_day'] = f.trading_day
    daily = a.groupby('trading_day',sort=True).last()[FEATURES]
    return daily, lps, b, a


def native_properties(f):
    counts = f.groupby('trading_day').size()
    if counts.nunique() != 1:
        raise ValueError('Unequal daily counts')
    n = int(counts.iloc[0])
    r = np.log(f.close).diff()
    a = pd.DataFrame(index=f.index)
    for h in (1,5,20):
        a[f'eff_{h}d'] = divide(r.rolling(n*h).sum().abs(),r.abs().rolling(n*h).sum())
    hi, lo = np.log(pd.to_numeric(f.high)), np.log(pd.to_numeric(f.low))
    a['wick_1d'] = pd.Series(np.clip(divide(hi-lo-(np.log(f.close)-np.log(f.open)).abs(),hi-lo),0,1)).rolling(n).mean()
    a['trading_day'] = f.trading_day
    return a.groupby('trading_day').last(), n


def centered_ranks(x, years):
    x = np.asarray(x,float)
    if x.ndim == 1:
        x = x[:,None]
    out = np.zeros_like(x)
    for year in np.unique(years):
        ix = np.flatnonzero(years == year)
        rr = stats.rankdata(x[ix],axis=0)
        out[ix] = rr-rr.mean(axis=0)
    return out / np.maximum(np.sqrt((out**2).sum(axis=0)),1e-15)


def association(panel, features=FEATURES, permutations=1999, bootstrap=1000, seed=20260906):
    """Conditional year-stratified reference distributions, not iid tests."""
    cols = list(features)+['pnl_log','capture','year']
    d = panel[cols].dropna()
    years = d.year.to_numpy()
    xx, yy = centered_ranks(d[features].to_numpy(),years), centered_ranks(d[['pnl_log','capture']].to_numpy(),years)
    observed = xx.T @ yy
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(years == y) for y in np.unique(years)]
    nulls = {}
    for method in ('circular','block20'):
        values = np.empty((permutations,len(features),2))
        for k in range(permutations):
            order = np.arange(len(d))
            for ix in groups:
                if method == 'circular':
                    offset = rng.integers(20,len(ix)-19)
                    order[ix] = np.roll(ix,offset)
                else:
                    blocks = [ix[i:i+20] for i in range(0,len(ix),20)]
                    order[ix] = np.concatenate([blocks[j] for j in rng.permutation(len(blocks))])
            values[k] = xx[order].T @ yy
        nulls[method] = values
    cis = np.empty((bootstrap,len(features),2))
    for k in range(bootstrap):
        orders=[]
        for ix in groups:
            starts = rng.integers(0,len(ix),size=int(np.ceil(len(ix)/20)))
            orders.append(ix[np.concatenate([(s+np.arange(20)) % len(ix) for s in starts])[:len(ix)]])
        idx=np.concatenate(orders)
        cis[k]=centered_ranks(d[features].to_numpy()[idx],years[idx]).T @ centered_ranks(d[['pnl_log','capture']].to_numpy()[idx],years[idx])
    rows=[]
    for i,feature in enumerate(features):
        for j,outcome in enumerate(('pnl_log','capture')):
            row={'feature':feature,'outcome':outcome,'rho':float(observed[i,j]),'ci_low':float(np.quantile(cis[:,i,j],.025)),'ci_high':float(np.quantile(cis[:,i,j],.975)),'n_days':len(d)}
            for method,v in nulls.items():
                row[f'{method}_p']=(1+np.sum(np.abs(v[:,i,j])>=abs(observed[i,j])))/(permutations+1)
                row[f'{method}_maxT_p']=(1+np.sum(np.max(np.abs(v),axis=(1,2))>=abs(observed[i,j])))/(permutations+1)
            rows.append(row)
    return pd.DataFrame(rows)


def simple_associations(panel, group_columns):
    rows=[]
    for key,g in panel.groupby(group_columns):
        key=key if isinstance(key,tuple) else (key,)
        for f in FEATURES:
            for target in ('pnl_log','capture'):
                sub=g[[f,target]].dropna()
                rho=stats.spearmanr(sub[f],sub[target]).statistic if sub[f].nunique()>1 else np.nan
                rows.append(dict(zip(group_columns,key))|{'feature':f,'outcome':target,'rho':rho,'n_days':len(sub)})
    return pd.DataFrame(rows)


def cell_labels(panel, medians=None):
    pairs={'fast_slow':('fast_share_5d','slow_work_velocity_5d'),'short_long_eff':('eff_1d','eff_20d')}
    medians = medians or {f:float(panel[f].median()) for pair in pairs.values() for f in pair}
    p=panel.copy()
    for name,(a,b) in pairs.items():
        p[name]=(p[a]>medians[a]).astype(int).astype(str)+(p[b]>medians[b]).astype(int).astype(str)
    return p,medians


def cell_table(panel,group_cols=()):
    rows=[]
    for table in ('fast_slow','short_long_eff'):
        for key,g in panel.groupby(list(group_cols)+[table]):
            key=key if isinstance(key,tuple) else (key,)
            loss=g.pnl_log.clip(upper=0).sum()
            win=g.pnl_log.clip(lower=0).sum()
            rows.append(dict(zip(list(group_cols)+['cell'],key))|{'table':table,'days':len(g),'losing_days':int((g.pnl_log<0).sum()),'winning_days':int((g.pnl_log>0).sum()),'mean_pnl_bp':g.pnl_log.mean()*1e4,'median_pnl_bp':g.pnl_log.median()*1e4,'mean_capture':g.capture.mean(),'loss_log':loss,'positive_log':win,'net_log':g.pnl_log.sum()})
    return pd.DataFrame(rows)


def trade_fragments(frame):
    """Exact marked-interval ledger. MFE is from open marks, not intrabar highs."""
    rows=[]
    p=frame.exec_pos.to_numpy()
    splits=np.r_[0,np.flatnonzero(p[1:]!=p[:-1])+1,len(p)]
    for k,(a,b) in enumerate(zip(splits[:-1],splits[1:])):
        q=frame.iloc[a:b]
        path=np.r_[0,np.cumsum(q.pnl_log)]
        net=float(path[-1]); mfe=float(path.max()); mae=float(path.min())
        rows.append({'trade':k,'first_interval_index':a,'last_interval_index':b-1,'first_booking':str(q.timestamp.iloc[0]),'last_booking':str(q.timestamp.iloc[-1]),'direction':p[a],'bars':b-a,'pnl_log':net,'mfe_log':mfe,'mae_log':mae,'giveback_log':mfe-net,'losing_never_favorable':bool(net<0 and mfe<=1e-12),'losing_after_favorable':bool(net<0 and mfe>1e-12),'boundary_clipped':a==0 or b==len(p)})
    return pd.DataFrame(rows)
