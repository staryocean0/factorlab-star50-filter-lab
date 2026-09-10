# HighVol horizon-specific state value V14 — Development protocol

Purpose: after V13 rejected a horizon-invariant ordinal interpretation of `UNSAFE/RECOVERING`, test whether current state still adds predictive information beyond recent-shock age at each fixed recovery horizon.

## Frozen data and labels
- 2020 warm-up; Development 2021–2023 only.
- Symbols: `000688.SH`, `000852.SH`.
- Reuse the V11 common cohort requiring a full 60 trading minutes of same-day support.
- Outcomes are unchanged: Normal within 15m, 30m, 60m.
- Recent-shock age buckets are unchanged: `<15m`, `15–25m`, `30–40m`, `>=45m`.
- State remains `UNSAFE` or `RECOVERING` under the unchanged V6 state machine.
- No PnL, payoff, routing, sizing, trading rule, Validation or BlackBox.

## Fixed model comparison
For each horizon compare two Beta(1,1)-smoothed lookup models under leave-one-year-out (LOYO):

A. `age_only`: four recent-shock-age buckets.
B. `state_plus_age`: eight cells = current state × recent-shock-age bucket.

For each held-out year, fit both tables using the other two Development years and score exactly the same held-out rows. Report Brier and LogLoss.

This is not a parameter search. The only question is whether the state label contributes incremental probability information after age is already known.

## Frozen support rule
`horizon_specific_state_value_supported=true` only if all are true:
1. pooled LOYO Brier for `state_plus_age` is lower than `age_only` at all 15/30/60m horizons;
2. pooled LOYO LogLoss for `state_plus_age` is lower than `age_only` at all three horizons;
3. at each horizon, `state_plus_age` has lower Brier in at least 2 of the 3 held-out years;
4. every state×age training cell has at least 50 observations in every LOYO training fold;
5. state thresholds, age buckets, sample cohort and horizons are unchanged;
6. Validation/BlackBox remain unqueried.

If supported, V14 may nominate a new **horizon-specific recovery surface** for a separately frozen Validation replay. It does not restore any horizon-invariant ordinal ordering requirement.

`production_authority=false`.
