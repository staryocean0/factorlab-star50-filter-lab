# HighVol recovery survival V11 — Development result

## Decision

**NOT ELIGIBLE FOR VALIDATION.**

The coherent fixed 15m / 30m / 60m recovery object failed one preregistered structural gate: `RECOVERING > UNSAFE` did not hold at the 60-minute horizon. No horizon is dropped and no threshold or age bucket is changed post hoc.

Development run: `34450053409`  
Execution head: `325363f6ebd25c284fcf9333cce61e84eb76e22e`  
Artifact: `10141174485`  
Artifact SHA256: `69b486865b89d92c4ac210f6d684af7c221b79f0dbaf39668044d4ae76ff7286`

`validation_queried=false`  
`blackbox_queried=false`  
`production_authority=false`

## Sample

- 7,327 Development active-risk observations with a full 60 trading minutes of same-day future support.
- The same rows are used for 15m / 30m / 60m outcomes.
- All 8 state × recent-shock-age base cells have `n >= 100`.
- Every cell obeys cumulative monotonicity `P15 <= P30 <= P60`.

## Frozen probability table

| recent-shock age | state | n | P(Normal<=15m) | P(Normal<=30m) | P(Normal<=60m) |
|---|---|---:|---:|---:|---:|
| <15m | UNSAFE | 275 | 0.0072 | 0.0325 | 0.7978 |
| <15m | RECOVERING | 1,170 | 0.0478 | 0.0828 | 0.6997 |
| 15-25m | UNSAFE | 507 | 0.0079 | 0.0550 | 0.9077 |
| 15-25m | RECOVERING | 1,427 | 0.0448 | 0.1029 | 0.8488 |
| 30-40m | UNSAFE | 585 | 0.0136 | 0.6252 | 0.9659 |
| 30-40m | RECOVERING | 1,171 | 0.0853 | 0.7690 | 0.9327 |
| >=45m | UNSAFE | 465 | 0.5246 | 0.8244 | 0.9829 |
| >=45m | RECOVERING | 1,727 | 0.7501 | 0.9098 | 0.9786 |

At 15m and 30m, `RECOVERING` has higher cumulative normalization probability in all four fixed age buckets. At 60m the ordering reverses in all four buckets, with `UNSAFE` having the higher cumulative normalization probability.

## Predictive information remains real

Leave-one-year-out pooled model vs fold-specific global-rate baseline:

| horizon | model Brier | baseline Brier | improvement | model LogLoss | baseline LogLoss | improvement |
|---|---:|---:|---:|---:|---:|---:|
| 15m | 0.08952 | 0.18309 | +0.09357 | 0.30044 | 0.55262 | +0.25218 |
| 30m | 0.11041 | 0.24956 | +0.13915 | 0.37156 | 0.69226 | +0.32070 |
| 60m | 0.08846 | 0.09804 | +0.00958 | 0.30005 | 0.34694 | +0.04689 |

Each of 2021, 2022 and 2023 individually had positive Brier improvement at all three horizons.

## Interpretation / next test

V11 rejects the assumption that `UNSAFE > RECOVERING` is a horizon-invariant ordinal severity ranking. The states are strongly ordered for near-term recovery, but the ordering crosses by 60 minutes.

A plausible structural mechanism is the fixed 12-bar realized-volatility window: a recent shock can keep a row `UNSAFE` in the short run yet mechanically leave the `rv12` window within the next hour, whereas a `RECOVERING` row can represent broader, more persistent elevated volatility. This explanation is not accepted from V11 alone.

The next Development-only test should therefore anchor time to the deterministic exit of the most recent shock from the 12-bar `rv12` window and ask whether the 60m crossover concentrates around that expiry. It must not tune state thresholds, horizons, or age buckets.
