from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START = '2021-01-01'
END = '2023-12-31'
YEARS = (2021, 2022, 2023)
HOLD_MIN = 3
PRIMARY_COST_BP_PER_LEG = 1.0
COSTS = (0.5, 1.0, 1.5, 2.0)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def load_candidate(root: Path) -> tuple[dict, str]:
    path = root / 'docs/research/star50_down_regime_break_v2/candidate.json'
    raw = path.read_bytes()
    cfg = json.loads(raw)
    assert cfg['candidate_id'] == 'star50_downside_accelerated_regime_break_v2'
    assert cfg['symbol'] == '000688.SH'
    assert cfg['signal']['efficiency5'] == '>=0.60'
    assert cfg['signal']['tail2_share'] == '>=0.50'
    assert cfg['signal']['tail1_condition'] is None
    assert cfg['execution']['direction'] == 'short'
    assert cfg['execution']['hold_minutes'] == HOLD_MIN
    assert cfg['development']['start'] == START and cfg['development']['end'] == END
    assert cfg['blackbox']['query'] is False
    return cfg, hashlib.sha256(raw).hexdigest()


def select(events: pd.DataFrame) -> pd.DataFrame:
    mask = (
        events['direction'].eq('down')
        & (pd.to_numeric(events['slow30_net_bp'], errors='coerce') > 0.0)
        & (pd.to_numeric(events['net5_bp'], errors='coerce') < 0.0)
        & (pd.to_numeric(events['efficiency5'], errors='coerce') >= 0.60)
        & (pd.to_numeric(events['tail2_share'], errors='coerce') >= 0.50)
        & np.isfinite(pd.to_numeric(events['signed_3m_bp'], errors='coerce'))
    )
    z = events.loc[mask].copy().sort_values(['session', 'onset_row'])
    rows = []
    for _, g in z.groupby('session', sort=False):
        next_allowed_onset = -1
        for _, r in g.iterrows():
            onset = int(r['onset_row'])
            if onset < next_allowed_onset:
                continue
            rows.append(r)
            # Match the existing project convention: after an onset at i,
            # entry is i+1 and a H-minute trade exits at open i+1+H.
            # The next accepted onset must be at least that exit row.
            next_allowed_onset = onset + 1 + HOLD_MIN
    q = pd.DataFrame(rows)
    if len(q):
        q = q.copy()
        q['gross_bp'] = pd.to_numeric(q['signed_3m_bp'], errors='coerce')
    return q


def metrics(z: pd.DataFrame) -> dict:
    n = int(len(z))
    mean = float(z['gross_bp'].mean()) if n else np.nan
    out = {
        'trades': n,
        'mean_gross_bp': mean,
        'median_gross_bp': float(z['gross_bp'].median()) if n else np.nan,
        'hit_rate': float((z['gross_bp'] > 0).mean()) if n else np.nan,
        'one_way_break_even_bp': mean / 2.0 if n else np.nan,
    }
    for cost in COSTS:
        out[f'mean_net_{cost:g}bp_per_leg'] = mean - 2.0 * cost if n else np.nan
    return out


def run(root: Path, out: Path) -> dict:
    candidate, candidate_sha256 = load_candidate(root)
    mech = load_module(
        root / 'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py',
        'star50_v2_mechanism',
    )
    minute = mech.build_minute(root)
    events = mech.build_events(minute)
    assert len(events) == 0 or (
        events['trading_day'].astype(str).min() >= START
        and events['trading_day'].astype(str).max() <= END
    )
    selected = select(events)

    annual_rows = []
    for year in YEARS:
        annual_rows.append({'year': year, **metrics(selected[selected['year'].eq(year)])})
    annual = pd.DataFrame(annual_rows)
    pooled = metrics(selected)

    acceptance = {
        'pooled_trades_ge_60': bool(pooled['trades'] >= 60),
        'each_year_trades_ge_15': bool((annual['trades'] >= 15).all()),
        'each_year_net1_positive': bool((annual['mean_net_1bp_per_leg'] > 0).all()),
        'pooled_net1_positive': bool(pooled['mean_net_1bp_per_leg'] > 0),
        'pooled_break_even_gt_1bp': bool(pooled['one_way_break_even_bp'] > 1.0),
    }
    acceptance['all_primary_pass'] = bool(all(acceptance.values()))

    out.mkdir(parents=True, exist_ok=True)
    selected.to_csv(out / 'dev_trades.csv', index=False)
    annual.to_csv(out / 'annual.csv', index=False)
    pd.DataFrame([pooled]).to_csv(out / 'pooled.csv', index=False)

    meta = {
        'schema': 'star50_down_regime_break_v2_dev_v1',
        'candidate_id': candidate['candidate_id'],
        'candidate_sha256': candidate_sha256,
        'development_start': START,
        'development_end': END,
        'development_only': True,
        'validation_queried': False,
        'blackbox_queried': False,
        'candidate': {
            'direction': 'short',
            'slow30_sign': 'positive',
            'net5_sign': 'negative',
            'efficiency5_min': 0.60,
            'tail2_share_min': 0.50,
            'tail1_condition': None,
            'hold_min': HOLD_MIN,
        },
        'acceptance': acceptance,
        'pooled': pooled,
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
