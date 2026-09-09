# R2 range-integrity v2 validation adjudication — 2026-09-08

Research identity: `rmr_range_boundary_parent_integrity_v2`

## Dedicated question

After controlling for attempted-breakout geometry, speed and local volatility, does an intact parent range add information about first re-entry versus continuation?

Frozen geometry baseline:

`outside_ratio + break_speed + local_vol_ratio`

Only added feature:

`range_integrity = (-z(abs_drift) + z(overlap) - z(parent_eff)) / 3`

The original broad R2 event/outcome engine and fixed S1/S2/S3 directional-change thresholds were retained unchanged.

## VALIDATION result

### PAIR_A — S1 outside S2

- DEV resolved: 2,441
- VALIDATION resolved: 2,064
- baseline Brier: `0.1763423591`
- augmented Brier: `0.1747020760`
- Brier improvement: `0.0016402832`
- baseline log-loss: `0.5355170456`
- augmented log-loss: `0.5310170155`
- log-loss improvement: `0.0045000300`
- DEV range-integrity coefficient: `+0.24009`
- annual Brier improvement positive in 2022, 2023, 2024 and 2025; negative in 2021
- annual direction gate: 4/5 PASS

### PAIR_B — S2 outside S3

- DEV resolved: 1,161
- VALIDATION resolved: 988
- baseline Brier: `0.1353216507`
- augmented Brier: `0.1337996323`
- Brier improvement: `0.0015220184`
- baseline log-loss: `0.4376522845`
- augmented log-loss: `0.4332160530`
- log-loss improvement: `0.0044362315`
- DEV range-integrity coefficient: `+0.21378`
- annual Brier improvement positive in 2021, 2022, 2023 and 2025; negative in 2024
- annual direction gate: 4/5 PASS

Both co-primary pairings passed every preregistered detailed VALIDATION gate, including sample supply, pooled Brier/log-loss improvement, annual stability and positive mechanistic sign.

Therefore the predeclared one-time DEV+VALIDATION final refit was allowed and frozen.

Final parameter bundle SHA256:

`08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`

## BLACKBOX boundary

This document deliberately contains no BLACKBOX metric, count, date, subperiod, event, probability or scale-specific recent result. The low-bandwidth certification result is recorded separately.

Production authority remains false.
