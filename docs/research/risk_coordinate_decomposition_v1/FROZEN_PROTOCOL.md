# Two-coordinate risk decomposition V1 — FROZEN DIAGNOSTIC

Date: 2026-09-09
Branch: `research/risk-coordinate-decomposition-v1-20260909`
Parent: `fine_activity_future_risk_v1`, which closed as `development_structure_not_established`.

## Role

This is a **same-Development failure-mechanism diagnostic**, not an independent confirmation and not a candidate-selection pass. It is explicitly motivated by the parent V1 observation that M3 ranked future movement magnitude but did not monotonically rank future Unsafe probability on STAR50.

No Validation or BlackBox data may be read. No returns/P&L, trading, routing, sizing, or production decisions are allowed.

## Fixed coordinates

No new feature search is permitted.

Coordinate A — absolute fine-scale activity:
- exact parent V1 M3;
- same causal 15-second A5 activity surprise;
- same clock-matched expanding median/MAD;
- same bands: `<=0`, `(0,1]`, `(1,2]`, `>2`.

Coordinate B — inherited relative volatility state:
- current trailing-5m 1m RMS / preceding non-overlapping 30m 1m RMS;
- denominator floor 1 bp;
- `NonUnsafe` if ratio < 1.5;
- `Unsafe` if ratio >= 1.5.

The 1.5 boundary is inherited, not tuned here.

## Population and targets

Identical parent V1 Development population:
- fine reference warm-up begins 2022-05-16;
- evaluation rows are 2023 only;
- previous five-minute observed range <30 bp;
- strict fine-path support;
- decision minute 35..105;
- complete next-15-minute same-half-session targets.

Targets are unchanged:
- future 15m RMS;
- future mean absolute 1m return;
- any future Unsafe in the next 15m.

## Required table

For each index × current state × M3 band, report:
- row count;
- median/mean future 15m RMS;
- mean future absolute return;
- P(any future Unsafe in 15m);
- median current volatility ratio.

Also report pooled current-state totals per index.

## Descriptive architecture checks

Because this diagnostic is performed on already-inspected Development evidence, these checks are architecture summaries only, not statistical validation.

`amplitude_axis_present` for an index requires, in both current states:
- bottom M3 cell n>=100;
- top M3 cell n>=30;
- median future RMS at M3>2 is >=10% above M3<=0.

`state_persistence_axis_present` for an index requires:
- both current-state pools n>=500;
- P(future Unsafe | current Unsafe) exceeds P(future Unsafe | current NonUnsafe) by >=30 percentage points.

Call the fixed two-coordinate representation `two_axis_decomposition_descriptively_consistent` only if both axes are present for both indices.

This wording must never be upgraded to fresh/OOS confirmation.

## Hard guards

- 2024+ physical price inputs absent.
- BlackBox absent.
- parent M3 implementation reused unchanged.
- current Unsafe threshold remains 1.5.
- M3 bands remain unchanged.
- no economic labels.
- `candidate_nominated=false`.
- `production_authority=false`.
