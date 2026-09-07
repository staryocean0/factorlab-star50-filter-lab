"""Display-only derivatives of the frozen fifth-round results; no new tests."""
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from star50_filter.streak_mechanism import FEATURES, sequence_stats

OUT = ROOT/'artifacts/streak_mechanism_v1'
trades = pd.read_csv(OUT/'5m_offset_0/trades.csv')
trades = trades.loc[~trades.boundary_clipped]
rates = trades.assign(win=trades.outcome == 1).groupby('year').win.mean()
probabilities = trades.year.map(rates).to_numpy()
simulations = np.concatenate([np.load(OUT/'sessions'/str(y)/'trade_shuffle.npy')
                             for y in range(2021, 2026)], axis=1)
lengths = sequence_stats(simulations, probabilities)[:, 0]
observed = sequence_stats(trades.outcome.to_numpy(), probabilities)[0, 0]
table = pd.read_csv(OUT/'5m_offset_0/stage_tests.csv')
fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), layout='constrained')
axes[0].hist(lengths, bins=np.arange(lengths.min()-.5, lengths.max()+1.5),
             color='#7394ae', edgecolor='white')
axes[0].axvline(observed, color='#ba5342', lw=2.2, label=f'Observed: {int(observed)} losses')
axes[0].axvline(np.median(lengths), color='#25394c', ls='--', label='Shuffled median: 15')
axes[0].set(xlabel='Longest losing run across all 3,482 trades', ylabel='Count / 1,999 shuffles',
            title='Observed losing streak is not unusually long')
axes[0].legend(fontsize=8)
names = ['Intraday efficiency', 'Fast variation share', 'Slow / work velocity', 'Threshold / work amplitude']
y = np.arange(4)
for shift, target, label, color in [(-.16, 'win_rate', 'Stage win rate', '#aaacb0'),
                                     (.16, 'mean_trade_log', 'Mean PnL per trade', '#337f8b')]:
    values = table.loc[table.outcome == target].set_index('feature').loc[FEATURES, 'rho']
    axes[1].barh(y+shift, values, height=.29, label=label, color=color)
axes[1].set_yticks(y, names)
axes[1].axvline(0, color='black', lw=.7)
axes[1].set(xlabel='Within-year centered rank correlation', title='Relationships are stronger for payoff size')
axes[1].invert_yaxis()
axes[1].legend(fontsize=8)
fig.suptitle('STAR50 fixed strategy | 2021–2025 consumed history | hindsight, not live rules', fontsize=12)
fig.savefig(OUT/'overview.png', dpi=150)
plt.close(fig)

stages = pd.read_csv(OUT/'5m_offset_0/stages.csv').query('eligible').copy()
rows = []
for name, a, b in [('eff_fast', FEATURES[0], FEATURES[1]), ('slow_threshold', FEATURES[2], FEATURES[3])]:
    labels = (stages[a] > stages[a].median()).astype(int).astype(str)+(stages[b] > stages[b].median()).astype(int).astype(str)
    for label, g in stages.groupby(labels):
        positive, negative = g[g.mean_trade_log > 0], g[g.mean_trade_log < 0]
        rows.append({'table': name, 'cell': label, 'stages': len(g), 'trades': int(g.n_trades.sum()),
                     'winning_trades': int(np.rint(g.n_trades*g.win_rate).sum()),
                     'earliest_profitable_counterexample_start': positive.iloc[0]['first'] if len(positive) else '',
                     'earliest_profitable_counterexample_end': positive.iloc[0]['last'] if len(positive) else '',
                     'earliest_losing_example_start': negative.iloc[0]['first'] if len(negative) else '',
                     'earliest_losing_example_end': negative.iloc[0]['last'] if len(negative) else ''})
pd.DataFrame(rows).to_csv(OUT/'condition_denominators_and_examples.csv', index=False)
print('Overview and cell denominators rendered from existing results')
