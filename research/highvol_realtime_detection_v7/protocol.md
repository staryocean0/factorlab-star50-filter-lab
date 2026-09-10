# HighVol realtime detection V7 — 1m partial-bar Development protocol

Purpose: test whether the already validated 5-minute shock-reset risk process can be recognized causally before each 5-minute bar closes, using the repository's one-minute index bars. This is risk-state measurement only. No PnL, position, routing, or trading rule is created.

## Inherited authority

Reference state machine is unchanged from V3/V6:

- 5m log return within trading day;
- `rv12 = std(last 12 valid 5m returns, ddof=0)`;
- `bg48 = std(previous 48 valid 5m returns, ddof=0)`;
- `shock = abs(ret_5m)/bg48 >= 3.0`;
- `UNSAFE` after shock, or while `vol_ratio=rv12/bg48 >= 1.50`;
- `RECOVERING` while `1.10 < vol_ratio < 1.50` after an active risk episode;
- `NORMAL` once `vol_ratio <= 1.10`;
- each new shock resets the recovery clock, but the V7 target here is contemporaneous state detection, not recovery-probability refitting.

No threshold above may change.

## Data

Development only:

- 2020 warm-up;
- 2021-2023 measured rows;
- symbols `000688.SH` and `000852.SH`;
- existing native 5m bars are the reference state path;
- existing 1m bars are the only realtime source.

Physical checkout must exclude 2024+, Validation and BlackBox.

## Required 1m -> 5m equivalence guard

For every complete day in 2020-2023 and each symbol:

1. require exactly 240 one-minute rows;
2. split morning and afternoon into 120 rows each;
3. group consecutive non-overlapping blocks of five rows;
4. fifth 1m close must equal the native 5m close after chronological alignment;
5. 48 5m blocks must exist per complete day.

Any mismatch stops the study.

## Partial-bar detector

For each native 5m bar with a valid previous same-day close and finite background volatility, build four causal provisional observations:

- offset 1: latest close after first minute of the 5m block;
- offset 2: after second minute;
- offset 3: after third minute;
- offset 4: after fourth minute.

At each offset:

- provisional `ret_5m = log(partial_close) - log(previous completed 5m close)`;
- provisional `rv12` uses the previous eleven completed valid 5m returns plus this provisional return;
- `bg48` uses only completed returns strictly before the current 5m bar, identical to the reference engine;
- provisional shock/state transition uses the exact inherited thresholds and the previous **completed 5m** risk state;
- no future 1m row inside the current 5m block may be read.

The fifth minute is the reference close and is not a tunable detector offset.

## Frozen outputs

For offsets 1-4, pooled/by-year/by-symbol report:

- exact 3-state accuracy;
- binary `UNSAFE` precision/recall;
- binary `RECOVERING` precision/recall;
- final-shock precision/recall;
- final-UNSAFE-onset precision/recall;
- unsafe false alarms per 1,000 final-NORMAL bars.

For true final `UNSAFE` onsets also report:

- earliest partial offset that first detects `UNSAFE`;
- earliest offset from which `UNSAFE` remains continuously detected through offset 4;
- fraction detected at least 4/3/2/1 minutes before the 5m close.

## Frozen Development support rule

The one-minute partial-bar detector is eligible for separate reusable Validation only if all are true:

1. 1m->5m equivalence passes for both symbols over 2020-2023;
2. at offset 4, pooled final-`UNSAFE` precision >= 0.90 and recall >= 0.90;
3. at offset 4, each of 2021, 2022 and 2023 has final-`UNSAFE` precision >= 0.85 and recall >= 0.85;
4. thresholds/state rules are unchanged;
5. no Validation/BlackBox data, PnL or trading rule is used.

This gate is intentionally defined before execution. Earlier offsets and `RECOVERING` metrics are diagnostic only and cannot replace a failure of the offset-4 gate.

`production_authority=false`.
