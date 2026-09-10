# HighVol realtime risk object V9 — Development protocol

Purpose: combine the already-validated V8 3-second causal state detector with the already-frozen V6 shock-reset recovery probability table, without fitting or tuning any new state rule.

## Frozen upstream components

V6 recovery object:

`current_state {UNSAFE, RECOVERING} × time since most recent shock -> P(Normal within next 15 minutes)`

Frozen age buckets: `LT15`, `M15_25`, `M30_40`, `GE45`.

Frozen V6 probabilities:

- UNSAFE/LT15 `0.007067137809187279`
- UNSAFE/M15_25 `0.007751937984496124`
- UNSAFE/M30_40 `0.01340033500837521`
- UNSAFE/GE45 `0.5284210526315789`
- RECOVERING/LT15 `0.05555555555555555`
- RECOVERING/M15_25 `0.04879679144385027`
- RECOVERING/M30_40 `0.08446215139442231`
- RECOVERING/GE45 `0.7555919258046918`

V8 realtime detector:

- unchanged 5m state machine;
- primary checkpoint `E-3s`;
- latest same-block 3s observation at or before checkpoint;
- no interpolation;
- same timestamp greatest `row_index` wins.

## Development boundary

- warm-up/reference history: 2020;
- scored Development: 2021-2023;
- symbols: `000688.SH`, `000852.SH`;
- physical checkout excludes 2024+ and BlackBox.

## Reference scoring rows

Use the exact V6 row semantics. Within each shock-started episode, score only bars after the most recent shock where:

- final completed 5m state is `UNSAFE` or `RECOVERING`;
- current completed bar is not itself a shock;
- recent-shock age is positive;
- all three future 5m bars needed for the 15-minute target are observable.

Reference probability is the frozen V6 table lookup from final 5m state and final recent-shock-age bucket.

## Realtime scoring at E-3s

For the same reference row, compute the V8 provisional state using only information available at `E-3s`.

- Prior completed 5m bars remain fully observed and causal.
- If the current partial bar already qualifies as a shock at E-3s, label it `fresh_shock` and do not force a V6 recovery probability because V6 never scored age zero/current-shock bars.
- Otherwise use the same completed-bar recent-shock age and the provisional V8 state.
- If provisional state is not `UNSAFE` or `RECOVERING`, realtime probability is unavailable for that row.
- No fallback, interpolation, threshold relaxation, or new probability fitting is allowed.

## Frozen outputs

Pooled, by year, and by symbol report:

- V6-reference scoring rows;
- realtime probability coverage;
- exact state agreement;
- exact V6 probability-cell agreement;
- probability MAE versus V6 reference probability;
- reference Brier / LogLoss against realized `Normal within next15m`;
- realtime Brier / LogLoss on rows with realtime probability;
- Brier / LogLoss degradation;
- fresh-shock and provisional-NORMAL unscorable counts.

## Frozen support screen

V9 is eligible for reusable Validation only if all hold:

1. pooled realtime probability coverage >= 0.98;
2. each Development year realtime probability coverage >= 0.95;
3. pooled probability MAE versus the V6 reference <= 0.01;
4. pooled realtime Brier degradation versus the V6 reference on matched rows <= 0.002;
5. each Development year realtime Brier degradation <= 0.005;
6. no V6 probability, V8 threshold, checkpoint, or state rule changed;
7. no PnL, payoff, routing, trading rule, Validation, or BlackBox query occurs.

This support screen only decides whether the composition is faithful enough to validate. It does not create production authority.

`production_authority=false`.
