# HighVol recovery survival V11 — frozen Development protocol

Purpose: extend the validated V6 shock-reset recovery object from a single `P(NORMAL within next 15m)` target to one coherent cumulative recovery curve at fixed horizons `15m / 30m / 60m`. This is risk-state measurement only; no PnL, payoff, routing, position, or trading rule is created.

## Data boundary

- 2020 native 5m is warm-up only.
- Development measured years are 2021–2023.
- Symbols are `000688.SH` and `000852.SH` on common trading days.
- Physical checkout excludes 2024+, Validation, and BlackBox.

## Inherited state machine

Unchanged from the validated V6 line:

- 5m log return within trading day;
- `rv12 = std(last 12 valid 5m returns, ddof=0)`;
- `bg48 = std(previous 48 valid 5m returns, ddof=0)`;
- `shock = abs(ret_5m)/bg48 >= 3.0`;
- `UNSAFE` after shock, or while `vol_ratio=rv12/bg48 >= 1.50`;
- `RECOVERING` while `1.10 < vol_ratio < 1.50` after an active risk episode;
- `NORMAL` once `vol_ratio <= 1.10`;
- every new shock resets the recovery clock.

No state threshold or episode rule may change.

## Observation rows

Within each active episode, score every non-shock bar in `UNSAFE` or `RECOVERING` after the episode-start shock and before the first return to `NORMAL`.

Each scored row uses current state and `recent_shock_age`, bars since the most recent shock. The shock bar itself is not scored.

Fixed recent-shock age buckets are unchanged from V6: bars 1–2 `LT15`; bars 3–5 `M15_25`; bars 6–8 `M30_40`; bars >=9 `GE45`.

To keep all three horizons one coherent cumulative object, a row is included only when the recovery outcome can be determined through 60 minutes: either the first subsequent `NORMAL` is observed, or at least 12 subsequent 5m bars are observed without `NORMAL`.

## Fixed cumulative targets

- `normal_within_15m`: first subsequent `NORMAL` within 3 bars;
- `normal_within_30m`: first subsequent `NORMAL` within 6 bars;
- `normal_within_60m`: first subsequent `NORMAL` within 12 bars.

Each row must therefore satisfy `y15 <= y30 <= y60`.

## Model form

For each horizon separately, fit the same 8-cell table: `current state {UNSAFE, RECOVERING} × recent-shock age bucket {LT15, M15_25, M30_40, GE45}`.

Use the same V6 Laplace/Beta(1,1) estimate in every cell: `probability = (successes + 1) / (n + 2)`.

No horizon, bucket, smoothing rule, state threshold, or feature may be selected post hoc.

## Development evaluation

Use leave-one-year-out evaluation. For held-out 2021, 2022, and 2023, fit the three 8-cell tables on the other two years pooled across both symbols and score the held-out year. At each horizon compare Brier and LogLoss with a horizon-specific global constant probability fitted on the same training rows using the same Laplace smoothing.

Then fit final 15m/30m/60m tables on all 2021–2023 Development rows.

## Frozen Development support rule

Eligible for separate Validation only if all are true:

1. at every fixed horizon, table Brier is lower than the horizon-specific global baseline in all 3 held-out years;
2. every final `state × age × horizon` cell has at least 100 rows;
3. for every state-age cell, final cumulative probabilities are monotone: `P15 <= P30 <= P60`;
4. at every horizon and every age bucket, `P(recovery | RECOVERING) > P(recovery | UNSAFE)`;
5. state thresholds, shock-reset semantics, age buckets, horizons, and Laplace smoothing are unchanged;
6. no Validation/BlackBox data, PnL, payoff, or trading rule is used.

LogLoss is diagnostic and cannot rescue a Brier failure. Failure means retain V6 as the supported single-horizon object and do not tune horizons or buckets. Passing allows a separate frozen multi-horizon Validation study.

`production_authority=false`.
