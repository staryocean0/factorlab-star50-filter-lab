# V19 residual failure audit — protocol

## Status and purpose

This is a **post-validation diagnostic audit**, not V20 and not a new confirmatory model study.

The validated V19 authority remains frozen:

`V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_REUSABLE_VALIDATION_SUPPORTED_2024_2025`

The audit asks only why the remaining V19 disagreements occur and whether they imply a genuinely new causal research question. It cannot change V19, cannot create production authority, and cannot reuse 2024-2025 as a fresh holdout for a future V20.

## Frozen authority

- V19 runner blob: `ee2fce299d5ee21abf1ab2c2c5183bac101ae822`
- V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`
- V18 runner blob: `62c207badff1c3e37cbb1a8e17ef89feeea611d8`
- V17 runner blob: `397d80037806ba11cadf7f77717d36d55fbafc91`
- V16 surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`
- primary checkpoint remains exactly E-15s.

## Data roles

This audit may inspect already-consumed data only:

- 2020 5m: warm-up/reference history only;
- 2021-2023 3s + 5m: Development diagnostic role;
- 2024-2025 3s + 5m: already-consumed reusable Validation diagnostic role;
- no 2026 3s;
- no protected BlackBox.

Development and Validation diagnostics must always be reported separately before any pooled descriptive total.

## Fixed residual taxonomy

### A. E-15 risk false negatives

Definition:

`reference_e15_state in {UNSAFE, RECOVERING}` and `machine_state == NORMAL`.

No new model is fitted. Each FN is classified by the unchanged V9 state at later **diagnostic-only** checkpoints:

- `late_by_e6`: E-6s is risk;
- `late_by_e3`: E-6s is not risk and E-3s is risk;
- `after_e3_or_close_only`: still not risk at E-3s but final/reference E-15 state is risk.

These later checkpoints cannot replace E-15s. They are used only to determine whether the miss was caused by risk evidence forming after E-15s.

### B. E-15 risk false positives

Definition:

`reference_e15_state == NORMAL` and `machine_state in {UNSAFE, RECOVERING}`.

Each FP is classified by later frozen V9 checkpoints:

- `resolved_by_e6`: E-6s is not risk;
- `resolved_by_e3`: E-6s remains risk but E-3s is not risk;
- `persists_through_e3_then_resolves_by_close`: E-3s remains risk but final/reference E-15 state is NORMAL.

The audit records whether the E-15 signal was a frozen partial shock and whether the final 5m bar was a frozen final shock. No threshold is moved.

### C. Exact three-state disagreement inside the risk set

Rows where both reference and machine are risk but `machine_state != reference_e15_state` are classified only as:

- `reference_UNSAFE_machine_RECOVERING`;
- `reference_RECOVERING_machine_UNSAFE`.

The audit records whether E-6/E-3 converges to the reference state. This is transition-timing diagnosis, not a new state rule.

### D. Episode residuals

For each Development/Validation split, reconstruct the exact frozen V19 reference and machine episodes and report:

- uncaptured reference episodes;
- fragmented reference episodes;
- false machine episodes;
- episode lengths;
- whether each episode failure contains one of the row-level A/B/C mechanisms.

No new episode definition is allowed.

## Fixed descriptive boundary bands

For shock-intensity diagnostics only, use the already-frozen V9 shock threshold `3.0` and fixed non-optimized bands:

- `<2.5`
- `2.5-3.0`
- `3.0-3.5`
- `3.5-4.0`
- `>=4.0`

These bands are descriptive. No threshold sweep or alternative cutoff may be scored.

## Decision rule about V20

This audit can reach only one of two conclusions:

1. `NO_V20_FROM_V19_RESIDUALS` if the dominant remaining errors are timing-boundary phenomena (evidence forms after E-15s or an E-15s partial shock resolves before close), or if a possible fix would require threshold/persistence/feature fitting on already-consumed Validation data.
2. `V20_HYPOTHESIS_EXISTS_BUT_NO_FRESH_REALTIME_VALIDATION_REMAINS` only if a distinct causal mechanism already observable by E-15s appears consistently in both Development and Validation diagnostics without fitting/search.

Even conclusion (2) does **not** authorize V20 execution or reuse 2024-2025 as fresh Validation.

## Governance

- no threshold search;
- no lead-time selection;
- no persistence-length search;
- no feature search;
- no probability fit;
- no subgroup optimization;
- no PnL/trading rule;
- no BlackBox;
- no 2026 3s;
- `production_authority=false`.
