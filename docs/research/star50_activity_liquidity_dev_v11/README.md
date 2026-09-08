# STAR50 activity/liquidity V11 — Development only

## Question

After V7–V10 failed to find a stable short-horizon routing edge from onset path shape, HighVol age, exit reversal, or cross-index state coherence, test a different economic state variable: **transaction activity**.

The hypothesis is not that HighVol itself predicts direction.  It is that a short-horizon module may only become economically meaningful when the HighVol onset is accompanied by unusually high contemporaneous turnover.

## Frozen Development diagnostic

Instrument: `000688.SH` (STAR50)

Data pool: 2021–2023 only, with 2020 permitted only as warm-up.

State event:

- `NormalVol -> HighVol`

Activity field:

- `amount` (not selected by performance; fixed because turnover amount is the direct monetary activity measure available in the native 1-minute data)

Causal activity ratio at the onset minute:

`activity_ratio = mean(amount over latest 5 minutes) / mean(amount over prior non-overlapping 30 minutes)`

Fixed activity states:

- `ElevatedActivity`: ratio >= 1.5
- `NormalActivity`: ratio < 1.5

Direction reference:

- sign of the latest 5 one-minute close-to-close returns

Execution diagnostic:

- decision at the HighVol onset minute
- enter next minute open
- fixed 3-minute holding period
- exit at the open three minutes after entry
- same half-session
- complete valid path only
- non-overlapping accepted events

Views:

- all valid onset events
- ElevatedActivity
- NormalActivity

For each view, report continuation and reversal relative to the latest-5-minute STAR50 direction, annual 2021/2022/2023 and pooled.

A view is only tagged `mechanism_promising` when every Development year has at least 15 trades and either continuation or reversal is positive after 1 bp per leg in all three years.  This tag is hypothesis generation only; it does **not** auto-promote a candidate.

## Governance

- Development only.
- Validation is not queried.
- BlackBox is not queried.
- No tail2, efficiency, slow30, shock-z, age, penetration, cross-index state, or threshold menu is added.
- `candidate_nominated=false` regardless of the result of this diagnostic.
