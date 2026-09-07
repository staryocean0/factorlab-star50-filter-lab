"""Bounded first-shock V2. Native snapshot measurement is NOT a traded event flow.

Imports sealed V1 feature/event definitions; writes only new evidence. All model
inputs are trailing; path-ledger controls are hindsight descriptive, never fit rows.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'first_shock_gate_v1/code'))
import first_shock_gate as g

SEED = 20260907
SYMBOLS = ('000688.SH', '000852.SH')
BASE = g.BASE
FINE = ['fine_log_rv5', 'fine_log_rv15', 'fine_log_max1', 'fine_abs_net5',
        'fine_gap3_fraction5', 'fine_max_age5', 'fine_repeat_fraction5']
SCALE = ['fine_log_e30', 'fine_log_e60', 'fine_log_e120', 'fine_log_e240']


def write_json(path, obj):
    g.write_json(Path(path), obj)


def rolling_max(a, n):
    return pd.Series(np.asarray(a, float)).rolling(n, min_periods=n).max().to_numpy()


def sample_session(times, prices, rows, step=15, gap_limit=15):
    """Seconds since ONE session open. Last source row wins ties explicitly.

    Endpoints must be <=3s old. Never interpolate a price. gap_limit=15 defines
    a 15s endpoint-return measurement, NOT a claim of uninterrupted 3s history.
    gap_limit=3 is the separately registered complete-path sensitivity.
    """
    t = np.asarray(times, float); p = np.asarray(prices, float); r = np.asarray(rows)
    if len(t) != len(p) or len(t) != len(r): raise ValueError('shape mismatch')
    if step not in (15, 30, 60) or gap_limit not in (3, 15): raise ValueError('unregistered grid')
    if len(t) and (not np.isfinite(t).all() or np.any(t < 0) or np.any(t > 7200)):
        raise ValueError('outside session')
    if len(t) and (np.any(p <= 0) or not np.isfinite(p).all()): raise ValueError('bad price')
    if len(t):
        order = np.lexsort((r, t)); t, p, r = t[order], p[order], r[order]
        if np.any((np.diff(t) == 0) & (np.diff(r) == 0)): raise ValueError('duplicate composite key')
    grid = np.arange(0, 7201, step)
    pos = np.searchsorted(t, grid, side='right') - 1
    value = np.full(len(grid), np.nan); age = np.full(len(grid), np.nan)
    chosen = np.full(len(grid), -1, dtype=np.int64)
    returns = np.full(len(grid), np.nan); crossed3 = np.full(len(grid), np.nan)
    known = pos >= 0
    if known.any():
        age[known] = grid[known] - t[pos[known]]
        good = known & (age <= 3)
        value[good] = p[pos[good]]; chosen[good] = r[pos[good]]
        # Prefix counts refer to gaps ending at each source row. Same-second
        # changes are retained in source, but not assigned a positive duration.
        c3 = np.r_[0, np.cumsum(np.diff(t) > 3)]
        cb = np.r_[0, np.cumsum(np.diff(t) > gap_limit)]
        for j in range(1, len(grid)):
            if np.isfinite(value[j-1:j+1]).all():
                a, b = pos[j-1], pos[j]
                crossed3[j] = float(c3[b] > c3[a])
                if cb[b] == cb[a]: returns[j] = np.log(value[j]/value[j-1])*1e4
    return {'second': grid, 'price': value, 'age': age, 'row_index': chosen,
            'return_bp': returns, 'crossed_gap3': crossed3}


def fine_features(sample):
    """Fixed physical lookbacks. Return values at minute boundaries, 1..120."""
    r = sample['return_bp']; step = int(sample['second'][1]); n5 = 300 // step; n15 = 900 // step
    rv5 = g.roll_mean(r*r, n5); rv15 = g.roll_mean(r*r, n15)
    ret_known = np.isfinite(r)
    repeat = np.where(ret_known, (r == 0).astype(float), np.nan)
    net = np.full(len(r), np.nan)
    if len(r) > n5:
        net[n5:] = np.abs(np.log(sample['price'][n5:]/sample['price'][:-n5])) * 1e4
    cols = {'fine_log_rv5': np.log(np.maximum(rv5, 1e-8)),
            'fine_log_rv15': np.log(np.maximum(rv15, 1e-8)),
            'fine_log_max1': np.log(np.maximum(rolling_max(np.abs(r), 60//step), 1e-8)),
            'fine_abs_net5': net,
            'fine_gap3_fraction5': g.roll_mean(sample['crossed_gap3'], n5),
            'fine_max_age5': rolling_max(sample['age'], n5),
            'fine_repeat_fraction5': g.roll_mean(repeat, n5)}
    for duration in (30, 60, 120, 240):
        length = duration // step
        if duration % step == 0 and length >= 2 and length % 2 == 0:
            cols[f'fine_log_e{duration}'] = np.log(np.maximum(g.haar_energy(r, length, n5), 1e-8))
        else: cols[f'fine_log_e{duration}'] = np.full(len(r), np.nan)
    minute_ix = np.arange(60//step, len(r), 60//step)
    return pd.DataFrame({k: v[minute_ix] for k, v in cols.items()})


def aligned_targets(f):
    """Actionable e=t+2..t+15 target, plus t+1 imminent and t+1..t+15 safety.

    An imminent event is not silently removed: it is a competing outcome,
    reported in every model's Clean bucket. Unknown futures never become zeros.
    """
    q = f.reset_index(drop=True).copy()
    q['target_any'] = q.target
    q['target'] = np.nan; q['target_imminent'] = np.nan
    for _, ix in q.groupby('session', sort=False).groups.items():
        ix = np.asarray(ix); first = q.loc[ix, 'first'].to_numpy(float)
        if len(ix)>15:
            future=np.lib.stride_tricks.sliding_window_view(first[1:],15)
            known=np.isfinite(future).all(axis=1)
            target=np.where(known,(future[:,1:]==1).any(axis=1).astype(float),np.nan)
            imminent=np.where(known,(future[:,0]==1).astype(float),np.nan)
            q.loc[ix[:-15], 'target']=target
            q.loc[ix[:-15], 'target_imminent']=imminent
    q['metric_ok'] = q.decision_ok & np.isfinite(q.target)
    return q


def attach_support(minute, fine, mask):
    q = aligned_targets(g.make_features(minute))
    if len(q) != len(fine): raise ValueError('fine/minute index mismatch')
    q = pd.concat([q, fine.reset_index(drop=True)], axis=1)
    q['base_decision_ok'] = q.decision_ok
    q['decision_ok'] &= np.asarray(mask, bool) & np.isfinite(q[FINE+SCALE]).all(axis=1)
    q['metric_ok'] = q.decision_ok & np.isfinite(q.target)
    return q


def fit_models(f):
    a = f.loc[f.year.isin([2021, 2022]) & f.metric_ok]
    c = f.loc[(f.year == 2023) & f.decision_ok]
    if len(a) < 500 or len(c) < 100 or a.target.sum() < 20 or a.target.nunique() != 2:
        return None, {'status': 'insufficient_support', 'train_n': len(a),
                      'train_positive_windows': int(a.target.sum()), 'calibration_n': len(c)}
    y = a.target.to_numpy(int)
    residualizer = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    b1 = a[BASE+FINE].to_numpy(float); z = a[SCALE].to_numpy(float)
    residualizer.fit(b1, z)
    residual = z-residualizer.predict(b1); scale = np.maximum(residual.std(axis=0), 1e-8)
    arrays = {'B0': a[BASE].to_numpy(float), 'B1': b1, 'B2': np.c_[b1, residual/scale]}
    models = {}
    for name, x in arrays.items():
        m = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000,
                class_weight=None, solver='lbfgs', random_state=SEED))
        m.fit(x, y); models[name] = m
    pack = {'models': models, 'residualizer': residualizer, 'residual_scale': scale}
    ps = predict(pack, c)
    pack['thresholds'] = {name: {str(b): float(np.quantile(p, 1-b)) for b in (.1, .2, .3)}
                          for name, p in ps.items()}
    return pack, {'status': 'fitted', 'train_n': len(a), 'train_positive_windows': int(y.sum()),
                  'calibration_n': len(c), 'thresholds': pack['thresholds'],
                  'train_counts_by_year': a.groupby('year').size().to_dict()}


def predict(pack, f):
    b1 = f[BASE+FINE].to_numpy(float)
    d = (f[SCALE].to_numpy(float)-pack['residualizer'].predict(b1))/pack['residual_scale']
    arrays = {'B0': f[BASE].to_numpy(float), 'B1': b1, 'B2': np.c_[b1, d]}
    return {name: pack['models'][name].predict_proba(x)[:, 1] for name, x in arrays.items()}


def block_ci(f, alarms, repeats=1000):
    daily = []
    for _, z in f.groupby('day', sort=True):
        row = []
        for name in ('B1', 'B2'):
            ix = z.index[z.metric_ok & ~alarms[name][z.index]]
            row += [float(f.loc[ix, 'target'].sum()), len(ix)]
        daily.append(row)
    return g.moving_block_ci(np.asarray(daily), repeats=repeats)


def matched_null(f, alarm, cuts, repeats=200):
    """Constrained session-template permutation: exact coverage/run lengths/clock.

    Assign donor templates only to recipients whose entire alarm template is
    eligible. Hungarian random-cost assignment preserves each donor once within
    morning/afternoon and train-defined volatility strata. Not a uniform exact
    randomization test; fixed/self-assigned sessions are disclosed.
    """
    from scipy.optimize import linear_sum_assignment
    session_rows = [np.asarray(ix) for ix in f.groupby('session', sort=False).groups.values()]
    if not all(len(ix) == 120 for ix in session_rows): raise ValueError('need full sessions')
    templates = np.asarray([alarm[ix] for ix in session_rows])
    elig = np.asarray([f.loc[ix, 'decision_ok'].to_numpy(bool) for ix in session_rows])
    y = np.asarray([f.loc[ix, 'target'].to_numpy(float) for ix in session_rows])
    first = np.asarray([f.loc[ix, 'first'].to_numpy(float) for ix in session_rows])
    groups = {}
    for j, ix in enumerate(session_rows):
        val = float(f.loc[ix[30], 'log_rv30'])
        bucket = int(np.digitize(val, cuts)) if np.isfinite(val) else -1
        groups.setdefault((int(f.loc[ix[0], 'afternoon']), bucket), []).append(j)
    assignments=[]
    for members in groups.values():
        m=np.asarray(members)
        allowed=(~elig[m]).astype(np.int32) @ templates[m].astype(np.int32).T == 0
        assert np.diag(allowed).all()
        assignments.append((m,allowed))
    rng = np.random.default_rng(SEED); rows = []
    event_pairs = np.argwhere((first == 1) & (np.arange(1, 121)[None, :] >= 33))
    observed = np.isfinite(y) & elig
    obs_episodes = int((templates & ~np.c_[np.zeros(len(templates), bool), templates[:, :-1]]).sum())
    for _ in range(repeats):
        a=np.zeros_like(templates);self_assigned=0
        for members,allowed in assignments:
            cost=rng.random(allowed.shape);cost[~allowed]=1e9
            rec,don=linear_sum_assignment(cost)
            assert allowed[rec,don].all()
            a[members[rec]]=templates[members[don]]
            self_assigned+=int((rec==don).sum())
        assert not (a & ~elig).any() and a.sum()==templates.sum()
        clean = observed & ~a
        hit = sum(bool(a[s, max(0, e-15):max(0, e-1)].any()) for s, e in event_pairs)
        episodes = int((a & ~np.c_[np.zeros(len(a), bool), a[:, :-1]]).sum())
        assert episodes==obs_episodes
        rows.append({'clean_risk': g.ratio(np.nansum(y[clean]), clean.sum()),
                     'risk_time': g.ratio(a.sum(), elig.sum()),
                     'recall': g.ratio(hit, len(event_pairs)), 'episodes': episodes,
                     'self_assignment_fraction':self_assigned/len(a),
                     'changed_alarm_cells':int((a!=templates).sum())})
    clean = observed & ~templates
    obs_risk = g.ratio(np.nansum(y[clean]), clean.sum())
    table = pd.DataFrame(rows)
    return {'status': 'constrained_conditional_surrogate', 'repeats': repeats,
            'exact_preservation':['alarm_minutes','episode_count','episode_lengths','clock_positions'],
            'volatility_strata': len(cuts)+1, 'volatility_measured_at_minute': 31,
            'stratum_sizes': [len(v) for v in groups.values()],
            'observed_clean_risk': obs_risk, 'observed_episodes': obs_episodes,
            'surrogate_quantiles': {c: table[c].quantile([.025, .5, .975]).tolist() for c in table},
            'fraction_surrogate_clean_risk_le_observed_not_exact_p':
                float((table.clean_risk <= obs_risk).mean()) if obs_risk is not None else None,
            'limit': 'not a uniform permutation p-value; strata coarse; eligibility can restrict permutations'}, table


def evaluate(pack, f, out, name, cuts, full_null=False):
    q = f.reset_index(drop=True).copy(); valid = q.decision_ok.to_numpy(bool)
    observed = q.metric_ok.to_numpy(bool); scores = {}
    if not valid.any(): return {'status': 'no_decisions'}
    ps = predict(pack, q.loc[valid])
    for m, p in ps.items():
        scores[m] = np.full(len(q), np.nan); scores[m][valid] = p; q[m+'_score'] = scores[m]
    result = {'all_rows': len(q), 'base_decisions': int(q.base_decision_ok.sum()),
              'decisions': int(valid.sum()), 'mature_decisions': int(observed.sum()),
              'unknown_future': int((valid & ~observed).sum()), 'models': {}, 'curves': {}}
    events = []; quotas = {}
    for model, s in scores.items():
        result['models'][model] = {}
        for mode in ('frozen', 'quota'):
            a = np.zeros(len(q), bool)
            a[valid] = s[valid] >= pack['thresholds'][model]['0.2'] if mode == 'frozen' else g.budget_alarm(s[valid], .2)
            q[model+'_'+mode] = a
            if mode == 'quota': quotas[model] = a
            es, ev = g.match_events(q, a); ev['model'] = model; ev['mode'] = mode; events.append(ev)
            stats = g.metrics(q.loc[observed, 'target'].to_numpy(int), s[observed], a[observed])
            clean = observed & ~a
            stats['risk_any_first_inside_clean'] = g.ratio(q.loc[clean, 'target_any'].sum(), clean.sum())
            stats['imminent_risk_inside_clean'] = g.ratio(q.loc[clean, 'target_imminent'].sum(), clean.sum())
            stats['risk_time_all_decisions'] = float(a[valid].mean())
            stats['label_decomposition_error'] = float(np.max(np.abs(q.loc[observed, 'target_any']-
                    q.loc[observed, 'target']-q.loc[observed, 'target_imminent']))) if observed.any() else None
            result['models'][model][mode] = {'windows': stats, 'events': es}
        result['curves'][model] = {}
        for budget in (.1, .2, .3):
            a = np.zeros(len(q), bool); a[valid] = g.budget_alarm(s[valid], budget)
            result['curves'][model][str(budget)] = g.metrics(q.loc[observed, 'target'].to_numpy(int), s[observed], a[observed])
    result['B2_minus_B1_clean_risk_ci'] = block_ci(q, quotas)
    # All 15 phases retained, not the first/best phase only.
    phase_rows = []
    for phase in range(15):
        ix = observed & (q.minute.to_numpy() % 15 == phase)
        for model in scores:
            phase_rows.append({'phase': phase, 'model': model, **g.metrics(q.loc[ix, 'target'].to_numpy(int),
                              scores[model][ix], quotas[model][ix])})
    pd.DataFrame(phase_rows).to_csv(out/f'{name}_phases.csv', index=False)
    if full_null:
        result['matched_null'] = {}
        for model in ('B1', 'B2'):
            nr, nt = matched_null(q, quotas[model], cuts)
            result['matched_null'][model] = nr; nt.to_csv(out/f'{name}_{model}_surrogates.csv', index=False)
    pd.concat(events, ignore_index=True).to_csv(out/f'{name}_events.csv', index=False)
    q.to_csv(out/f'{name}_decisions.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
    write_json(out/f'{name}_summary.json', result)
    return result


def anchor_table(f, symbol):
    """Outcome-selected case/control ledger; never an estimation of population risk."""
    q = f.reset_index(drop=True)
    candidates = np.zeros(len(q), bool)
    for _, ix in q.groupby('session', sort=False).groups.items():
        ix = np.asarray(ix); ev = q.loc[ix, 'event'].to_numpy(float)
        for j in range(32, len(ix)):
            w = ev[max(0, j-30):min(len(ix), j+16)]
            candidates[ix[j]] = bool(np.isfinite(w).all() and not w.any())
    events = q[(q['first'] == 1) & (q.minute >= 33)]
    pool = q.loc[candidates].copy(); entries = []
    train = q[q.year.isin([2021, 2022])]
    match_cols = ['log_rv30', 'log_rv480']
    scales = train[match_cols].std().fillna(1).clip(lower=1e-8)
    for ix, e in events.iterrows():
        eid = f'{symbol}/{e.session}/{int(e.minute)}'
        entries.append({'anchor_id': eid, 'paired_event_id': eid, 'kind': 'event',
             'symbol': symbol, 'session': e.session, 'day': e.day, 'year': int(e.year),
             'minute': int(e.minute), 'minute_return_bp': float(e.return_bp),
             'sigma_pre': float(e.sigma_pre), 'matching_distance': 0.0})
        c = pool[(pool.year == e.year) & (pool.afternoon == e.afternoon) & (pool.minute == e.minute)].copy()
        if len(c):
            distance = (((c[match_cols]-e[match_cols].astype(float))/scales)**2).sum(axis=1, skipna=False)
            c['distance'] = distance
            c = c[np.isfinite(c.distance)].sort_values(['distance', 'day'], kind='stable').head(3)
        for rank, (_, row) in enumerate(c.iterrows()):
            entries.append({'anchor_id': eid+f'/control{rank+1}', 'paired_event_id': eid,
                'kind': 'control', 'symbol': symbol, 'session': row.session, 'day': row.day,
                'year': int(row.year), 'minute': int(row.minute),
                'minute_return_bp': float(row.return_bp), 'sigma_pre': float(row.sigma_pre),
                'matching_distance': float(row.distance)})
    return pd.DataFrame(entries)


def path_summary(times, prices, rows, anchor):
    """Observed paths, no latent onset claim; invalid/long gaps explicitly retained."""
    t = np.asarray(times, float); p = np.asarray(prices, float); r = np.asarray(rows)
    order = np.lexsort((r, t)); t, p, r = t[order], p[order], r[order]
    e = int(anchor['minute'])*60; left = e-60
    grid = sample_session(t, p, r, 15, 15)
    def at(second):
        j = np.searchsorted(t, second, side='right')-1
        return (float(p[j]), float(second-t[j])) if j >= 0 and second-t[j] <= 3 else (np.nan, np.nan)
    p0, a0 = at(left); p1, a1 = at(e); ppre, _ = at(max(0, left-300))
    ix = np.flatnonzero((t > left) & (t <= e))
    # Include the most recent observation at the left endpoint for true increments.
    start = np.searchsorted(t, left, side='right')-1
    local = np.r_[start, ix] if start >= 0 else ix
    local = np.unique(local)
    tt, pp = t[local], p[local]
    delta = np.diff(np.log(pp))*1e4 if len(local)>1 else np.array([])
    gaps = np.diff(tt)
    zero_time = gaps == 0
    positive_gaps = gaps[gaps > 0]
    uninterrupted = bool(np.isfinite([p0, p1]).all() and len(delta) and
                         positive_gaps.size and positive_gaps.max() <= 3 and not zero_time.any())
    observed_net = np.log(p1/p0)*1e4 if np.isfinite([p0,p1]).all() else np.nan
    total = float(np.abs(delta).sum())
    max_move = float(np.abs(delta).max()) if len(delta) else np.nan
    pre30, _ = at(left-30)
    same_min = np.isfinite(observed_net)
    s = dict(anchor)
    s.update({'snapshot_minute_return_bp': observed_net,
        'snapshot_minus_official_bp': observed_net-float(anchor['minute_return_bp']),
        'source_rows_in_event_minute': len(ix), 'same_second_changes_in_event_minute': int(zero_time.sum()),
        'max_source_gap_seconds': float(positive_gaps.max()) if positive_gaps.size else None,
        'event_minute_complete_3s': uninterrupted,
        'observed_max_increment_bp_not_jump': max_move,
        'complete_path_top3_share': float(np.sort(np.abs(delta))[-3:].sum()/total) if uninterrupted and total>0 else None,
        'complete_path_efficiency': float(abs(observed_net)/total) if uninterrupted and total>0 else None,
        'observed_range_bp_lower_bound': float(np.log(pp.max()/pp.min())*1e4) if len(pp)>1 else None,
        'pre5m_net_bp': float(np.log(p0/ppre)*1e4) if np.isfinite([p0,ppre]).all() else None,
        'pre30s_net_bp': float(np.log(p0/pre30)*1e4) if np.isfinite([p0,pre30]).all() else None,
        'endpoint_age_start_seconds': a0, 'endpoint_age_end_seconds': a1})
    if uninterrupted and total > 0:
        s['path_reason'] = 'concentrated' if s['complete_path_top3_share'] >= .6 else (
            'round_trip' if s['complete_path_efficiency'] < .25 else 'distributed_directional_or_mixed')
    else: s['path_reason'] = 'unknown_incomplete_or_same_second'
    # Intra-minute timing proxy: first 20%/80% of final signed net move from the
    # last pre-minute source quote. Descriptive thresholds, not true causal onset.
    s['seconds_to20pct'] = None; s['seconds_to80pct'] = None
    if uninterrupted and abs(observed_net)>1e-12:
        progress = np.log(pp/p0)*1e4*np.sign(observed_net)/abs(observed_net)
        for frac in (.2,.8):
            hits = np.flatnonzero((tt >= left) & (progress >= frac))
            if len(hits): s[f'seconds_to{int(100*frac)}pct'] = float(tt[hits[0]]-left)
    keep = (t >= max(0, e-600)) & (t <= min(7200, e+300))
    path = pd.DataFrame({'anchor_id': anchor['anchor_id'], 'kind': anchor['kind'],
            'second_relative_to_minute_start': t[keep]-left, 'row_index': r[keep],
            'log_price_relative_bp': np.log(p[keep]/p0)*1e4 if np.isfinite(p0) else np.full(keep.sum(),np.nan)})
    return s, path


def read_seconds(root, symbol, year):
    sys.path.insert(0, str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    frame = load_market_data(symbol, '3s', f'{year}-01-01', f'{year}-12-31', root=root)
    need = {'observation_datetime', 'price', 'row_index', 'trading_day', 'symbol'}
    if not need <= set(frame): raise ValueError(f'missing fields: {need-set(frame)}')
    if frame.duplicated(['symbol','observation_datetime','row_index']).any(): raise ValueError('bad source key')
    ts = frame.market_time_shanghai.dt.tz_localize(None)
    f = frame[['trading_day','row_index','price']].copy()
    f['second_day'] = (ts.dt.hour*3600+ts.dt.minute*60+ts.dt.second).to_numpy()
    f['afternoon'] = (f.second_day >= 13*3600).astype(int)
    f['session'] = f.trading_day + '/' + f.afternoon.astype(str)
    f['second'] = f.second_day - np.where(f.afternoon == 1,13*3600,9*3600+30*60)
    audit = {'symbol': symbol, 'year': year, 'source_rows': len(frame),
             'out_of_session_rows': int((~f.second.between(0,7200)).sum()),
             'same_second_extra': int(frame.duplicated(['symbol','observation_datetime']).sum())}
    return f[f.second.between(0,7200)].copy(), audit


def measure_symbol(root, symbol, minute, anchors, out):
    fine_primary=[]; fine_strict=[]; audit=[]; ledgers=[]; paths=[]
    anchor_groups = {s: z.to_dict('records') for s,z in anchors.groupby('session', sort=False)}
    index = minute[['session','day','year','minute']]
    for year in range(2021,2026):
        seconds, source_audit = read_seconds(root,symbol,year)
        groups = {s: z for s,z in seconds.groupby('session',sort=False)}
        grid_counts = {str(step): {'total_returns':0,'valid_gap15':0,'valid_gap3':0,'fresh_endpoints':0}
                       for step in (15,30,60)}
        for session, sub in index[index.year==year].groupby('session',sort=False):
            raw=groups.get(session)
            if raw is None: t=np.array([]);p=np.array([]);r=np.array([],dtype=int)
            else: t=raw.second.to_numpy(float);p=raw.price.to_numpy(float);r=raw.row_index.to_numpy()
            for step in (15,30,60):
                a=sample_session(t,p,r,step,15); b=sample_session(t,p,r,step,3)
                c=grid_counts[str(step)];c['total_returns']+=len(a['second'])-1
                c['valid_gap15']+=int(np.isfinite(a['return_bp'][1:]).sum())
                c['valid_gap3']+=int(np.isfinite(b['return_bp'][1:]).sum())
                c['fresh_endpoints']+=int(np.isfinite(a['price'][1:]).sum())
                if step==15:
                    fa=fine_features(a);fb=fine_features(b)
                    fa['session']=session;fb['session']=session
                    fine_primary.append(fa);fine_strict.append(fb)
            for anchor in anchor_groups.get(session,[]):
                s,path=path_summary(t,p,r,anchor);ledgers.append(s);paths.append(path)
        source_audit['grids']=grid_counts;audit.append(source_audit)
        print('MEASURED',symbol,year,json.dumps(grid_counts),flush=True)
        del seconds,groups
    primary=pd.concat(fine_primary,ignore_index=True);strict=pd.concat(fine_strict,ignore_index=True)
    if not primary.session.equals(minute.session.reset_index(drop=True)):raise ValueError('measurement order differs')
    pd.DataFrame(ledgers).to_csv(out/f'{symbol}_path_ledger.csv',index=False)
    if paths:pd.concat(paths,ignore_index=True).to_csv(out/f'{symbol}_paths.csv.gz',index=False,
                compression={'method':'gzip','mtime':0})
    write_json(out/f'{symbol}_sampling_audit.json',audit)
    return primary.drop(columns='session'),strict.drop(columns='session')


def validate_inputs(root,out):
    import pyarrow.parquet as pq
    audit=[]
    for folder,frequency in [('cross_index_risk_gate_v1','1m'),('cross_index_risk_gate_3s_v1','3s')]:
        d=root/'data'/folder;m=json.loads((d/'manifest.json').read_text())
        if frequency=='3s':
            ac=json.loads((d/'primary_acceptance.json').read_text())
            assert ac['manifest_sha256']==hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest()
            assert not ac['online_serving_granted'] and not ac['production_granted']
        entries=[i for i in m['files'] if i['symbol'] in SYMBOLS and 2021<=i['year']<=2025 and
                 (frequency=='3s' or i['frequency']=='1m')]
        assert len(entries)==10
        for i in entries:
            p=d/i['path'] if frequency=='3s' else root/i['path']
            actual=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==i['sha256'],str(p)
            f=pq.ParquetFile(p);assert f.metadata.num_rows==i['rows']
            x=f.read(columns=['symbol','trading_day']).to_pandas()
            assert set(x.symbol)=={i['symbol']};assert x.trading_day.min()>=f"{i['year']}-01-01"
            assert x.trading_day.max()<=f"{i['year']}-12-31"
            audit.append({'path':str(p.relative_to(root)),'sha256':actual,'rows':len(x),
                          'manifest_sha256':hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest()})
    actuals=set(str(p.relative_to(root)) for p in (root/'data').rglob('*.parquet'))
    assert actuals==set(i['path'] for i in audit),'unexpected physical price inputs'
    write_json(out/'input_receipt.json',{'files':audit,'execution_location':'GitHub Actions',
             'run_id':os.getenv('GITHUB_RUN_ID'),'workflow_commit':os.getenv('GITHUB_SHA'),
             'scope':'two indices 2021-2025; 20 files; no full-package or production acceptance',
             'fresh_oos':False,'production_authority':False})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.out.resolve()
    if out.exists() and any(out.iterdir()):raise FileExistsError('refuse to overwrite')
    out.mkdir(parents=True,exist_ok=True);validate_inputs(root,out)
    sys.path.insert(0,str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    minute={}
    for symbol in SYMBOLS:
        native=load_market_data(symbol,'1m','2021-01-01','2025-12-31',root=root)
        minute[symbol]=g.minute_panel(native,symbol)
    common=set(minute[SYMBOLS[0]].session)&set(minute[SYMBOLS[1]].session)
    for symbol in SYMBOLS:minute[symbol]=minute[symbol][minute[symbol].session.isin(common)].reset_index(drop=True)
    if not minute[SYMBOLS[0]][['session','minute']].equals(minute[SYMBOLS[1]][['session','minute']]):
        raise ValueError('not paired')
    joint_min=np.isfinite(minute[SYMBOLS[0]].return_bp)&np.isfinite(minute[SYMBOLS[1]].return_bp)
    joint={s:x.copy() for s,x in minute.items()}
    for s in SYMBOLS:joint[s].loc[~joint_min,'return_bp']=np.nan
    fine={};strict={};base={};support=[]
    for s in SYMBOLS:
        base[s]=aligned_targets(g.make_features(joint[s]));anchors=anchor_table(base[s],s)
        anchors.to_csv(out/f'{s}_anchors.csv',index=False)
        fine[s],strict[s]=measure_symbol(root,s,joint[s],anchors,out)
    joint_fine=np.isfinite(fine[SYMBOLS[0]][FINE+SCALE]).all(axis=1)&np.isfinite(fine[SYMBOLS[1]][FINE+SCALE]).all(axis=1)
    joint_strict=np.isfinite(strict[SYMBOLS[0]][FINE+SCALE]).all(axis=1)&np.isfinite(strict[SYMBOLS[1]][FINE+SCALE]).all(axis=1)
    results={};fits={};frames={}
    for s in SYMBOLS:
        frames[s]={
            'primary_joint_gap15':attach_support(joint[s],fine[s],joint_fine),
            'sensitivity_joint_gap3':attach_support(joint[s],strict[s],joint_strict),
            'sensitivity_individual_gap15':attach_support(minute[s],fine[s],np.ones(len(fine[s]),bool))}
        train=base[s][base[s].year.isin([2021,2022]) & (base[s].minute==31)]
        cuts=np.quantile(train.log_rv30.dropna(),[1/3,2/3])
        for version,f in frames[s].items():
            for year,z in f.groupby('year'):
                support.append({'symbol':s,'version':version,'year':int(year),'rows':len(z),
                    'base_decisions':int(z.base_decision_ok.sum()),'fine_decisions':int(z.decision_ok.sum()),
                    'mature_decisions':int(z.metric_ok.sum()),
                    'actionable_positive_windows':int(z.loc[z.metric_ok,'target'].sum()),
                    'known_first_events':int(((z['first']==1)&(z.minute>=33)).sum())})
            pack,fit=fit_models(f);fits[s+'/'+version]=fit
            if pack is None:continue
            import joblib
            joblib.dump(pack,out/f'{s}_{version}_models.joblib')
            for year in (2024,2025):
                name=f'{s}_{version}_{year}'
                results[name]=evaluate(pack,f[f.year==year],out,name,cuts,version=='primary_joint_gap15')
                print('EVALUATED',name,flush=True)
    pd.DataFrame(support).to_csv(out/'support.csv',index=False)
    write_json(out/'fits.json',fits);write_json(out/'all_results.json',results)
    write_json(out/'run_receipt.json',{'status':'completed bounded V2 measurements and comparisons',
        'execution_location':'GitHub Actions','code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'protocol_sha256':hashlib.sha256((Path(__file__).resolve().parents[1]/'protocol.json').read_bytes()).hexdigest(),
        'run_id':os.getenv('GITHUB_RUN_ID'),'git_commit':os.getenv('GITHUB_SHA'),
        'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
        'summaries':len(results),'fits_attempted':len(fits),'fresh_oos':False,'production_authority':False,
        'not_claimed':['causal mechanism','real-time source availability','zero-risk Clean bucket',
                       'fresh OOS','optimal resolution','all possible models rejected'],
        'random_control_limit':'constrained random-cost assignments are not uniform exact permutation tests; self-matching disclosed'})
    print('V2_COMPLETE',len(results),flush=True)


if __name__=='__main__':main()
