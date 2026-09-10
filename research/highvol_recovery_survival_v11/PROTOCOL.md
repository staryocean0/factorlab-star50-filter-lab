# HighVol recovery survival V11 — Development protocol

Purpose: extend the validated V6 shock-reset recovery object from a single 15-minute target to one coherent cumulative recovery curve at fixed trading-time horizons 15m / 30m / 60m.

This remains bottom-layer causal risk-state research only. No PnL, payoff, position, routing, stop/target, sizing, or trading variable is allowed.

## Inherited state machine

Unchanged from V6:

- symbols: `000688.SH`, `000852.SH`;
- 5m log return within trading day;
- `rv12 = std(last 12 valid 5m returns, ddof=0)`;
- `bg48 = std(previous 48 valid 5m returns, ddof=0)`;
- `shock = abs(ret_5m)/bg48 >= 3.0`;
- `UNSAFE` after shock, or while `vol_ratio >= 1.50`;
- `RECOVERING` while `1.10 < vol_ratio < 1.50` after an active risk episode;
- `NORMAL` once `vol_ratio <= 1.10`;
- every recurrent shock resets the recovery clock;
- recent-shock-age buckets: `<15m`, `15-25m`, `30-40m`, `>=45m`.

No state threshold or age boundary may change.

## Development boundary

- 2020: warm-up/reference history only;
- measured Development: 2021-2023;
- physical checkout contains no 2024+ data;
- Validation and BlackBox are not queried.

## Coherent survival sample

Use active-risk observations only (`UNSAFE` or `RECOVERING`) after the most recent shock and before the first return to `NORMAL`.

A row is eligible only when the same trading day contains a full 12 subsequent 5m bars (60 trading minutes). The exact same eligible rows are therefore used for all three horizons.

For each eligible row define nested outcomes:

- `normal_within_15m`: at least one `NORMAL` state in the next 3 bars;
- `normal_within_30m`: at least one `NORMAL` state in the next 6 bars;
- `normal_within_60m`: at least one `NORMAL` state in the next 12 bars.

By construction these events are nested for every row.

## Probability object

For each of the 8 fixed cells

`current_state {UNSAFE, RECOVERING} × recent_shock_age {LT15, M15_25, M30_40, GE45}`

estimate each cumulative recovery probability with Beta(1,1) / Laplace smoothing:

`p_h = (success_h + 1) / (n + 2)`

for `h in {15,30,60}`.

No model family, smoothing strength, state, age bucket, or horizon is searched.

## Development evaluation

Use leave-one-year-out folds over 2021 / 2022 / 2023. In each fold:

- fit the 8-cell table on the other two years;
- score the held-out year at all three horizons;
- compare against a horizon-specific training-fold global-rate baseline using the same Beta(1,1) smoothing;
- report Brier and LogLoss.

## Frozen support rule

V11 is eligible for separate reusable Validation only if all are true:

1. all 8 final Development base cells have `n >= 100`;
2. every cell satisfies `P15 <= P30 <= P60`;
3. for every age bucket and every horizon, `P(recovery | RECOVERING) > P(recovery | UNSAFE)`;
4. for each of 15m / 30m / 60m, pooled leave-one-year-out Brier improves versus its fold-specific global-rate baseline;
5. for each horizon, at least 2 of 3 held-out years improve Brier versus baseline;
6. for each horizon, pooled leave-one-year-out LogLoss improves versus baseline;
7. inherited thresholds and age buckets are unchanged;
8. no Validation, BlackBox, PnL, payoff or trading rule is used.

Failure of any horizon fails the coherent object; horizons cannot be dropped post hoc.

`production_authority=false`.
