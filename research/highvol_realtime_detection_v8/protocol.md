# HighVol realtime detection V8 — 3s partial-bar Development protocol

Purpose: test whether the validated 5-minute shock-reset risk process can be recognized causally within the final minute before each 5-minute reference bar closes, using only exact 3-second index observations already present in this repository. This is risk-state measurement only; no PnL, position, routing, payoff, or trading rule is created.

## Inherited reference state

V8 does not modify the V6/V7 state machine:

- 5m log return within trading day;
- `rv12 = std(last 12 valid 5m returns, ddof=0)`;
- `bg48 = std(previous 48 valid 5m returns, ddof=0)`;
- `shock = abs(ret_5m)/bg48 >= 3.0`;
- `UNSAFE` after shock, or while `vol_ratio=rv12/bg48 >= 1.50`;
- `RECOVERING` while `1.10 < vol_ratio < 1.50` after an active risk episode;
- `NORMAL` once `vol_ratio <= 1.10`;
- state transition uses the previous completed 5m reference state.

No threshold/state rule may change.

## Development boundary

- 2020 native 5m is warm-up/reference history only;
- measured 3s/reference bars are 2021-2023;
- symbols: `000688.SH`, `000852.SH`;
- physical checkout excludes 2024+, Validation and BlackBox.

## Time semantics and causal observation selection

Repository timestamp policy treats source `Z` strings as Shanghai wall-clock labels, not UTC conversions.

Native 1m/5m bars are bar-end labelled: e.g. five 1m bars labelled 09:31..09:35 aggregate exactly to the native 5m bar labelled 09:35. The 3s source contains `trading_day`, exact `observation_time`, `price`, and stable `row_index`.

For a native 5m bar ending at time `E`, fixed checkpoints are:

- `E - 60s`
- `E - 30s`
- `E - 15s`
- `E - 6s`
- `E - 3s`

At each checkpoint select the last 3s observation satisfying:

- same `trading_day`;
- observation time is within `[E-5m, checkpoint]`;
- if multiple source rows have the same timestamp, the row with greatest `row_index` wins.

No interpolation or forward-looking observation is allowed. If no same-block observation is available, the checkpoint is missing. Report staleness in seconds between checkpoint and selected observation because the source can be sparse/irregular near minute ends.

## Provisional state

At each available checkpoint:

- provisional `ret_5m = log(selected 3s price) - log(previous completed native 5m close)`;
- provisional `rv12` = prior eleven completed valid 5m returns plus provisional return;
- `bg48` remains the native reference value based only on completed returns strictly before the current bar;
- provisional shock and state transition use the unchanged thresholds above and previous completed native 5m state.

## Frozen outputs

For each lead 60/30/15/6/3 seconds, pooled/by-year/by-symbol report:

- usable checkpoint coverage;
- median and p95 observation staleness;
- exact 3-state accuracy;
- `UNSAFE` precision/recall;
- `RECOVERING` precision/recall;
- shock precision/recall;
- final-UNSAFE-onset precision/recall;
- Unsafe false alarms per 1,000 final-NORMAL bars.

For true final `UNSAFE` onsets report earliest and persistent detection across the ordered checkpoint sequence.

## Frozen Development support rule

The 3s detector is eligible for separate reusable Validation only if **all** are true at the fixed `E-3s` checkpoint:

1. pooled usable coverage >= 0.95;
2. each Development year usable coverage >= 0.95;
3. pooled final-UNSAFE precision >= 0.90 and recall >= 0.90;
4. each of 2021, 2022 and 2023 final-UNSAFE precision >= 0.85 and recall >= 0.85;
5. reference state thresholds/rules are unchanged;
6. no Validation/BlackBox data, PnL, payoff or trading rule is used.

The earlier 60/30/15/6-second checkpoints are diagnostic only and cannot replace failure of the 3-second gate. Observation staleness is reported, not tuned or thresholded.

`production_authority=false`.
