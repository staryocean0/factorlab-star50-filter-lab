"""One bounded post-hoc audit of existing original-account snapshots."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/apr_sep_2025_morphology'
START, END = '2025-04-01', '2025-09-30'


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def top_share(values, n=2):
    x = np.asarray(values, float)
    return float(np.sort(x)[-n:].sum() / x.sum()) if x.sum() > 1e-12 else None


def main():
    OUT.mkdir(exist_ok=True)
    source = ROOT / 'artifacts/streak_mechanism_v1/5m_offset_0/bars.parquet'
    account = ROOT / 'artifacts/three_proposals_v1/2025/accounts/F.parquet'
    marker = ROOT / 'artifacts/drawdown_material/5m_offset_0.parquet'
    accepted = json.loads((ROOT / 'artifacts/streak_mechanism_v1/manifest.json').read_text())['files']
    accounts = json.loads((ROOT / 'artifacts/three_proposals_v1/delivery_manifest.json').read_text())['files']
    assert sha(source) == accepted[str(source.relative_to(ROOT))]
    assert sha(account) == accounts[str(account.relative_to(ROOT))]
    receipt = json.loads((ROOT / 'artifacts/drawdown_material/receipt.json').read_text())
    expected = next(x['export_sha256'] for x in receipt['views'] if x['view_id'] == '5m_offset_0')
    assert sha(marker) == expected
    save('data_usage.json', {'role': 'repeat_audit_of_consumed_2025', 'start': START, 'end': END,
        '2020_first_close': 'original_filter_level_display_only', 'new_strategy_or_account_runs': 0,
        'input_hashes': {str(p.relative_to(ROOT)): sha(p) for p in [source, account, marker]},
        'method_sha256': sha(ROOT / 'docs/research/apr_sep_2025_morphology/method.md'),
        'source_sha256': sha(Path(__file__)), 'data_2026_used': False, 'production_authority': False})
    raw = pd.read_parquet(source, filters=[('year', '==', 2025)]).reset_index(drop=True)
    acc = pd.read_parquet(account)
    assert np.array_equal(raw.pnl_log, acc.gross_log)
    assert np.array_equal(raw.exec_pos, acc.exec_pos)
    assert np.array_equal(raw.timestamp, acc.timestamp)
    body = np.log(raw.close.shift(1) / raw.open.shift(1))
    gap = np.log(raw.open / raw.close.shift(1))
    market = np.log(raw.open / raw.open.shift(1))
    assert np.max(abs((body + gap - market).iloc[1:])) < 1e-12
    rows = []
    for day, g in raw.loc[raw.trading_day.between(START, END)].groupby('trading_day', sort=True):
        assert len(g) == 48
        for slot in range(4):
            ix = g.index.to_numpy()[slot * 12:(slot + 1) * 12]
            r, b, h = market.iloc[ix].to_numpy(), body.iloc[ix].to_numpy(), gap.iloc[ix].to_numpy()
            p = raw.exec_pos.iloc[ix].to_numpy()
            gross = float((p * r).sum())
            assert abs(gross - raw.pnl_log.iloc[ix].sum()) < 1e-12
            body_total, gap_total = float(abs(b).sum()), float(abs(h).sum())
            two_body = top_share(abs(b))
            two_return = top_share(abs(r))
            large = np.sort(abs(b))[-2:]
            remainder = np.sort(abs(b))[:-2]
            body_dom = bool(body_total >= gap_total)
            pattern = bool(two_body is not None and two_body >= .5
                           and two_return is not None and two_return >= .5 and body_dom)
            rows.append({'day': day, 'slot': slot, 'first_index': int(ix[0]), 'last_index': int(ix[-1]),
                'first_booking': str(raw.timestamp.iloc[ix[0]]), 'last_booking': str(raw.timestamp.iloc[ix[-1]]),
                'first_body_label': str(raw.timestamp.iloc[ix[0] - 1]),
                'gross_log': gross, 'net_proxy_log': float(acc.net_log.iloc[ix].sum()),
                'price_abs_log': float(abs(r).sum()), 'body_abs_log': body_total, 'gap_abs_log': gap_total,
                'top1_price_share': top_share(abs(r), 1), 'top2_price_share': two_return,
                'top2_body_share': two_body, 'up_top2_share': top_share(np.maximum(r, 0)),
                'down_top2_share': top_share(np.maximum(-r, 0)),
                'other10_body_median_over_top2_mean': float(np.median(remainder) / large.mean()) if large.mean() else None,
                'body_dominated': body_dom, 'large_body_pattern': pattern,
                'body_pnl_log': float((p * b).sum()), 'gap_pnl_log': float((p * h).sum()),
                'overnight_gap_abs_log': float(abs(h[raw.trading_day.iloc[ix].to_numpy() != raw.trading_day.shift().iloc[ix].to_numpy()]).sum())})
    f = pd.DataFrame(rows)
    f.to_csv(OUT / 'windows.csv', index=False)
    assert abs(f.gross_log.sum() - raw.loc[raw.trading_day.between(START, END), 'pnl_log'].sum()) < 1e-12
    summaries = []
    for region, sub in [('apr_sep', f), ('original_september_drawdown',
        f.loc[(f.first_booking > '2025-09-12 09:50:00') & (f.last_booking <= '2025-09-26 13:55:00')])]:
        for outcome, x in [('loss', sub.loc[sub.gross_log < -1e-12]),
                            ('profit', sub.loc[sub.gross_log > 1e-12])]:
            shape = x.large_body_pattern
            concentrated = x.top2_price_share >= .5
            body_concentrated = x.top2_body_share >= .5
            summaries.append({'region': region, 'outcome': outcome, 'windows': len(x),
                'top2_price_majority_count': int(concentrated.sum()),
                'top2_body_majority_count': int(body_concentrated.sum()),
                'large_body_pattern_count': int(shape.sum()),
                'large_body_pattern_fraction': float(shape.mean()) if len(x) else None,
                'median_top2_price_share': float(x.top2_price_share.median()) if len(x) else None,
                'median_top2_body_share': float(x.top2_body_share.median()) if len(x) else None,
                'net_gross_log': float(x.gross_log.sum()),
                'pattern_gross_log': float(x.loc[shape, 'gross_log'].sum()),
                'pattern_negative_or_positive_amount_share': float(x.loc[shape, 'gross_log'].sum() / x.gross_log.sum()) if len(x) else None})
    save('summary.json', {'groups': summaries,
        'fee_only_losing_windows': int(((f.gross_log >= 0) & (f.net_proxy_log < 0)).sum()),
        'whole_range_gross_return': float(np.expm1(f.gross_log.sum())),
        'whole_range_net_proxy_return': float(np.expm1(f.net_proxy_log.sum())),
        'interpretation': 'post-hoc window accounting, not a causal explanation fraction or prediction test'})
    examples = []
    for name, condition in [('large_body_loss', f.large_body_pattern),
                             ('other_loss', ~f.large_body_pattern),
                             ('gap_dominated_loss', (f.top2_price_share >= .5) & ~f.body_dominated)]:
        x = f.loc[condition & (f.gross_log < 0)]
        if len(x):
            row = x.loc[x.gross_log.idxmin()].to_dict()
            row['example'] = name
            examples.append(row)
    reference = next((x for x in examples if x['example'] == 'large_body_loss'), None)
    if reference:
        x = f.loc[f.large_body_pattern & (f.gross_log > 0)].copy()
        x['distance'] = abs(np.log(x.price_abs_log / reference['price_abs_log']))
        x = x.loc[x.distance <= np.log(1.25)]
        if len(x):
            row = x.loc[x.distance.idxmin()].drop('distance').to_dict()
            row['example'] = 'same_shape_matched_profit'
            examples.append(row)
    save('examples.json', examples)
    original_first = pd.read_parquet(marker, filters=[('trading_day', '==', '2020-07-23')],
                                     columns=['timestamp', 'close']).sort_values('timestamp').close.iloc[0]
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, axes = plt.subplots(2, len(examples), figsize=(4.5 * len(examples), 6), squeeze=False, layout='constrained')
    for col, ex in enumerate(examples):
        ix = np.arange(int(ex['first_index']), int(ex['last_index']) + 1)
        candles = raw.iloc[ix - 1]
        ref = float(candles.open.iloc[0])
        for k, candle in enumerate(candles.itertuples()):
            o, hi, lo, c = 10000 * np.log(np.array([candle.open, candle.high, candle.low, candle.close]) / ref)
            color = '#c84b57' if c >= o else '#238b75'
            axes[0, col].vlines(k, lo, hi, color=color, lw=1)
            axes[0, col].add_patch(Rectangle((k - .25, min(o, c)), .5, max(abs(c - o), .1), color=color, alpha=.65))
        filtered = 10000 * (candles.lowpass.to_numpy() + np.log(original_first) - np.log(ref))
        axes[0, col].plot(np.arange(12), filtered, label='original causal LP12', lw=1.3)
        axes[0, col].scatter(np.arange(12) + .35, 10000 * np.log(raw.open.iloc[ix].to_numpy() / ref),
                             marker='.', color='black', label='next open')
        axes[0, col].set_title(f"{ex['example']}\n{ex['first_booking'][:16]} | top2 bodies {ex['top2_body_share']:.1%}", fontsize=9)
        axes[0, col].legend(fontsize=7)
        axes[1, col].bar(np.arange(12), raw.pnl_log.iloc[ix].to_numpy() * 10000, alpha=.5)
        axes[1, col].plot(np.arange(12), raw.pnl_log.iloc[ix].cumsum().to_numpy() * 10000, label='cumulative PnL bp')
        secondary = axes[1, col].twinx()
        secondary.step(np.arange(12), raw.exec_pos.iloc[ix], color='grey', alpha=.4)
        secondary.set_ylim(-1.3, 1.3)
        axes[1, col].set_xlabel('12 original open-to-open intervals; candle i-1 + next open i')
    fig.suptitle('2025 April–September | unchanged original full-position strategy | retrospective examples')
    fig.savefig(OUT / 'examples.png', dpi=135)
    plt.close(fig)
    save('validation.json', {'original_pnl_and_position_unchanged': True,
        'body_plus_gap_market_identity_passed': True, 'window_accounting_reconciled': True,
        'new_account_replays': 0, 'observations': len(f), 'data_2026_used': False,
        'files': {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'validation.json'}})
    print(pd.DataFrame(summaries).to_string(index=False))
    print(pd.DataFrame(examples)[['example', 'first_booking', 'last_booking', 'gross_log',
        'top2_price_share', 'top2_body_share', 'body_abs_log', 'gap_abs_log',
        'other10_body_median_over_top2_mean']].to_string(index=False))


if __name__ == '__main__':
    main()
