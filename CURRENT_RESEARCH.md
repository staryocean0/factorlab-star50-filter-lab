# Current research entry

## 2026-09-11 current authority

**Current task: STAR50 / CSI1000 bottom-layer K-line risk-state research only.**

The research product of this bucket is a causal risk annotation/gate. It is not a directional trading strategy.

## Current validated 5m recovery object — V16

The decisive V16 action is complete.

Frozen horizon-adaptive object:

- `15m = current_state {UNSAFE, RECOVERING} + time-since-most-recent-shock`;
- `30m = current_state {UNSAFE, RECOVERING} + time-since-most-recent-shock`;
- `60m = time-since-most-recent-shock only`.

Age buckets remain fixed as `<15m`, `15-25m`, `30-40m`, `>=45m`. Every new shock resets the recovery clock.

Development authority:

- branch: `research/highvol-horizon-adaptive-surface-v16-20260910`;
- execution commit: `bcdc18d5886869865c6454fa323ebc6858090249`;
- run: `34497737506`;
- artifact: `10160511846`;
- frozen surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`;
- Development decision: `FREEZE_EXACT_SURFACE_AND_RUN_REUSABLE_VALIDATION`.

Reusable Validation authority:

- branch: `research/highvol-horizon-adaptive-v16-validation-20260910`;
- execution commit: `198c3040182f500e7e8c576ee7fa5ade3b30c9fa`;
- run: `34602527314`;
- artifact: `10264689647`;
- artifact SHA256: `e28a877d40c3bd2464b4f09b1078cdfae83a7ecebcc8bbd34fdb7bad4e8d82f5`;
- common scored rows: `5908`;
- year rows: `2024=2339`, `2025=2201`, `2026=1368` through `2026-08-21`;
- `full_validation_supported=true`.

Pooled frozen improvement over age-only:

- 15m: Brier `+0.00268837`, LogLoss `+0.00890434`;
- 30m: Brier `+0.00305660`, LogLoss `+0.00980693`;
- 60m: Brier `0.0`, LogLoss `0.0` because V16 is exactly the age-only anchor at 60m.

Annual Brier wins versus age-only:

- 15m: `3/3`;
- 30m: `3/3`;
- 60m: exact equality by construction.

All scored rows satisfy `p15 <= p30 <= p60`. The 60m row-level prediction difference from frozen age-only is exactly `0.0`.

Primary sealed evidence:

- `docs/research/highvol_horizon_adaptive_v16_validation_20260911.md`;
- `docs/research/highvol_horizon_adaptive_v16_validation_receipt_20260911.json`;
- `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json`;
- `research/highvol_horizon_adaptive_v16_validation/VALIDATION_RESULTS.md`;
- `research/highvol_horizon_adaptive_v16_validation/DECISIVE_RECEIPT.json`.

## Why V16 exists

The multi-horizon path is already complete and must not be rerun:

- V11: one unified 15/30/60m `state + age` survival surface was rejected in Development;
- V12: simple shock-expiry explanation was rejected;
- V13: exact recent-shock-age sample composition did not explain the 60m crossover;
- V14: established horizon-dependent incremental state value: useful at 15m and 30m, not stable at 60m; reusable Validation showed the same 15m/30m gains and 60m reversal;
- V15: Development block/bootstrap adjudication again supported state increment at 15m/30m and not 60m;
- V16: froze the horizon-adaptive surface and has now passed reusable Validation.

Do not reopen V11-V15 merely to reconfirm this chain.

## 2026 5m construction authority

2026 5m Validation bars were deterministically synthesized from sealed one-minute Validation inputs only after the historical 2023 equivalence guard passed exactly for both indices:

- 242 common 2023 days per symbol;
- 11,616 rows per symbol;
- `max_abs_close_diff=0.0` for both symbols.

The authorized 2026 one-minute inputs contain 154 complete trading days through `2026-08-21` and synthesize to 7,392 5m rows per symbol.

No data after `2026-08-21` was used.

## Current realtime risk object

The current cross-scale realtime authority remains V10 at the preregistered `E-15s` checkpoint:

`E-15s causal state + time since most recent shock -> P(Normal within next 15 minutes)`.

V8/V9/V10 realtime support uses available 3s Validation coverage through 2025; the repository 3s physical contract ends at 2025-12-31, so there is no claimed 2026 3s Validation authority.

V16 validates the 5m multi-horizon recovery surface. It does **not** by itself validate a realtime 15/30/60m transfer.

## Earlier supported risk process

The supported post-shock mechanism remains:

`shock -> UNSAFE / RECOVERING -> Normal`

with the clock rule:

> Every new shock resets the recovery clock. Recovery risk is indexed by time since the most recent shock, not time since the first shock of the episode.

Relevant prior authority:

- V3: `UNSAFE` vs `RECOVERING` separates near-term normalization probability;
- V4: state×age recovery calibration passed Development and reusable Validation;
- V5: recurrent shock sharply lowers near-term normalization probability and resets recovery; no universal separate `CLUSTERED` state was supported;
- V6: recent-shock age beat episode-start age in all Development leave-one-year-out folds and passed full reusable Validation through 2026-08-21;
- V7: 1m realtime detector failed preregistered UNSAFE recall and was not promoted;
- V8: frozen 3s detector passed Development and available 2024-2025 reusable Validation subset;
- V9: unified realtime risk object passed the same subset;
- V10: preregistered `E-15s` realtime probability annotation passed Development and available 2024-2025 reusable Validation subset.

## Scope-repaired bucket authority

This repository owns bottom-layer causal K-line risk-state research only, including:

- volatility level / expansion;
- shock isolation and recurrence;
- `Unsafe / Recovering / HighVol` state evolution;
- switch-on, persistence, recovery and recovery probability;
- cross-scale 3s / 1m / 5m risk attributes and failure cases.

The current task is **not** to optimize a directional trading strategy, holding period, stop/target, sizing, account overlay or payoff router.

Historical HighVol Router V1, directional STAR50 V10-V17 sign-flip work, half-day slope work, drawdown/account/payoff diagnostics and misplaced R1/R2 material remain preserved but are not current authority.

Correct neighboring buckets:

- `factorlab-two-wave-strategy-lab`: causal parent-structure classification into range / uptrend / downtrend from completed same-scale waves;
- `factorlab-trend-reversion-regime-lab`: concrete reversal / mean-reversion strategy research including R1/R2.

## Data and governance

Read before new work:

- `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`;
- `docs/governance/DATA_USAGE_POLICY_V2.md`;
- `docs/governance/data_usage_declaration.json`;
- `docs/governance/blackbox_query_ledger.json`.

Forward data roles:

- 2020: warm-up only where needed;
- Development: 2021-2023;
- reusable Validation: 2024 through 2026-08-21;
- protected BlackBox-V1: strictly after the cutoff under its frozen aggregate-only protocol.

No prior payoff or risk-state Validation result automatically authorizes BlackBox access.

## Current breakpoint

The requested V16 decisive action is finished and sealed. The new breakpoint is:

`V16_REUSABLE_VALIDATION_SUPPORTED`

Do **not** rerun V11-V16, refit the frozen surface, or query BlackBox.

A future realtime transfer of the validated multi-horizon 5m object is scientifically eligible only as a separately preregistered next protocol; it has **not** been started here.

`blackbox_queried=false`.
`production_authority=false`.
