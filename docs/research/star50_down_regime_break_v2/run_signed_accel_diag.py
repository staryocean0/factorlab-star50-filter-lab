from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HOLD_MIN = 3


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def build_panel(root: Path, start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    mech = load_module(root / 'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py', 'signed_diag_mech')
    reg = load_module(root / 'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py', 'signed_diag_reg')
    orig = load_module(root / 'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py', 'signed_diag_orig')
    fg = load_module(root / 'docs/research/state_conditioned_frequency_v2/code/fast_grid.py', 'signed_diag_fg')

    native = orig.load_native(root, '000688.SH').copy()
    native['trading_day'] = native['trading_day'].astype(str).str[:10]
    native = native[(native['trading_day'] >= start) & (native['trading_day'] <= end)].copy()
    assert len(native)
    state = reg.build_continuous_state(native, '000688.SH')
    minute = fg.build_minute_grid(native, state.rename(columns={'vol_ratio': 'recovery_ratio'}), '000688.SH').reset_index(drop=True)
    minute = minute[(minute['trading_day'] >= start) & (minute['trading_day'] <= end)].reset_index(drop=True)
    events = mech.build_events(minute)

    extra = []
    for session, z0 in minute.groupby('session', sort=False):
        z = z0.sort_values('minute').reset_index(drop=True)
        p = np.log(pd.to_numeric(z['close'], errors='coerce').to_numpy(float))
        r = np.diff(p, prepend=np.nan) * 1e4
        valid = z['valid'].to_numpy(bool)
        for i in range(35, len(z)):
            if not valid[i-34:i+1].all():
                continue
            rr = r[i-4:i+1]
            if len(rr) != 5 or not np.isfinite(rr).all():
                continue
            net = float(rr.sum())
            if net == 0:
                continue
            sign = 1 if net > 0 else -1
            prefix3 = float(rr[:3].sum())
            tail2 = float(rr[-2:].sum())
            prefix_dir = sign * prefix3
            tail2_dir = sign * tail2
            total_dir = abs(net)
            extra.append({
                'session': session,
                'onset_row': i,
                'prefix3_net_bp': prefix3,
                'tail2_net_bp': tail2,
                'prefix3_dir_bp': prefix_dir,
                'tail2_dir_bp': tail2_dir,
                'signed_accel_contrast_bp_per_min': tail2_dir / 2.0 - prefix_dir / 3.0,
                'late2_same_direction': bool(tail2_dir > 0),
                'late2_majority_of_net': bool(tail2_dir >= 0.5 * total_dir),
            })
    extra = pd.DataFrame(extra)
    out = events.merge(extra, on=['session', 'onset_row'], how='left', validate='one_to_one')
    return minute, out


def non_overlap(events: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    z = events.loc[mask].copy().sort_values(['session', 'onset_row'])
    rows = []
    for _, g in z.groupby('session', sort=False):
        next_allowed = -1
        for _, r in g.iterrows():
            onset = int(r['onset_row'])
            if onset < next_allowed:
                continue
            rows.append(r)
            next_allowed = onset + 1 + HOLD_MIN
    return pd.DataFrame(rows)


def summarize(name: str, events: pd.DataFrame, mask: pd.Series) -> list[dict]:
    z = non_overlap(events, mask)
    rows = []
    for year in sorted(events['year'].unique()):
        q = z[z['year'].eq(year)]
        gross = pd.to_numeric(q['signed_3m_bp'], errors='coerce').dropna()
        rows.append({
            'subset': name,
            'year': int(year),
            'n': int(len(gross)),
            'mean_gross_3m_bp': float(gross.mean()) if len(gross) else np.nan,
            'mean_net_1bp_per_leg': float(gross.mean() - 2.0) if len(gross) else np.nan,
            'median_gross_3m_bp': float(gross.median()) if len(gross) else np.nan,
            'hit_rate': float((gross > 0).mean()) if len(gross) else np.nan,
        })
    gross = pd.to_numeric(z['signed_3m_bp'], errors='coerce').dropna()
    rows.append({
        'subset': name,
        'year': 'pooled',
        'n': int(len(gross)),
        'mean_gross_3m_bp': float(gross.mean()) if len(gross) else np.nan,
        'mean_net_1bp_per_leg': float(gross.mean() - 2.0) if len(gross) else np.nan,
        'median_gross_3m_bp': float(gross.median()) if len(gross) else np.nan,
        'hit_rate': float((gross > 0).mean()) if len(gross) else np.nan,
    })
    return rows


def run(root: Path, out: Path, start: str, end: str, role: str) -> None:
    _, e = build_panel(root, start, end)
    base = (
        e['direction'].eq('down')
        & (pd.to_numeric(e['slow30_net_bp'], errors='coerce') > 0)
        & (pd.to_numeric(e['net5_bp'], errors='coerce') < 0)
        & (pd.to_numeric(e['efficiency5'], errors='coerce') >= 0.60)
        & np.isfinite(pd.to_numeric(e['signed_3m_bp'], errors='coerce'))
    )
    abs_tail = pd.to_numeric(e['tail2_share'], errors='coerce') >= 0.50
    same = e['late2_same_direction'].eq(True)
    accel = pd.to_numeric(e['signed_accel_contrast_bp_per_min'], errors='coerce') > 0
    majority = e['late2_majority_of_net'].eq(True)

    subsets = {
        'base_down_break_eff60': base,
        'v2_abs_tail2_ge50': base & abs_tail,
        'signed_accel_only': base & same & accel,
        'signed_accel_plus_abs_tail2_ge50': base & abs_tail & same & accel,
        'signed_late2_majority_net': base & same & majority,
        'signed_accel_and_majority_net': base & same & accel & majority,
    }
    rows = []
    for name, mask in subsets.items():
        rows.extend(summarize(name, e, mask))

    diag = e.loc[base].copy()
    out.mkdir(parents=True, exist_ok=True)
    diag.to_csv(out / 'base_events_with_signed_accel.csv', index=False)
    pd.DataFrame(rows).to_csv(out / 'subset_summary.csv', index=False)
    meta = {
        'schema': 'star50_signed_acceleration_diagnostic_v1',
        'role': role,
        'start': start,
        'end': end,
        'diagnostic_only': True,
        'candidate_validation_claim': False,
        'blackbox_queried': False,
        'subsets': list(subsets),
    }
    (out / 'summary.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(pd.DataFrame(rows).to_csv(index=False))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--repo-root', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    p.add_argument('--role', required=True)
    a = p.parse_args()
    run(Path(a.repo_root).resolve(), Path(a.out).resolve(), a.start, a.end, a.role)


if __name__ == '__main__':
    main()
