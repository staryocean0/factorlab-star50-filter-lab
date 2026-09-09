# HighVol / Unsafe recovery calibration v4 — frozen Development protocol

Date: 2026-09-10

## Objective

Turn the supported `UNSAFE` / `RECOVERING` recovery-state distinction into a small causal probability object:

`P(reach NORMAL within next 15m | current risk state, shock-episode age)`.

This is risk-state calibration only. No PnL, trade direction, entry/exit, holding period, instrument mapping, sizing, or production action is allowed.

## Inherited engine

Reuse v3 exactly: same 5m state engine, de-overlapped shock episode definition, censoring rule, common-day support, fixed landmarks and 15m outcome. Thresholds remain `RV_WINDOW=12`, `BG_WINDOW=48`, `HIGHVOL_RATIO=1.50`, `EXTREME_RATIO=2.25`, `RECOVERY_NORMAL_RATIO=1.10`, `SHOCK_SIGMA=3.00`.

## Development data

- 2020 only for rolling warm-up.
- Fit/calibration rows: 2021-01-01 through 2023-12-31.
- Symbols: `000688.SH` and `000852.SH`, pooled into one calibration table.
- No 2024+, no Validation, no BlackBox in the Development workflow.

## Frozen model class

Exactly 8 cells:

- current state: `UNSAFE`, `RECOVERING`;
- episode age landmark: 1, 3, 6, 9 five-minute bars (5, 15, 30, 45 minutes).

For each cell, with `s` Normal-within-next15 successes among `n` fully observed active landmarks, freeze

`p = (s + 1) / (n + 2)`

(Beta(1,1) / Laplace smoothing).

No symbol coefficient, current vol-ratio coefficient, interaction beyond the fixed 2×4 cells, regression fitting, threshold search, isotonic adjustment or post-result pooling is permitted.

## Development diagnostics

Report cell `n`, successes, raw frequency and smoothed probability. Also report in-sample Brier/log loss for:

1. the 8-cell state×age table;
2. an age-only 4-cell table fitted with the same smoothing;
3. a state-only 2-cell table;
4. one global probability.

These fit diagnostics describe information content; they are not OOS claims.

## Frozen eligibility to become a calibration candidate

All must hold before Validation is opened:

1. exactly 8 state×age cells exist;
2. every cell has `n >= 100` Development observations;
3. at every one of the four fixed ages, smoothed `P(Normal next15 | RECOVERING)` is strictly greater than the corresponding `UNSAFE` probability;
4. no state threshold or episode rule changed;
5. no Validation/BlackBox data was read.

If eligible, the exact 8 probabilities, counts, code identity and data role are frozen before reusable Validation.

## Validation intent

After freeze, evaluate the frozen probability table on reusable Validation without refitting. Primary calibration diagnostics will be Brier score, log loss, calibration by predicted cell, and comparison to the frozen Development global baseline. Any incomplete 5m Validation coverage must be reported explicitly; never manufacture 5m bars from another frequency merely to fill coverage.

`production_authority=false`.
