# Current research entry

## 2026-09-10 current authority

**Current task: STAR50 / CSI1000 bottom-layer K-line risk-state research only.**

The research product of this bucket is a causal risk annotation/gate. It is not a directional trading strategy.

### Current supported risk process

The current best-supported post-shock process is:

`shock -> UNSAFE / RECOVERING -> Normal`

with an important clock rule:

> **Every new shock resets the recovery clock.** Recovery risk is better indexed by time since the most recent shock than by time since the first shock of the episode.

Current frozen probability object:

`current_state {UNSAFE, RECOVERING} × recent_shock_age -> P(Normal within next 15 minutes)`

Age buckets are fixed as `<15m`, `15-25m`, `30-40m`, `>=45m`.

### Evidence chain

- V3 recovery-hazard study: `UNSAFE` vs `RECOVERING` separates near-term normalization probability across Development years; recurrence hazard itself is not a stable monotone state discriminator.
- V4 probability calibration: the 8-cell state×age recovery table passed Development and 2024-2025 reusable Validation.
- V5 re-shock study: a recurrent shock sharply lowers near-term normalization probability and effectively restarts the recovery process; a separate universal `CLUSTERED` state was not supported.
- V6 clock comparison: recent-shock age beat episode-start age in leave-one-year-out Development Brier in all 3 years and LogLoss in all 3 years.
- V6 full reusable Validation through 2026-08-21: **SUPPORTED**. 2026 5m bars were deterministically constructed from the sealed 1m Validation pack only after exact 2023 1m->5m equivalence was confirmed for both indices (`max_abs_close_diff=0.0`).

V6 full Validation metrics:

- scored rows: `6334`;
- pooled Brier: `0.0841926` vs frozen global-rate baseline `0.1873921`;
- pooled LogLoss: `0.2910978` vs baseline `0.5621032`;
- annual Brier improved vs baseline in 2024, 2025, and 2026 through 2026-08-21;
- observed `P(Normal next15 | RECOVERING) > P(Normal next15 | UNSAFE)` in all 4 fixed age buckets for both STAR50 and CSI1000.

Primary sealed evidence:

- `docs/research/highvol_recovery_clock_v6_full_validation_20260910.md`
- `docs/research/highvol_recovery_clock_v6_full_validation_receipt_20260910.json`

`blackbox_queried=false`.

`production_authority=false`.

## Scope-repaired bucket authority

The repository owns bottom-layer causal K-line risk-state research only, including:

- volatility level / expansion;
- shock isolation and recurrence;
- `Unsafe / Recovering / HighVol` state evolution;
- switch-on, persistence, recovery and recovery probability;
- cross-scale 3s / 1m / 5m risk attributes and failure cases.

The current task is **not** to optimize a directional trading strategy, holding period, stop/target, sizing, account overlay or payoff router.

## Correct neighboring buckets

- `factorlab-two-wave-strategy-lab`: causal parent-structure classification into range / uptrend / downtrend from completed same-scale waves.
- `factorlab-trend-reversion-regime-lab`: concrete reversal / mean-reversion strategy research including R1/R2.

## Historical material retained but no longer current authority

This repository contains extensive historical strategy/payoff research, including:

- HighVol Router V1;
- STAR50 V10-V17 directional sign-flip research;
- half-day slope and earlier filter/payoff variants;
- drawdown/account/payoff diagnostics;
- previously misplaced R1/R2 material (already migrated out).

These historical results remain recoverable in Git but do not regain current authority in this bucket.

The complete pre-repair current snapshot remains at:

`4232d20b143a9c532e14a39761370bf1eca8d084`

Reusable bottom-layer findings extracted from archived strategy work are recorded separately in `docs/research/RISK_STATE_LEGACY_FINDINGS_20260909.md`.

## Current valid risk-research anchors

- `docs/handoff/cloud_risk_gate_20260907/`
- `docs/research/causal_volatility_tool_v1/`
- `docs/research/highvol_unsafe_recovery_v2_anchor_20260910.md`
- `docs/research/highvol_recovery_hazard_v3_20260910.md`
- `docs/research/highvol_recovery_calibration_v4_20260910.md`
- `docs/research/highvol_reshock_cluster_v5_20260910.md`
- `docs/research/highvol_recovery_clock_v6_full_validation_20260910.md`
- tail distribution / resolution-transfer / cross-scale root-cause material where the result is a K-line risk property rather than a payoff rule.

## Data and governance

Read `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md` and `docs/governance/DATA_USAGE_POLICY_V2.md` before new work.

Forward data roles:

- 2020: warm-up only where needed;
- Development: 2021-2023;
- reusable Validation: 2024 through 2026-08-21;
- protected BlackBox-V1: strictly after the cutoff under its aggregate-only protocol.

Deterministic 1m->5m construction is allowed when explicitly authorized and protected by a frozen construction contract plus historical equivalence guard where overlapping 5m exists. See `data/README.md`.

No prior payoff or risk-state Validation result automatically authorizes BlackBox access.

## Next research direction

Do not reopen R1/R2 or payoff routing here. The next risk-state work should improve **real-time state measurement**, especially cross-resolution detection/latency of the supported shock-reset recovery process, while preserving the frozen 5m recovery object as the reference state.

`production_authority=false`.
