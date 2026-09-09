# HighVol state analysis v1

## Execution contract

- Common trading-day interval: 2020-07-23 to 2025-12-31
- Common trading days: 1322
- rv window: 12 bars
- background window: preceding 48 valid intraday 5m returns
- HighVol ratio threshold: 1.5
- ExtremeVol ratio threshold: 2.25
- Shock threshold: 3.0 sigma
- Overnight returns excluded; risk state resets each trading day.
- No trading rule, PnL optimization, position sizing, BLACKBOX, or 2026 data used.

## Pooled core measurements

| metric | 000688.SH | 000852.SH |
|---|---:|---:|
| eligible bars | 62086 | 62086 |
| HighVol+Extreme share | 3.932% | 3.102% |
| Extreme share | 0.021% | 0.019% |
| HighVol persistence | 68.036% | 65.245% |
| shock rate | 1.525% | 1.485% |
| recovery failure probability | 44.295% | 41.051% |

## Frozen structural adjudication

**similar_structure**

Rule fixed before observing outputs: at least two of four core metrics must have >=20% pooled symmetric relative gap and >=80% same-sign annual differences.

Automatic next-stage output: `next_stage_common_mechanism.csv`.

This is mechanism measurement, not a trading recommendation.
