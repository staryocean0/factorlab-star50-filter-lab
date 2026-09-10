# HighVol realtime risk object V9 — frozen reusable Validation

Purpose: validate the already-frozen composition

`E-3s causal risk state + time since most recent shock -> P(Normal within next 15 minutes)`

without fitting, tuning, changing thresholds, or introducing any trading/payoff object.

## Frozen Development authority

- source branch: `research/highvol-realtime-risk-object-v9-20260910`
- source commit: `e01b293dcfc3100a02265315376bc63a9137c3d3`
- source protocol blob: `64bdbaa7624fed5cdf3c6fa167c1ab64a2c547d7`
- source runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`
- Development run: `34443013548`
- Development artifact: `10138625380`
- artifact SHA256: `70abd300bfc2c66eba758b2d7fca0f51f91102d9e06db6be574af2958091ba07`

The V6 probability table, V8 state thresholds, state transition rules, age buckets, and primary checkpoint `E-3s` are frozen exactly as in Development.

## Validation boundary

The repository 3-second physical contract ends at 2025-12-31, so this Validation evaluates the physically available reusable subset only:

- scored years: 2024, 2025;
- symbols: `000688.SH`, `000852.SH`;
- reference 5m history: 2020-2025, solely for causal state construction;
- measured 3s files: 2024 and 2025 only;
- no 2026 3s data is queried;
- BlackBox is physically excluded.

A PASS means **supported on the available 2024-2025 3s Validation subset**, not complete Validation through 2026-08-21.

## Frozen support screen

At the same `E-3s` checkpoint, all must hold:

1. pooled realtime probability coverage >= 0.98;
2. each measured Validation year coverage >= 0.95;
3. pooled probability MAE versus frozen V6 reference <= 0.01;
4. pooled realtime Brier degradation versus V6 reference on matched rows <= 0.002;
5. each measured Validation year Brier degradation <= 0.005;
6. V6 probability table, V8 thresholds, checkpoint and state rules remain unchanged;
7. no probability fit, threshold search, PnL, payoff, routing, trading rule, or BlackBox query occurs.

`production_authority=false` regardless of outcome.
