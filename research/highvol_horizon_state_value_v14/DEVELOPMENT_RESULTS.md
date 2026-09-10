# V14 horizon-specific state value — Development results

Status: **SUPPORTED; freeze horizon-specific recovery surface for reusable Validation.**

Execution authority:

- branch: `research/highvol-horizon-specific-state-value-v14-20260910`
- execution commit: `a9223748933fc842a68865a3837e24f49f014691`
- Actions run: `34454169246`
- artifact: `10142758729`
- artifact SHA256: `129271138720dcf972345006ea7e938aed0356531d2fa2d872e2aaa8d06d7f9f`
- Development only: 2021–2023, 2020 warm-up
- common 60-minute-support cohort: 7,327 rows
- Validation queried: false
- BlackBox queried: false

## Fixed question

Does `current_state` (`UNSAFE` / `RECOVERING`) add probability information after recent-shock age bucket is already known, separately at fixed 15m / 30m / 60m horizons?

The fixed comparison was:

- age-only: 4 recent-shock-age buckets;
- state+age: 8 state×age cells;
- Beta(1,1) smoothing;
- leave-one-year-out across 2021/2022/2023;
- identical held-out rows for both models.

## Development result

State+age improved pooled LOYO Brier and LogLoss at every horizon:

| horizon | age-only Brier | state+age Brier | Brier improvement | age-only LogLoss | state+age LogLoss | LogLoss improvement |
|---|---:|---:|---:|---:|---:|---:|
| 15m | 0.09234152 | 0.08952055 | +0.00282097 | 0.30984859 | 0.30043919 | +0.00940940 |
| 30m | 0.11183274 | 0.11041093 | +0.00142181 | 0.37610404 | 0.37155641 | +0.00454763 |
| 60m | 0.08895077 | 0.08845929 | +0.00049147 | 0.30183008 | 0.30004758 | +0.00178249 |

For each of 15m, 30m and 60m, state+age also improved Brier in **all 3 held-out years**. The smallest state×age training cell in any LOYO fold had `n=166`, above the frozen minimum 50.

Therefore V13's horizon-dependent ordering does **not** mean the state label is redundant. The correct interpretation is:

> recent-shock age and current state jointly matter, but the mapping from state to recovery probability is horizon specific.

The 8-cell × 3-horizon table is frozen in `FROZEN_HORIZON_SURFACE.json`. No threshold, bucket, horizon or state definition may be changed before Validation.

`production_authority=false`.
