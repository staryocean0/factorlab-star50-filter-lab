# HighVol / Unsafe recovery dynamics v2

## Scope

- Continues the current cross-index K-line risk-state mainline.
- Inherits every HighVol/Unsafe threshold from v1 unchanged; no threshold search or retuning.
- Shock-triggered episodes are de-overlapped; recurrent shocks before Normal remain inside the same episode.
- Common trading days: 1322 (2020-07-23 to 2025-12-31).
- Historical consumed development evidence only; fresh_oos=false; no 2026, BLACKBOX, PnL, or trading authority.

## Pooled episode dynamics

| metric | 000688.SH | 000852.SH |
|---|---:|---:|
| shock-triggered Unsafe episodes | 790 | 766 |
| same-session Normal recovery | 96.08% | 95.30% |
| recurrent shock before Normal | 16.71% | 16.19% |
| median bars to Normal (recovered only) | 12.00 | 12.00 |
| p90 bars to Normal (recovered only) | 17.00 | 16.00 |
| median bars to leave Unsafe | 1.00 | 1.00 |
| session censor fraction | 3.92% | 4.70% |
| not Normal by 60m among observable/recovered | 35.42% | 29.89% |
| median episode peak vol ratio | 1.512 | 1.477 |

## Interpretation rule

Cross-index pooled differences are accompanied by calendar-year direction counts in `cross_index_direction_summary.csv`. No new binary promotion gate is created here. A difference is treated as descriptive unless its direction is visible across annual rows as well.

The migrated RMR material is used only as a guardrail: state/mechanism evidence is not converted into a payoff or trading rule in this diagnostic.

`production_authority=false`.
