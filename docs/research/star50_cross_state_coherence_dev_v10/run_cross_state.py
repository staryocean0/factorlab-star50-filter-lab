from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START = '2021-01-01'
END = '2023-12-31'
YEARS = (2021, 2022, 2023)
CODES = ('000688.SH', '000852.SH')
CELL_ORDER = (
    'star_high|csi_high',
    'star_high|csi_normal',
    'star_normal|csi_high',
    'star_normal|csi_normal',
)
RELATIONS = ('all', 'same', 'opposite')


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_minute(root: Path, code: str) -> pd.DataFrame:
    reg = load_module(
        root / 'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py',
        f'v10_reg_{code.replace(".", "_")}',
    )
    orig = load_module(
        root / 'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py',
        f'v10_orig_{code.replace(".", "_")}',
    )
    fg = load_module(
        root / 'docs/research/state_conditioned_frequency_v2/code/fast_grid.py',
        f'v10_fg_{code.replace(".", "_")}',
    )
    native = orig.load_native(root, code).copy()
    native['trading_day'] = native.trading_day.astype(str).str[:10]
    # 2020 is allowed only as warm-up.  Nothing after Development is loaded.
    native = native[native.trading_day <= END].copy()
    state = reg.build_continuous_state(native, code)
    minute = fg.build_minute_grid(
        native,
        state.rename(columns={'vol_ratio': 'recovery_ratio'}),
        code,
    ).reset_index(drop=True)
    minute['trading_day'] = minute.trading_day.astype(str).str[:10]
    return minute[(minute.trading_day >= START) & (minute.trading_day <= END)].reset_index(drop=True)


def prepare_index(minute: pd.DataFrame, prefix: str) -> pd.DataFrame:
    rows = []
    for session, z0 in minute.groupby('session', sort=False):
        z = z0.sort_values('minute').reset_index(drop=True)
        close = z.close.to_numpy(float)
        opened = z.open.to_numpy(float)
        valid = z.valid.to_numpy(bool)
        r = np.full(len(z), np.nan)
        for i in range(1, len(z)):
            if (
                valid[i] and valid[i - 1]
                and np.isfinite(close[i]) and np.isfinite(close[i - 1])
                and close[i] > 0 and close[i - 1] > 0
            ):
                r[i] = np.log(close[i] / close[i - 1]) * 1e4
        for i in range(len(z)):
            recent = r[i - 4:i + 1] if i >= 4 else np.array([])
            net5 = float(recent.sum()) if len(recent) == 5 and np.isfinite(recent).all() else np.nan
            rows.append({
                'trading_day': str(z.trading_day.iloc[i]),
                'year': int(z.year.iloc[i]),
                'session': str(session),
                'minute': int(z.minute.iloc[i]),
                f'{prefix}_state': str(z.route_state.iloc[i]),
                f'{prefix}_net5_bp': net5,
                f'{prefix}_open': float(opened[i]) if np.isfinite(opened[i]) else np.nan,
                f'{prefix}_valid': bool(valid[i]),
            })
    return pd.DataFrame(rows)


def state_bit(state: str, high: str, normal: str) -> str | None:
    if state == 'HighVol':
        return high
    if state == 'NormalVol':
        return normal
    return None


def build_events(star: pd.DataFrame, csi: pd.DataFrame) -> pd.DataFrame:
    keys = ['trading_day', 'year', 'session', 'minute']
    x = star.merge(csi, on=keys, how='inner', validate='one_to_one')
    x = x.sort_values(['session', 'minute']).reset_index(drop=True)
    rows = []
    for session, z0 in x.groupby('session', sort=False):
        z = z0.sort_values('minute').reset_index(drop=True)
        star_open = z.star_open.to_numpy(float)
        star_valid = z.star_valid.to_numpy(bool)
        previous_cell = None
        for i, row in enumerate(z.itertuples()):
            sb = state_bit(row.star_state, 'star_high', 'star_normal')
            cb = state_bit(row.csi_state, 'csi_high', 'csi_normal')
            cell = f'{sb}|{cb}' if sb is not None and cb is not None else None
            entered = cell is not None and cell != previous_cell
            previous_cell = cell
            if not entered:
                continue
            if not (np.isfinite(row.star_net5_bp) and np.isfinite(row.csi_net5_bp)):
                continue
            ssign = 1 if row.star_net5_bp > 0 else (-1 if row.star_net5_bp < 0 else 0)
            csign = 1 if row.csi_net5_bp > 0 else (-1 if row.csi_net5_bp < 0 else 0)
            if ssign == 0 or csign == 0:
                continue
            en = i + 1
            ex = en + 3
            if ex >= len(z):
                continue
            if not star_valid[en:ex + 1].all():
                continue
            if not (
                np.isfinite(star_open[en]) and np.isfinite(star_open[ex])
                and star_open[en] > 0 and star_open[ex] > 0
            ):
                continue
            raw = float(np.log(star_open[ex] / star_open[en]) * 1e4)
            continuation = float(ssign * raw)
            relation = 'same' if ssign == csign else 'opposite'
            rows.append({
                'year': int(row.year),
                'trading_day': str(row.trading_day),
                'session': str(session),
                'minute': int(row.minute),
                'cell': cell,
                'direction_relation': relation,
                'star_net5_bp': float(row.star_net5_bp),
                'csi_net5_bp': float(row.csi_net5_bp),
                'star_recent_direction': 'up' if ssign > 0 else 'down',
                'csi_recent_direction': 'up' if csign > 0 else 'down',
                'star_future_raw_3m_bp': raw,
                'star_continuation_3m_bp': continuation,
                'star_reversal_3m_bp': -continuation,
                'star_abs_3m_displacement_bp': abs(raw),
            })
    return pd.DataFrame(rows)


