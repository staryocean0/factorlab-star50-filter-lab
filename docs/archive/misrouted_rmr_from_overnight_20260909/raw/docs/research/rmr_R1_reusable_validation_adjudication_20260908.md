# R1 reusable DEV / VALIDATION adjudication — 2026-09-08

Decision: `R1_REUSABLE_VALIDATION_PASS_FINAL_REFIT_FROZEN`

This review implements the repository-wide reusable three-role policy:

- DEV: 2015-01-05 .. 2020-12-31;
- VALIDATION: 2021-01-01 .. 2025-12-31;
- BLACKBOX: 2026-01-05 .. 2026-08-21, not used during this stage.

The R1 identity and representation were not changed:

`rmr_cross_scale_pullback_parent_integrity_v2`

`R1_PARENT_COMPOSITE_1D`

`parent_integrity = (z(abs_drift) - z(overlap) + z(parent_eff)) / 3`

The directional-change thresholds, severity definition and recovery/failure geometry remained frozen.

## Detailed validation result

Validation detail is intentionally inspectable under the new policy.

### PAIR_A — S1 inside S2

- DEV resolved events: 1,730;
- VALIDATION resolved events: 1,283;
- pooled Brier improvement (baseline minus candidate): `0.0097436681`;
- pooled log-loss improvement: `0.0214322349`;
- annual Brier improvement was positive in 2021, 2022, 2023, 2024 and 2025 — 5/5 years.

### PAIR_B — S2 inside S3

- DEV resolved events: 685;
- VALIDATION resolved events: 517;
- pooled Brier improvement: `0.0094935894`;
- pooled log-loss improvement: `0.0217072277`;
- annual Brier improvement was positive in 2021, 2022, 2023, 2024 and 2025 — 5/5 years.

Both pairings passed every preregistered validation gate. Because validation passed, the already-fixed recipe performed one final refit on the full DEV+VALIDATION pool through 2025-12-31. No 2026 blackbox row was used in fitting.

Frozen final bundle:

`docs/governance/rmr_R1_reusable_blackbox_parameter_freeze_v1.json`

Parameter bundle SHA256:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

Final refit resolved-event inventory was 3,013 for PAIR_A and 1,202 for PAIR_B.

This adjudication is detailed by design because VALIDATION is a reusable diagnostic asset, not a one-shot sealed holdout.

Production authority remains false.
