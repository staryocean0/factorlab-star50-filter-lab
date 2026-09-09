# Two-coordinate risk map — reusable Validation diagnostic V1

Date: 2026-09-09
Branch: `research/risk-coordinate-validation-v1-20260909`
Parent Development diagnostic: `risk_coordinate_decomposition_v1`.

## Scientific role

This is a **reusable Validation diagnostic**, not fresh/OOS qualification.

The two coordinates, thresholds, conditioning set, future targets, and architecture checks are frozen from Development before this Validation run.

No BlackBox data may be read. No trading, return/P&L, sizing, routing, instrument, or production outcome is evaluated.

## Available Validation scope

The repository fine-scale 3-second contract currently ends at 2025. Therefore this fine-scale diagnostic evaluates:

- Validation slice 1: calendar 2024;
- Validation slice 2: calendar 2025.

It does **not** read 2026 and does not claim to cover the complete repository Validation pool through 2026-08-21.

Causal reference warm-up starts 2022-05-16 and runs forward through each decision time. A row's M3 reference uses only strictly earlier same-index / same-half-session / same-minute observations.

## Frozen coordinates

### A. M3 activity surprise

Identical to parent:
- previous five physical minutes of strict 15-second returns;
- A5 = RMS of those returns;
- expanding clock-matched median/MAD of log(A5), min history 60;
- M3 bands: `<=0`, `(0,1]`, `(1,2]`, `>2`.

### B. Current relative-volatility state

Identical to parent:
- current trailing-5m 1m RMS divided by preceding non-overlapping 30m 1m RMS;
- 1 bp denominator floor;
- NonUnsafe if ratio <1.5;
- Unsafe if ratio >=1.5.

## Frozen population and targets

- subjects: 000688.SH and 000852.SH;
- previous five-minute range <30bp;
- strict fine support, no interpolation/zero fill;
- decision minutes 35..105 within a half-session;
- complete next-15-minute same-half-session future required.

Targets:
- future 15m RMS;
- future mean absolute 1m return;
- any future Unsafe during the next 15m.

## Frozen per-index-per-year checks

For each index × year separately:

`amplitude_axis_present` requires in both current states:
- M3<=0 n>=100;
- M3>2 n>=30;
- median future RMS(M3>2) / median future RMS(M3<=0) >=1.10.

`state_persistence_axis_present` requires:
- both current-state pools n>=500;
- P(future Unsafe | current Unsafe) - P(future Unsafe | current NonUnsafe) >=30 percentage points.

The Validation diagnostic is called `validation_diagnostic_replicates_two_axis_structure` only if both axes pass for both indices in both 2024 and 2025.

Otherwise it is `validation_diagnostic_does_not_fully_replicate`.

No criterion may be changed after seeing Validation output.

## Required interpretation

Even a full pass remains reusable Validation evidence, not BlackBox qualification and not production authority.

A failure must be diagnosed by the frozen cells; it may not be rescued by changing M3 bands, 1.5, the 30bp condition, future horizon, or sample-size thresholds in this pass.

Always record:
- `validation_queried=true`;
- `validation_years=[2024,2025]`;
- `read_2026=false`;
- `blackbox_queried=false`;
- `fresh_oos=false`;
- `candidate_nominated=false`;
- `production_authority=false`.
