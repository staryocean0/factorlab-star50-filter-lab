"""Additional attribution from completed snapshots, never new policy trials."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/three_proposals_v1'


def main():
    panels = {p: pd.concat([pd.read_parquet(OUT / str(y) / 'accounts' / (p + '.parquet'))
                            for y in range(2021, 2026)], ignore_index=True)
              for p in ['F', 'A', 'B', 'AB', 'C', 'AC', 'BC', 'ABC', 'channel_only']}
    base = pd.read_parquet(OUT / 'ledgers/F/trades.parquet')
    complete = base.loc[base.complete.astype(bool) & ~base.left_clipped.astype(bool)].copy()
    ix = complete.entry_index.to_numpy(int)
    a = panels['A'].filled_position.to_numpy()[ix] == 0
    b = panels['B'].filled_position.to_numpy()[ix] == 0
    groups = []
    for name, selected in [('A_only', a & ~b), ('B_only_added_after_A', b & ~a),
                           ('A_and_B_overlap', a & b), ('neither', ~a & ~b)]:
        x = complete.loc[selected]
        groups.append({'bucket': name, 'count': len(x), 'net_log_sum': float(x.net_log.sum()),
            'mean_net_log_bp': float(x.net_log.mean() * 10000),
            'mean_gross_log_bp': float(x.gross_log.mean() * 10000),
            'warning': 'existing-family attribution only; no intersection policy or its MDD tested'})
    pd.DataFrame(groups).to_csv(OUT / 'veto_overlap_attribution.csv', index=False)
    decomposition = pd.read_csv(OUT / 'interval_decomposition.csv')
    comparison = pd.read_csv(OUT / 'comparison.csv')
    turns = comparison.loc[comparison.basis == 'uniform_fee_proxy'].set_index('policy').turnover_sides
    rows = []
    for p in ['A', 'B', 'AB']:
        g = decomposition.loc[decomposition.policy == p].iloc[0]
        delta_gross = g.delta_net_log - g.saved_fee_log
        saved_sides = int(turns['F'] - turns[p])
        threshold = float(1 - np.exp(delta_gross / saved_sides))
        rows.append({'policy': p, 'gross_log_delta': delta_gross, 'saved_turnover_sides': saved_sides,
            'break_even_fee_per_side_bp': threshold * 10000,
            'meaning': 'same signed-log index path fee sensitivity, not actual ETF/options pricing'})
    pd.DataFrame(rows).to_csv(OUT / 'fee_break_even.csv', index=False)
    quarterly = pd.read_csv(OUT / 'quarterly.csv')
    f = quarterly.loc[quarterly.policy == 'F'].set_index('quarter')
    stability = []
    for p in panels:
        q = quarterly.loc[quarterly.policy == p].set_index('quarter')
        difference = q.net_log - f.net_log
        affected = abs(np.expm1(q.net_log) - np.expm1(f.net_log)) >= .00025
        stability.append({'policy': p, 'quarters': len(q), 'positive_quarters': int((difference > 1e-12).sum()),
            'negative_quarters': int((difference < -1e-12).sum()),
            'affected_quarters': int(affected.sum()),
            'positive_affected_quarters': int(((difference > 0) & affected).sum()),
            'median_affected_log_delta': float(difference.loc[affected].median()) if affected.any() else 0.,
            'total_log_delta': float(difference.sum())})
    pd.DataFrame(stability).to_csv(OUT / 'quarterly_stability.csv', index=False)
    # Same ORIGINAL peak/trough endpoints, separate from each policy's own MDD.
    f = panels['F']
    trough = int(f.gross_drawdown.idxmax())
    peak = int(f.gross_nav.iloc[:trough + 1].idxmax())
    event = []
    for p, bars in panels.items():
        log_pnl = float(bars.gross_log.iloc[peak + 1:trough + 1].sum())
        event.append({'policy': p, 'original_peak_label': str(f.timestamp.iloc[peak]),
            'original_trough_label': str(f.timestamp.iloc[trough]),
            'window_gross_log': log_pnl, 'window_geometric_return': float(np.expm1(log_pnl)),
            'warning': 'fixed original window return, not this policy own maximum drawdown'})
    pd.DataFrame(event).to_csv(OUT / 'original_mdd_window.csv', index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), layout='constrained')
    menus = [['F', 'A', 'B', 'AB'], ['F', 'C', 'AC', 'BC', 'ABC']]
    for col, menu in enumerate(menus):
        for p in menu:
            x = panels[p].groupby('trading_day', sort=True).tail(1)
            for row, kind in enumerate(['gross', 'net']):
                axes[row, col].plot(pd.to_datetime(x.trading_day), x[kind + '_nav'], label=p)
                axes[row, col].set_yscale('log')
                axes[row, col].set_title(f'{kind}: original full-unit account, initial NAV=1')
                axes[row, col].grid(alpha=.2)
        axes[0, col].legend()
    fig.savefig(OUT / 'full_account_comparison.png', dpi=140)
    plt.close(fig)
    print(pd.DataFrame(groups).drop(columns='warning').to_string(index=False))
    print(pd.DataFrame(rows).drop(columns='meaning').to_string(index=False))
    print(pd.DataFrame(stability).to_string(index=False))


if __name__ == '__main__':
    main()
