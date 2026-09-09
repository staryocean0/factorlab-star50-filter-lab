# R5-C reusable validation adjudication — 2026-09-08

Research identity: `rmr_event_density_state_reversal_v2`

Data policy: reusable DEV / VALIDATION / BLACKBOX.

## Frozen dedicated comparison

R5-C was not re-tested against severity alone. The dedicated baseline was strengthened to nearby event geometry:

`severity + completed_wave_duration_bars + bars_since_prev_confirmation`

The only added candidate feature was:

`event_density_z`

with the representation frozen as:

- same-scale confirmations in trailing 240 observed 1m bars / 240;
- preceding 100 same-scale observations for median/MAD normalization;
- current observation excluded;
- S1 and S2 co-primary;
- no window search, no scale search, no interactions, no PnL.

## VALIDATION result

### S1

- DEV resolved: 5,322
- VALIDATION resolved: 3,882
- geometry baseline Brier: `0.2501765347`
- augmented Brier: `0.2499595980`
- Brier improvement: `0.0002169367`
- geometry baseline log-loss: `0.6935177247`
- augmented log-loss: `0.6930794657`
- log-loss improvement: `0.0004382590`
- annual Brier improvement positive in 2021, 2022, 2023 and 2025; negative in 2024
- annual direction gate: 4/5 PASS
- fitted DEV event-density-z coefficient: `+0.0920`

### S2

- DEV resolved: 1,941
- VALIDATION resolved: 1,348
- geometry baseline Brier: `0.2502597258`
- augmented Brier: `0.2493310010`
- Brier improvement: `0.0009287248`
- geometry baseline log-loss: `0.6937171489`
- augmented log-loss: `0.6918026458`
- log-loss improvement: `0.0019145031`
- annual Brier improvement positive in all 2021–2025 years
- annual direction gate: 5/5 PASS
- fitted DEV event-density-z coefficient: `+0.0912`

Both scales passed every preregistered detailed VALIDATION gate. Therefore the predeclared DEV+VALIDATION final refit was allowed and frozen before BLACKBOX.

Final parameter bundle SHA256:

`36e40c3b209f3179dd0d9612af3396277cf96af0513c259a6090e39a2306fc7a`

## BLACKBOX boundary

This document intentionally contains **no BLACKBOX metric, count, subperiod, event, probability or failure detail**. The reusable BLACKBOX decision is recorded separately as a low-bandwidth three-state receipt.

The detailed VALIDATION PASS establishes that event density adds small but stable information beyond nearby event geometry on 2021–2025. It does not override a later BLACKBOX certification result.

Production authority: false.
