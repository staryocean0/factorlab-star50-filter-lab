# HighVol realtime horizon-adaptive recovery V17 — Development protocol

## Purpose

V16 established and reusable-Validation-supported one fixed 5m recovery surface:

- `15m = current_state + recent-shock age`;
- `30m = current_state + recent-shock age`;
- `60m = recent-shock age only`.

V17 asks one bounded question: **can that exact frozen V16 multi-horizon object be emitted 15 seconds before the 5m close using the already-frozen V9/V10 realtime state measurement, without refitting or changing any probability?**

This is a risk-state transfer study only. It does not create a trading strategy, payoff rule, router, position sizing rule, or production authority.

## Frozen authority

- V16 frozen surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`.
- V16 Development execution: `bcdc18d5886869865c6454fa323ebc6858090249`, run `34497737506`.
- V16 reusable Validation: run `34602527314`, `full_validation_supported=true`.
- V10 preregistered realtime checkpoint: **E-15s** only.
- exact frozen V9 realtime runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`.
- exact frozen V11 common-cohort builder blob: `713f0dcc41e7f32f75934fc7709a406ff71579e6`.

No alternative lead time is evaluated in V17 Development. E-30s/E-60s are not eligible rescue paths.

## Development boundary

- warm-up/reference: 2020 where required by the frozen 5m state process;
- scored Development: 2021-01-01 through 2023-12-31;
- symbols: `000688.SH`, `000852.SH`;
- 3s inputs: 2021-2023 only;
- 2024+, reusable Validation, and BlackBox are physically excluded from the run.

The scored cohort is the exact frozen V11 common 15/30/60m cohort and must contain exactly `7327` rows.

## Fixed realtime construction

For each frozen V11 cohort row:

1. locate the same 5m bar in the frozen V9 reference state process;
2. at `bar_end - 15 seconds`, select the latest same-block 3s observation at or before the checkpoint;
3. recompute the partial 5m return, rolling volatility, shock intensity, and provisional risk state using the exact frozen V9 logic and thresholds;
4. if the partial bar is a fresh shock, provisional `NORMAL`, or lacks the required checkpoint/reference window, the realtime multi-horizon object is unavailable, exactly preserving the existing V9/V10 risk-object gating semantics;
5. otherwise emit the frozen V16 probabilities with **no fit**:
   - 15m: `(partial_state, frozen recent-shock age bucket)`;
   - 30m: `(partial_state, frozen recent-shock age bucket)`;
   - 60m: frozen `age-only` anchor for that age bucket.

The recent-shock age bucket is unchanged unless a fresh partial shock occurs; a fresh partial shock makes the row unavailable rather than silently changing the frozen cohort definition.

Every emitted realtime row must satisfy `p15 <= p30 <= p60`. The emitted 60m probability must equal the frozen V16 age-only anchor exactly.

## Fixed outputs

Report pooled, by Development year, and by symbol:

- reference rows and realtime-scored rows;
- realtime coverage;
- exact provisional-state agreement with final 5m state on scored rows;
- per-horizon probability MAE and exact-cell agreement versus the frozen final-5m V16 reference;
- per-horizon realtime/reference Brier and LogLoss on the same matched rows;
- per-horizon Brier/LogLoss degradation;
- fresh-shock / provisional-NORMAL / missing-checkpoint counts;
- rowwise monotonicity and exact 60m-anchor guards.

## Development acceptance

V17 is eligible to freeze for one reusable Validation on the existing available 2024-2025 3s coverage only if all hold:

1. exact V11 common cohort row count is `7327`;
2. final 5m V11/V9 state alignment is exact on all cohort rows;
3. pooled realtime multi-horizon coverage is at least `0.98`;
4. each Development year coverage is at least `0.95`;
5. pooled probability MAE versus frozen V16 is at most `0.01` at both 15m and 30m;
6. pooled Brier degradation versus frozen V16 is at most `0.002` at both 15m and 30m;
7. each Development year Brier degradation is at most `0.005` at both 15m and 30m;
8. every emitted row satisfies `p15 <= p30 <= p60`;
9. 60m realtime probability equals the frozen age-only V16 anchor exactly on every emitted row, so 60m MAE/Brier/LogLoss degradation versus the matched frozen reference is zero within `1e-12`;
10. V16 probabilities, V9 state thresholds, V11 cohort definition, age buckets, horizons, and E-15s checkpoint remain unchanged;
11. no probability fit, threshold search, projection change, lead-time search, or post-hoc horizon selection is performed;
12. Validation and BlackBox are not queried;
13. no PnL, payoff, routing, sizing, leverage, or trading rule is computed.

Failure cannot be rescued by trying another checkpoint, changing the gating semantics, refitting the V16 surface, dropping a horizon/year, or changing state/age definitions.

A Development PASS authorizes only freezing this exact V17 transfer and one reusable Validation on **2024-2025 3s coverage**. It does not authorize any 2026 3s claim and does not authorize BlackBox.

`production_authority=false`.
