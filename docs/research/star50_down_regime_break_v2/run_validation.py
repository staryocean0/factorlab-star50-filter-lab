from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START = '2024-01-01'
END = '2026-08-21'
YEARS = (2024, 2025, 2026)
DRAWS = 10_000
SEED = 20260908


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def build_validation_events(root: Path) -> pd.DataFrame:
    dev = load_module(root / 'docs/research/star50_down_regime_break_v2/run_dev.py', 'star50_v2_dev')
    mech = load_module(root / 'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py', 'star50_v2_mech')
    reg = load_module(root / 'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py', 'star50_v2_reg')
    orig = load_module(root / 'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py', 'star50_v2_orig')
    fg = load_module(root / 'docs/research/state_conditioned_frequency_v2/code/fast_grid.py', 'star50_v2_fg')

    candidate, _ = dev.load_candidate(root)
    assert candidate['validation']['start'] == START and candidate['validation']['end'] == END
    assert candidate['validation']['open_only_if_development_passes'] is True
    assert candidate['blackbox']['query'] is False

    native = orig.load_native(root, '000688.SH').copy()
    native['trading_day'] = native['trading_day'].astype(str).str[:10]
    native = native[(native['trading_day'] >= START) & (native['trading_day'] <= END)].copy()
    if len(native) == 0:
        raise RuntimeError('no Validation rows')
    assert native['trading_day'].min() >= START and native['trading_day'].max() <= END

    state = reg.build_continuous_state(native, '000688.SH')
    minute = fg.build_minute_grid(
        native,
        state.rename(columns={'vol_ratio': 'recovery_ratio'}),
        '000688.SH',
    ).reset_index(drop=True)
    minute = minute[(minute['trading_day'] >= START) & (minute['trading_day'] <= END)].reset_index(drop=True)
    events = mech.build_events(minute)
    if len(events):
        d = events['trading_day'].astype(str)
        assert d.min() >= START and d.max() <= END
    return events


def day_block_bootstrap_net1(selected: pd.DataFrame) -> dict:
    if len(selected) == 0:
        return {'draws': DRAWS, 'seed': SEED, 'days': 0, 'mean_net_bp': np.nan, 'ci_low_bp': np.nan, 'ci_high_bp': np.nan}
    q = selected[['trading_day', 'gross_bp']].copy()
    q['net_bp'] = pd.to_numeric(q['gross_bp'], errors='coerce') - 2.0
    q = q.dropna()
    g = q.groupby('trading_day', sort=True)['net_bp'].agg(['sum', 'count']).reset_index()
    mean = float(q['net_bp'].mean()) if len(q) else np.nan
    if len(g) < 2:
        return {'draws': DRAWS, 'seed': SEED, 'days': int(len(g)), 'mean_net_bp': mean, 'ci_low_bp': np.nan, 'ci_high_bp': np.nan}
    sums = g['sum'].to_numpy(float)
    counts = g['count'].to_numpy(float)
    rng = np.random.default_rng(SEED)
    vals = np.empty(DRAWS, dtype=float)
    for i in range(DRAWS):
        ix = rng.integers(0, len(g), len(g))
        vals[i] = sums[ix].sum() / counts[ix].sum()
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return {
        'draws': DRAWS,
        'seed': SEED,
        'days': int(len(g)),
        'mean_net_bp': mean,
        'ci_low_bp': float(lo),
        'ci_high_bp': float(hi),
    }


def run(root: Path, out: Path) -> dict:
    dev = load_module(root / 'docs/research/star50_down_regime_break_v2/run_dev.py', 'star50_v2_dev_eval')
    candidate, candidate_sha256 = dev.load_candidate(root)
    prereg = json.loads((root / 'docs/research/star50_down_regime_break_v2/VALIDATION_PREREGISTRATION.json').read_text())
    assert prereg['candidate_sha256'] == candidate_sha256
    assert prereg['development_evidence']['all_primary_pass'] is True
    assert prereg['validation_start'] == START and prereg['validation_end'] == END
    assert prereg['blackbox_query'] is False

    events = build_validation_events(root)
    selected = dev.select(events)
    annual_rows = []
    for year in YEARS:
        annual_rows.append({'year': year, **dev.metrics(selected[selected['year'].eq(year)])})
    annual = pd.DataFrame(annual_rows)
    pooled = dev.metrics(selected)
    positive_years = int((annual['mean_net_1bp_per_leg'] > 0).sum())
    acceptance = {
        'total_trades_ge_30': bool(pooled['trades'] >= 30),
        'pooled_net1_positive': bool(pooled['mean_net_1bp_per_leg'] > 0),
        'positive_year_slices_ge_2': bool(positive_years >= 2),
        'pooled_break_even_gt_1bp': bool(pooled['one_way_break_even_bp'] > 1.0),
    }
    acceptance['all_primary_pass'] = bool(all(acceptance.values()))
    bootstrap = day_block_bootstrap_net1(selected)

    out.mkdir(parents=True, exist_ok=True)
    selected.to_csv(out / 'validation_trades.csv', index=False)
    annual.to_csv(out / 'annual.csv', index=False)
    pd.DataFrame([pooled]).to_csv(out / 'pooled.csv', index=False)
    (out / 'bootstrap_net1.json').write_text(json.dumps(bootstrap, indent=2, default=str) + '\n')

    meta = {
        'schema': 'star50_down_regime_break_v2_validation_v1',
        'candidate_id': candidate['candidate_id'],
        'candidate_sha256': candidate_sha256,
        'validation_start': START,
        'validation_end': END,
        'validation_role': 'reusable_validation_tuning_evidence',
        'candidate_fit_on_validation': False,
        'blackbox_queried': False,
        'candidate': {
            'direction': 'short',
            'slow30_sign': 'positive',
            'net5_sign': 'negative',
            'efficiency5_min': 0.60,
            'tail2_share_min': 0.50,
            'tail1_condition': None,
            'hold_min': 3,
        },
        'positive_year_slices': positive_years,
        'acceptance': acceptance,
        'pooled': pooled,
        'bootstrap_net1_day_block': bootstrap,
    }
    (out / 'summary.json').write_text(json.dumps(meta, indent=2, default=str) + '\n')
    print(json.dumps(meta, default=str))
    return meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    run(Path(args.repo_root).resolve(), Path(args.out).resolve())


if __name__ == '__main__':
    main()