def stats(z: pd.DataFrame) -> dict:
    c = pd.to_numeric(z.star_continuation_3m_bp, errors='coerce').dropna()
    r = pd.to_numeric(z.star_reversal_3m_bp, errors='coerce').dropna()
    raw = pd.to_numeric(z.star_future_raw_3m_bp, errors='coerce').dropna()
    a = pd.to_numeric(z.star_abs_3m_displacement_bp, errors='coerce').dropna()
    n = len(c)
    mc = float(c.mean()) if n else np.nan
    mr = float(r.mean()) if n else np.nan
    return {
        'n': int(n),
        'mean_raw_3m_bp': float(raw.mean()) if len(raw) else np.nan,
        'mean_continuation_3m_bp': mc,
        'median_continuation_3m_bp': float(c.median()) if n else np.nan,
        'continuation_hit': float((c > 0).mean()) if n else np.nan,
        'continuation_net_1bp_per_leg': mc - 2 if n else np.nan,
        'continuation_one_way_break_even_bp': mc / 2 if n else np.nan,
        'mean_reversal_3m_bp': mr,
        'reversal_net_1bp_per_leg': mr - 2 if n else np.nan,
        'reversal_one_way_break_even_bp': mr / 2 if n else np.nan,
        'mean_abs_3m_displacement_bp': float(a.mean()) if len(a) else np.nan,
    }


def run(root: Path, out: Path):
    star = prepare_index(build_minute(root, CODES[0]), 'star')
    csi = prepare_index(build_minute(root, CODES[1]), 'csi')
    events = build_events(star, csi)
    rows = []
    promising = []
    for cell in CELL_ORDER:
        base = events[events.cell == cell]
        for relation in RELATIONS:
            z = base if relation == 'all' else base[base.direction_relation == relation]
            annual = []
            for year in YEARS:
                q = stats(z[z.year == year])
                annual.append(q)
                rows.append({'cell': cell, 'relation': relation, 'year': year, **q})
            pooled = stats(z)
            rows.append({'cell': cell, 'relation': relation, 'year': 'pooled', **pooled})
            a = pd.DataFrame(annual)
            if len(a) == 3 and bool((a.n >= 15).all()):
                cont = bool((a.continuation_net_1bp_per_leg > 0).all())
                rev = bool((a.reversal_net_1bp_per_leg > 0).all())
                if cont or rev:
                    promising.append({
                        'cell': cell,
                        'relation': relation,
                        'direction': 'continuation' if cont else 'reversal',
                    })
    summary = {
        'schema': 'star50_cross_state_coherence_dev_v10',
        'development_only': True,
        'validation_queried': False,
        'blackbox_queried': False,
        'candidate_nominated': False,
        'matrix_cells': len(CELL_ORDER),
        'cell_order': list(CELL_ORDER),
        'relations': list(RELATIONS),
        'event_count': int(len(events)),
        'mechanism_promising_views': promising,
    }
    out.mkdir(parents=True, exist_ok=True)
    events.to_csv(out / 'events.csv', index=False)
    pd.DataFrame(rows).to_csv(out / 'summary.csv', index=False)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))
    print(pd.DataFrame(rows).to_csv(index=False))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo-root', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    run(Path(a.repo_root).resolve(), Path(a.out))


if __name__ == '__main__':
    main()
