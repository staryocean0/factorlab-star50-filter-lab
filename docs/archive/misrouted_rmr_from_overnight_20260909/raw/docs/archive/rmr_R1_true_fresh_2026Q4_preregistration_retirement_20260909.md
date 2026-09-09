# R1 true-fresh 2026Q4 preregistration — retired unopened

Date: 2026-09-09

Historical identity: `rmr_cross_scale_pullback_parent_integrity_v2` true-fresh 2026Q4 challenge.

## Decision

`RETIRED_UNOPENED_SUPERSEDED_BY_CURRENT_REUSABLE_GOVERNANCE`

The preregistered Q4 challenge is retired without source admission, outcome execution, refit, or result inspection.

No BLACKBOX source was opened and no BLACKBOX query was created. `production_authority=false`.

## Why this is retirement, not a scientific failure

The old protocol required a complete `2026-10-01 .. 2026-12-31` calendar block and explicitly set the earliest execution date in China to `2027-01-01`. At the time of retirement the prerequisite future block did not exist in the project.

More importantly, the preregistration was tied to the earlier specialist selection/holdout surface and historical bundle:

`e618a5a06a803f4464267e69e39f98fa316fd572f40efcb3f9e40fc25df2779c`

The project subsequently adopted the permanent reusable three-role policy and established the current certified R1 reproduction/final-fit bundle:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

The current authority also states not to wait for future data; when newer data is supplied, the three-role map is to be versioned forward rather than treating existing history as consumed.

Running the old Q4 protocol later would therefore resurrect a superseded parameter/protocol surface instead of using current governance.

## Exact historical implementation

The complete pre-cleanup tree is recoverable at commit:

`5fc178352fe0fefdaa8415881dc6e7aa5d2ba3a5`

That commit contains the full preregistered Q4 surface:

- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_source_admission_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_source_admission_execution_freeze_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_execution_authorization_template_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_evaluation_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_evaluation_execution_freeze_v1.json`
- `scripts/admit_rmr_R1_true_fresh_2026Q4_source.py`
- `scripts/evaluate_rmr_R1_true_fresh_2026Q4.py`
- `tests/test_rmr_R1_true_fresh_2026Q4_source_admission.py`
- `tests/test_rmr_R1_true_fresh_2026Q4_evaluator.py`

The earlier specialist dependencies are separately anchored in:

`docs/archive/rmr_R1_parent_integrity_selection_holdout_history_anchor_20260909.md`

## Future-data rule

If the user later supplies genuinely newer data, do **not** resurrect this protocol automatically. Instead:

1. version the current reusable three-role data map forward;
2. preserve the certified R1 scale identity and current final certified bundle unless a separately authorized scientific identity says otherwise;
3. preregister any new challenge under the then-current authority before opening outcomes;
4. keep production authority false unless separately changed by explicit governance.

This retirement removes a stale future obligation while preserving its exact historical design for audit.
