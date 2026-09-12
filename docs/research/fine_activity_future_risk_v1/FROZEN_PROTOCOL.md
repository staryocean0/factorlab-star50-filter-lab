# Fine-activity future-risk V1 — FROZEN PROTOCOL

Date: 2026-09-09
Branch: `research/fine-activity-future-risk-v1-20260909`
Status at freeze: outcomes not computed by this V1 runner.

## Question

When the visible five-minute price range is still below 30 bp, does causal 15-second activity surprise contain information about **continuous future risk**, rather than only a sparse first-shock label?

This is a risk-mechanism study. It does not evaluate returns/P&L, trade direction, execution, sizing, routing, options/futures, or production.

## Data roles

Repository policy V2 governs this study.

- Fine-scale warm-up/reference only: `2022-05-16 .. 2022-12-31`.
- Development evaluation: calendar year `2023` only.
- Validation `2024-01-01 .. 2026-08-21`: **not read in V1**.
- BlackBox-V1: **not read**.

Subjects: `000688.SH` and `000852.SH`.
Inputs: repository 1m and native 3s index observations only.

The strict fine path follows the prior audited rule: sample a 15-second grid, require each endpoint to be at most 3 seconds old, never interpolate, never zero-fill, preserve same-second source rows by stable row key. Decision points before 2022-05-16 are excluded from scientific use.

## Current-state condition

Primary condition: previous five physical minutes have

`pre5m_range_bp < 30`.

This is only a low-amplitude surface condition; it is not called safe/clean.

## Primary measurement M3

Over the previous five physical minutes, using only strict 15-second returns:

`A5 = sqrt(mean(r_15s^2))`.

For each index × half-session × minute-of-half-session, build an expanding reference from **strictly earlier** admissible observations:

- center = median(log(A5));
- scale = `max(1.4826 * MAD, 1e-8)`;
- minimum prior observations = 60.

Then

`M3 = (log(A5) - center) / scale`.

No future/current observation enters its own reference.

## Control C1z

Compute the previous-five-minute 1m RMS and apply the same causal clock-matched expanding median/MAD standardization. This is `C1z` and represents ordinary recent minute-scale activity.

## Secondary measurement M4

For continuity with the frozen 2026-09-07 structure study:

- `M1 = log((RV_15s + 1e-16)/(RV_1m + 1e-16))` over the same five minutes;
- `M4 = M3 + M1`.

M4 is descriptive secondary evidence. V1 primary adjudication is based on M3.

## Future-risk targets

At decision minute `t`, all targets use later information only for evaluation and stay inside the same half-session.

1. `future_rms15_bp`: RMS of the next 15 complete 1m close-to-close returns, minutes `t+1..t+15`.
2. `future_mean_abs15_bp`: mean absolute value of the same 15 returns.
3. `future_any_unsafe15`: whether any minute in `t+1..t+15` is in the frozen continuous-volatility Unsafe state, where at each future minute `u`:
   - recent = RMS of trailing 5 complete 1m returns ending at `u`;
   - background = RMS of the preceding non-overlapping 30 1m returns;
   - denominator floor = 1 bp;
   - Unsafe iff `recent/background >= 1.5`.

No target crosses a half-session boundary.

## Fixed views

M3 bands are frozen before execution:

- `<=0`;
- `(0,1]`;
- `(1,2]`;
- `>2`.

Primary tables report, per index, n / median future RMS / mean future RMS / mean future absolute return / Unsafe probability in each band.

Incremental-control view is also fixed:

- restrict to `C1z < 1`;
- compare `M3 < 1` versus `M3 >= 1`.

No M3/C1 threshold is tuned after outcomes.

## Development-only adjudication

Call the mechanism `development_structure_supported` only if **both indices** satisfy all:

1. median `future_rms15_bp` is non-decreasing across the four ordered M3 bands with at least 100 eligible rows in every band;
2. the `>2` band median future RMS is at least 10% above the `<=0` band;
3. `P(future_any_unsafe15)` in `>2` exceeds `<=0` by at least 5 percentage points;
4. inside `C1z < 1`, both M3 groups have at least 500 rows and `M3>=1` has higher median future RMS and higher Unsafe probability than `M3<1`.

Otherwise adjudicate `development_structure_not_established`.

This is deliberately demanding and is not a production-promotion gate.

## Hard guards

Fail closed if:

- any 2024+ price row is present in the workflow workspace;
- any pre-2022-05-16 fine decision enters evaluation/reference;
- fine endpoints are interpolated or zero-filled;
- a target crosses a half-session;
- BlackBox files are present/read;
- P&L/trading fields are used;
- thresholds/bands are changed after results.

Always record:

- `validation_queried=false`;
- `blackbox_queried=false`;
- `fresh_oos=false`;
- `production_authority=false`.
