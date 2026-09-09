# HighVol / Unsafe recovery hazard v3 — frozen Development protocol

Date: 2026-09-10

## Purpose

This is bottom-layer K-line risk-state research only. It tests whether the inherited `UNSAFE` versus `RECOVERING` labels carry stable information about the *next part of the same shock-recovery process* after controlling coarsely for episode age.

No PnL, trade direction, entry/exit, holding period, stop, target, sizing, leverage, carrier mapping, or production action is permitted.

## Frozen inherited state engine

Use the historical HighVol/Unsafe state definition unchanged:

- 5-minute same-day log returns; overnight returns excluded;
- `RV_WINDOW = 12` bars;
- `BG_WINDOW = 48` preceding valid intraday returns;
- `HIGHVOL_RATIO = 1.50`;
- `EXTREME_RATIO = 2.25`;
- `RECOVERY_NORMAL_RATIO = 1.10`;
- `SHOCK_SIGMA = 3.00`;
- state resets each trading day.

A shock sets `UNSAFE`. While in an active risk process, `vol_ratio >= 1.50` stays `UNSAFE`, `1.10 < vol_ratio < 1.50` is `RECOVERING`, and `vol_ratio <= 1.10` returns to `NORMAL`.

The source/provenance anchor is `docs/research/highvol_unsafe_recovery_v2_anchor_20260910.md`.

## Data boundary

Development-only evaluation:

- 2020 5-minute data may be read only as rolling-history warm-up;
- episode starts and all reported measurements must be in 2021-01-01 through 2023-12-31;
- both `000688.SH` and `000852.SH` use common trading-day support;
- physically do not checkout/read 2024+ in the Development workflow;
- no BlackBox data.

## Episode unit

Use the v2 de-overlapped shock-triggered episode definition unchanged:

1. candidate start bar has `shock=True` and previous same-day bar is not `UNSAFE`;
2. episode ends at first subsequent `NORMAL` bar;
3. if no Normal occurs before day/session support ends, right-censor;
4. any new shock before first Normal is recurrence inside the same episode, not a new episode.

## Frozen landmark design

Observe each episode at exactly these elapsed ages after the start shock:

- 1 bar = 5 minutes;
- 3 bars = 15 minutes;
- 6 bars = 30 minutes;
- 9 bars = 45 minutes.

At each landmark report the fraction already recovered to `NORMAL`. For episodes still active, the current state must be `UNSAFE` or `RECOVERING`.

## Frozen future hazard window

For every active landmark, look forward exactly 3 bars = 15 minutes, without crossing the day/session support boundary.

Report, separately for current `UNSAFE` and current `RECOVERING`:

- probability of reaching `NORMAL` within the next 15 minutes;
- probability of another `shock=True` before Normal within the next 15 minutes;
- probability of still being non-Normal 15 minutes later.

If an episode reaches Normal before the full 3-bar horizon, the outcome is observed. If neither Normal nor full 3-bar support is available before the session/day boundary, that landmark is censored from the 15-minute hazard denominator. No extrapolation is allowed.

## Frozen summaries

For each symbol, each landmark, and pooled plus each Development year 2021/2022/2023:

- observable episode landmarks;
- already-Normal fraction by the landmark;
- active landmark count;
- active count by current state;
- each of the three future-hazard fractions and denominators.

Also report state-separation gaps at each landmark:

- recovery gap = `P(Normal next15 | Recovering) - P(Normal next15 | Unsafe)`;
- recurrence gap = `P(shock before Normal next15 | Unsafe) - P(... | Recovering)`;
- persistence gap = `P(non-Normal at +15 | Unsafe) - P(... | Recovering)`.

Expected positive signs are scientific diagnostics, not tuned acceptance thresholds. For each pooled gap, show how many of the three annual Development rows have the same sign. Do not select landmarks after seeing results.

## Interpretation

The primary question is state sufficiency:

- if `UNSAFE` consistently has lower near-term recovery and/or higher persistence/recurrence than `RECOVERING` across fixed landmarks and years, the label separation has process meaning and may support a later frozen probability calibration study;
- if the ordering is weak, reversed, or year-dependent, the existing state labels are not sufficient for a calibrated risk process and a future Development iteration must revisit state measurement rather than invent a payoff rule.

No new threshold is promoted in v3. No Validation is opened in this Development run.

`production_authority=false`; `blackbox_queried=false`.
