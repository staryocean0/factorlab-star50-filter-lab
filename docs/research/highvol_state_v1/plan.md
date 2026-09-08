# HighVol State Research v1

## Scope

Compare 000688.SH and 000852.SH 5m market states.

This phase is mechanism measurement only. No trading rule, parameter optimization, position sizing, or production routing.

## State definitions

Normal:
- baseline volatility state

HighVol:
- realized volatility elevated relative to rolling background volatility

ExtremeVol:
- extreme volatility persistence state

Unsafe:
- post-shock state where risk has not decayed

Recovering:
- volatility declining but not yet normalized

## Measurements

1. Volatility state frequency
2. State persistence length
3. Transition matrix
4. Shock to Unsafe transition
5. Unsafe to Recovering transition
6. Recovery failure probability

## Outputs

- HighVol_State_Comparison.csv
- Unsafe_Recovery_Transition.csv
- report.md
