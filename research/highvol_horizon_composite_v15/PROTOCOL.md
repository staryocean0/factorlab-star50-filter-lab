# HighVol recovery V15 — horizon-dependence Development adjudication

## Purpose

V14 frozen Validation rejected a joint `15m/30m/60m` state+age recovery surface because `current_state` added stable incremental information beyond recent-shock age at 15m and 30m but not at 60m. That Validation result may generate a new hypothesis, but it cannot itself promote selected horizons.

V15 therefore returns to Development and tests one fixed mechanism:

> the incremental value of `UNSAFE/RECOVERING` beyond recent-shock age is robust at short recovery horizons (15m and 30m) and has decayed to statistical uncertainty by 60m.

This is a risk-process study only. It creates no payoff, PnL, position, routing, stop, target, sizing, or trading rule.

## Frozen lineage and cohort

- Development years: 2021, 2022, 2023.
- 2020: warm-up/reference history only.
- Symbols: `000688.SH`, `000852.SH`.
- Cohort/state construction: exactly the V11 common-cohort recovery rows.
- Expected Development rows: `7327`.
- States: `UNSAFE`, `RECOVERING`.
- Recent-shock-age buckets: `LT15`, `M15_25`, `M30_40`, `GE45`.
- Horizons: `15m`, `30m`, `60m`.
- State thresholds and shock-reset clock are unchanged.

The V11 runner is materialized in CI from historical commit `30fda623af5c9461ffe60c4985e6150f01eec8f8` and must have Git blob SHA `713f0dcc41e7f32f75934fc7709a406ff71579e6`.

## Fixed models

For every leave-one-year-out fold and every horizon, fit only these two Laplace-smoothed lookup models on the other two Development years:

1. `age_only`: `recent_shock_age_bucket -> P(Normal within horizon)`;
2. `state_plus_age`: `(current_state, recent_shock_age_bucket) -> P(Normal within horizon)`.

No refit family, threshold menu, interaction search, horizon search, or feature search is allowed.

## Fixed out-of-fold comparison

For each held-out row define paired Brier improvement:

`delta = (p_age_only - y)^2 - (p_state_plus_age - y)^2`.

Positive `delta` means `current_state` adds predictive value beyond age.

All uncertainty is computed from the pooled out-of-fold predictions using a **trading-day clustered paired bootstrap**:

- cluster key: `trading_day` (both indices on the same date remain in the same cluster);
- repetitions: `10000`;
- RNG seed: `20260910`;
- percentile interval: `2.5% / 97.5%`.

Days are sampled with replacement; within a sampled day all rows are retained. No bootstrap setting may be changed after results are seen.

## Frozen Development support rule

The horizon-dependence hypothesis is supported only if all are true:

1. row count is exactly `7327`;
2. every state×age training cell used in LOYO has `n >= 50`;
3. at 15m, pooled Brier-improvement bootstrap 95% CI lower bound is `> 0`;
4. at 30m, pooled Brier-improvement bootstrap 95% CI lower bound is `> 0`;
5. at 60m, the pooled Brier-improvement bootstrap 95% CI **contains 0**;
6. state+age beats age-only in annual held-out Brier in at least 2 of 3 Development years at 15m;
7. the same annual condition holds at 30m;
8. state thresholds, age buckets, horizons, cohort, and shock-reset clock are unchanged;
9. Validation is not queried in V15;
10. BlackBox is not queried;
11. no PnL or trading rule is created.

A failure cannot be rescued by changing the bootstrap, dropping a year, choosing another horizon, or changing age/state definitions.

## Interpretation boundary

A PASS does **not** itself define the final multi-horizon probability surface. It only authorizes a separate Development construction of a deterministic horizon-adaptive object. Any such later object must preserve cumulative probability monotonicity before it can be frozen for Validation.

V14 Validation values are provenance for the hypothesis only and are not inputs to V15 estimation or scoring.

`production_authority=false`.
