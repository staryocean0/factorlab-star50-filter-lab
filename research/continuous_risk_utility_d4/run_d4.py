"""D4 preregistered continuous-refresh probes; not a trading or serving model."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import importlib.util
import json
import platform
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROTOCOL_COMMIT = 'ef865110aee6c1c3b300d27c38a578c2b8882a67'
PROTOCOL_BLOB = 'a377e60eea7681182427262d576bddcafe448ef5'
D3_BLOB = 'ea9f77bedd0b952385917015ef080800bfa596ba'
BUNDLE_SHA = 'ee634995477c6a6c043ccb452175b142e20161d932e26a0dc391ff48e186b533'
TRANSPORT_SHA = 'cc37a181782ea25e61329285641739a2284e77a0f1a4c3672783d8ee23b78b84'
OLD_MODEL_SHA = 'f5a33a71969a18f2e7aa0aad45cd83903943d86962f2a92f5206e348667a2db0'
MODELS = ('H', 'L', 'C')
ENDPOINTS = ('log_future_sigma', 'future_tail')
SEED = 20260913
FAMILY = 12
REPETITIONS = 5000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


source = ROOT / 'research/causal_state_utility_d3/run_d3.py'
if git_blob(source.read_bytes()) != D3_BLOB:
    raise RuntimeError('D3 dependency is not the frozen source')
spec = importlib.util.spec_from_file_location('d4_frozen_d3', source)
d3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d3)


def history(prices: pd.DataFrame) -> pd.DataFrame:
    """L uses only returns strictly before the current bar; no overnight return."""
    p = d3.history(prices)
    p['lag_std12'] = np.nan
    for _, g in p.groupby('symbol', sort=False):
        v = g.r.dropna()
        p.loc[v.index, 'lag_std12'] = v.shift(1).rolling(12, min_periods=12).std(ddof=0)
    return p


def table(p, events, years):
    q = d3.causal_table(p, events, years)
    q['lag_intensity'] = q.last_abs / q.bg48
    q['lag_ratio'] = q.lag_std12 / q.bg48
    if not np.isfinite(q.loc[q.available, ['lag_intensity', 'lag_ratio']]).all().all():
        raise RuntimeError('L would alter original cohort')
    return q


def design(q, model):
    if model not in MODELS:
        raise ValueError('unknown probe')
    if model == 'H':
        return d3.design(q, 'B1')
    if model == 'C':
        return d3.design(q, 'B3')
    z = q.copy()
    z['shock_intensity'] = z.lag_intensity
    z['vol_ratio'] = z.lag_ratio
    return d3.design(z, 'B3')


def predict(q, model, probe, endpoint):
    x, names = design(q, model)
    if names != probe['names']:
        raise RuntimeError('feature schema drift')
    value = ((x - np.array(probe['mean'])) / np.array(probe['scale'])) @ np.array(probe['beta']) + probe['intercept']
    return np.clip(value, 0, 1) if endpoint == 'future_tail' else value


def quantile_fit(q):
    if not q.year.between(2021, 2023).all():
        raise ValueError('quantiles fit on Development only')
    return {s: {c: g[c].quantile([.2, .8], interpolation='linear').tolist()
                for c in ('shock_intensity', 'vol_ratio')}
            for s, g in q[q.available].groupby('symbol', sort=True)}


def quantile_keys(q, boundaries):
    result = pd.DataFrame(index=q.index)
    for col, prefix in (('shock_intensity', 'I'), ('vol_ratio', 'V')):
        result[prefix] = 'UNAVAILABLE'
        for symbol, b in boundaries.items():
            m = q.symbol.eq(symbol) & q.available
            low, high = b[col]
            result.loc[m, prefix] = np.select([q.loc[m, col] <= low, q.loc[m, col] <= high],
                                               ['QLOW', 'QMID'], default='QHIGH')
    result['bucket'] = 'I_' + result.I + '|V_' + result.V
    result.loc[~q.available, 'bucket'] = 'UNAVAILABLE'
    return result


def interval(blocks):
    rng = np.random.default_rng(SEED)
    gain, count = np.zeros(REPETITIONS), np.zeros(REPETITIONS)
    for _, g in blocks.groupby('year', sort=True):
        indices = rng.integers(0, len(g), size=(REPETITIONS, len(g)))
        gain += g.gain.to_numpy()[indices].sum(axis=1)
        count += g.n.to_numpy()[indices].sum(axis=1)
    a = .05 / (2 * FAMILY)
    low, high = np.quantile(gain / count, [a, 1-a])
    return {'low': float(low), 'high': float(high), 'blocks': len(blocks), 'repetitions': REPETITIONS}


def compare(q, endpoint, base, predictions, forward, dev_n, coverage, h, out):
    y = q[endpoint].to_numpy(float)
    l0 = (y - predictions[(endpoint, base)]) ** 2
    l1 = (y - predictions[(endpoint, 'C')]) ** 2
    gain = l0 - l1
    slices = {}
    for col in ('year', 'symbol'):
        for key, ix in q.groupby(col, sort=True).indices.items():
            slices[f'{col}:{key}'] = {'n': len(ix), 'absolute_gain': float(gain[ix].mean()),
                                      'relative_gain': float(gain[ix].mean()/l0[ix].mean())}
    cis = {}
    for days in (5, 20):
        blocks = d3.block_stats(q, gain, days)
        blocks.to_csv(out/f'blocks_{h}_{endpoint}_C_vs_{base}_{days}d.csv', index=False, float_format='%.17g')
        cis[str(days)] = interval(blocks)
    absolute, relative = float(gain.mean()), float(gain.mean()/l0.mean())
    gates = {
        'sample_size': len(q) >= 10000 and dev_n >= 20000 and all(v['n'] >= 1000 for v in slices.values()),
        'positive_events': endpoint != 'future_tail' or int(y.sum()) >= 100,
        'relative_at_least_one_percent': relative >= .01,
        'tail_absolute_at_least_0005': endpoint != 'future_tail' or absolute >= .0005,
        'adjusted_5day_interval_positive': cis['5']['low'] > 0,
        'annual_and_symbol_signs': all(v['absolute_gain'] >= 0 for v in slices.values()),
        'coverage': coverage >= .95,
        'development_2023_forward_nonnegative': forward >= 0,
    }
    return {'horizon': h, 'endpoint': endpoint, 'comparison': f'C_vs_{base}', 'n': len(q),
            'baseline_loss': float(l0.mean()), 'continuous_loss': float(l1.mean()),
            'absolute_gain': absolute, 'relative_gain': relative, 'ci_5day': cis['5'],
            'ci_20day_sensitivity': cis['20'], 'slices': slices, 'development_forward_gain': forward,
            'gates': gates, 'supported': all(gates.values())}


def describe(q, p, h, boundaries):
    keys = quantile_keys(q, boundaries)
    z = q.copy()
    z['numeric_bucket'] = keys.bucket
    tables = {}
    for col in ('numeric_bucket', 'year', 'symbol', 'freshness', 'state'):
        rows = []
        levels = ([f'I_{a}|V_{b}' for a in ('QLOW','QMID','QHIGH') for b in ('QLOW','QMID','QHIGH')]
                  if col == 'numeric_bucket' else sorted(z[col].unique()))
        for level in levels:
            g = z[z[col].eq(level)]
            rows.append({'bucket': str(level), 'n': len(g), 'occupancy': len(g)/len(z),
                         'sigma_mean': float(g.sigma.mean()) if len(g) else None,
                         'sigma_median': float(g.sigma.median()) if len(g) else None,
                         'tail_rate': float(g.future_tail.mean()) if len(g) else None})
        tables[col] = rows
    future = z.price_idx.to_numpy(int)[:, None] + np.arange(1, h//5+1)
    shocks = p.own_tail.to_numpy()[future]
    upper = (keys.I.eq('QHIGH') | keys.V.eq('QHIGH')).to_numpy()
    eligible, captured = np.unique(future[shocks]), np.unique(future[shocks & upper[:, None]])
    tables['descriptive_upper_axis_event_coverage'] = {
        'eligible_unique_shocks': len(eligible), 'covered_unique_shocks': len(captured),
        'coverage': len(captured)/len(eligible) if len(eligible) else None,
        'window_occupancy': float(upper.mean()),
        'selected_window_no_tail_rate': float(z.loc[upper, 'future_tail'].eq(0).mean()) if upper.any() else None,
        'not_a_promotion_gate': True,
    }
    return tables


def inputs(args):
    if sha(args.d3_bundle.read_bytes()) != BUNDLE_SHA or sha(args.transport.read_bytes()) != TRANSPORT_SHA:
        raise RuntimeError('sealed input mismatch')
    with zipfile.ZipFile(args.d3_bundle) as z:
        old_bytes = z.read('results/FROZEN_PROBES.json')
    if sha(old_bytes) != OLD_MODEL_SHA:
        raise RuntimeError('old model drift')
    raw, events, identity = d3.load_inputs(args.transport, args.ledger)
    identity.update({'d3_bundle_sha256': BUNDLE_SHA, 'd3_model_sha256': OLD_MODEL_SHA,
                     'd3_runner_git_blob': D3_BLOB, 'protocol_commit': PROTOCOL_COMMIT,
                     'protocol_git_blob': PROTOCOL_BLOB, 'runner_sha256': sha(Path(__file__).read_bytes()),
                     'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__})
    return raw, history(raw), events, json.loads(old_bytes), identity


def execute(args):
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    raw, p, events, old, identity = inputs(args)
    close = events[events.event_type.eq('CLOSE')]
    if args.phase == 'fit':
        if (out/'FROZEN_MODELS.json').exists():
            raise RuntimeError('refuse overwriting final frozen models')
        q = table(p, events, (2021,2022,2023))
        models, forward, coverage, forward_models = {}, {}, {}, {}
        for h in d3.HORIZONS:
            rows = d3.labels(p, q, h, close)
            z = rows[rows.available & rows.label_ok].reset_index(drop=True)
            a, b = z[z.year <= 2022], z[z.year == 2023]
            coverage[str(h)] = {'eligible': len(z), 'time_feasible': int(rows.label_ok.sum()), 'grid': len(rows)}
            for endpoint in ENDPOINTS:
                preds = {}
                for m in MODELS:
                    x, names = design(a, m)
                    f = d3.fit_probe(x, a[endpoint].to_numpy(float), names)
                    key = f'{h}|{endpoint}|{m}'
                    forward_models[key] = f
                    preds[m] = predict(b, m, f, endpoint)
                    if m == 'L':
                        xx, nn = design(z, m)
                        models[key] = d3.fit_probe(xx, z[endpoint].to_numpy(float), nn)
                    else:
                        models[key] = old['probes'][f"{h}|{endpoint}|{'B1' if m == 'H' else 'B3'}"]
                    if models[key]['n'] != len(z):
                        raise RuntimeError('development cohort changed')
                y = b[endpoint].to_numpy(float)
                for base in ('H','L'):
                    l0, l1 = (y-preds[base])**2, (y-preds['C'])**2
                    forward[f'{h}|{endpoint}|{base}'] = {'n': len(b), 'absolute_gain': float((l0-l1).mean()),
                                                         'relative_gain': float((l0-l1).mean()/l0.mean())}
        frozen = {'schema': 'd4_frozen_probes_v1', 'identity': identity, 'models': models,
                  'development_coverage': coverage, 'development_forward': forward,
                  'quantile_boundaries': quantile_fit(q), 'ridge_lambda': .01,
                  'reuse_H_C_from_D3': True, 'validation_scored_in_d4': False}
        dump(out/'FROZEN_MODELS.json', frozen)
        dump(out/'DEVELOPMENT_FORWARD_MODELS.json', forward_models)
        dump(out/'FIT_RECEIPT.json', {'identity': identity, 'model_sha256': sha((out/'FROZEN_MODELS.json').read_bytes()),
             'new_full_development_models': 6, 'reused_models': 12, 'forward_diagnostic_models': 18,
             'training_years': [2021,2022,2023], 'validation_scored_in_d4': False})
        dump(out/'DEVELOPMENT_FORWARD.json', forward)
        print(json.dumps({'fit_complete': True, 'model_sha256': sha((out/'FROZEN_MODELS.json').read_bytes()), 'forward': forward}), flush=True)
        return
    before = sha((out/'FROZEN_MODELS.json').read_bytes())
    frozen = json.loads((out/'FROZEN_MODELS.json').read_text())
    if frozen['identity'] != identity or before != json.loads((out/'FIT_RECEIPT.json').read_text())['model_sha256']:
        raise RuntimeError('code/environment/input/model drift after freeze')
    q = table(p, events, (2024,2025))
    comparisons, coverage, descriptions, parity = [], {}, {}, {}
    for h in d3.HORIZONS:
        rows = d3.labels(p, q, h, close)
        z = rows[rows.available & rows.label_ok].reset_index(drop=True)
        time_n = int(rows.label_ok.sum())
        coverage[str(h)] = {'grid': len(rows), 'time_feasible': time_n, 'eligible': len(z), 'coverage': len(z)/time_n,
                            'future_window_unavailable': int((~rows.label_ok).sum()),
                            'state_or_history_unavailable': int((rows.label_ok & ~rows.available).sum()),
                            'stale_over15s_eligible': int(z.freshness.eq('GT15s').sum())}
        columns = ['symbol','trading_day','bar_end','decision_time','state','freshness','lag_intensity','lag_ratio',
                   'shock_intensity','vol_ratio','bg48','log_future_sigma','future_tail','label_start','label_end']
        evidence = z[columns].copy()
        preds = {}
        with zipfile.ZipFile(args.d3_bundle) as archive:
            previous = pd.read_csv(archive.open(f'results/validation_predictions_{h}m.csv.gz'), compression='gzip', float_precision='round_trip')
        if list(previous.symbol) != list(z.symbol) or not np.array_equal(pd.to_datetime(previous.bar_end).to_numpy(), z.bar_end.to_numpy()):
            raise RuntimeError('cohort drift vs D3 saved evidence')
        for endpoint in ENDPOINTS:
            for m in MODELS:
                pred = predict(z, m, frozen['models'][f'{h}|{endpoint}|{m}'], endpoint)
                preds[(endpoint,m)] = pred
                evidence[f'{endpoint}_{m}'] = pred
                if m in ('H','C'):
                    diff = float(np.max(np.abs(pred-previous[f"{endpoint}_{'B1' if m == 'H' else 'B3'}"].to_numpy())))
                    parity[f'{h}|{endpoint}|{m}'] = diff
                    if diff > 1e-10:
                        raise RuntimeError('reused D3 predictions changed')
            for base in ('H','L'):
                gain = frozen['development_forward'][f'{h}|{endpoint}|{base}']['absolute_gain']
                comparisons.append(compare(z, endpoint, base, preds, gain,
                    frozen['development_coverage'][str(h)]['eligible'], len(z)/time_n, h, out))
        evidence.to_csv(out/f'validation_predictions_{h}m.csv.gz', index=False,
                        compression={'method':'gzip','mtime':0}, float_format='%.17g')
        descriptions[str(h)] = describe(z, p, h, frozen['quantile_boundaries'])
    # Causal scalar export has no labels/current final close; quantile columns are research encodings.
    allq = table(p, events, (2021,2022,2023,2024,2025))
    attrs = allq[['symbol','bar_end','decision_time','published_at','valid_until','observation_time','state',
                  'state_basis','availability_reason','available','shock_intensity','vol_ratio','lag_intensity','lag_ratio']].copy()
    attrs['delta_intensity'] = attrs.shock_intensity-attrs.lag_intensity
    attrs['delta_ratio'] = attrs.vol_ratio-attrs.lag_ratio
    numeric = ['shock_intensity','vol_ratio','lag_intensity','lag_ratio','delta_intensity','delta_ratio']
    attrs.loc[~attrs.available, numeric] = np.nan
    attrs['numeric_bucket'] = quantile_keys(allq, frozen['quantile_boundaries']).bucket
    attrs.to_csv(out/'causal_attributes.csv.gz', index=False, compression={'method':'gzip','mtime':0}, float_format='%.17g')
    supported = [f'{h}|{ep}' for h in d3.HORIZONS for ep in ENDPOINTS
                 if all(r['supported'] for r in comparisons if r['horizon']==h and r['endpoint']==ep)]
    if before != sha((out/'FROZEN_MODELS.json').read_bytes()):
        raise RuntimeError('frozen model was mutated')
    summary = {'schema':'d4_utility_result_v1', 'supported_endpoints':supported,
               'decision':'D4_CONTINUOUS_REFRESH_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS' if supported else 'D4_CONTINUOUS_REFRESH_UTILITY_NOT_SUPPORTED',
               'comparisons':comparisons, 'coverage':coverage, 'D3_reused_prediction_max_diffs':parity,
               'model_sha256_before_after':before, 'identity':identity, 'attribute_rows':len(attrs),
               'attribute_available_rows':int(attrs.available.sum()), 'fresh_oos':False,
               'd3_decision_unchanged':True, 'v19_modified':False, 'v20_started':False,
               'queried_2026':False, 'blackbox_queried':False, 'pnl_computed':False, 'production_authority':False}
    dump(out/'SUMMARY.json', summary)
    dump(out/'VALIDATION_DESCRIPTIVE.json', descriptions)
    print(json.dumps(summary,ensure_ascii=False,indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['fit','evaluate'], required=True)
    for key in ('d3-bundle','transport','ledger','out'):
        parser.add_argument('--'+key, type=Path, required=True)
    execute(parser.parse_args())
