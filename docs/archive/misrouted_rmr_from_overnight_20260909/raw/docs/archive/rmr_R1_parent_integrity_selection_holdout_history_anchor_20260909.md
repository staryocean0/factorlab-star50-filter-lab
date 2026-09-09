# R1 parent-integrity selection/holdout history anchor

Date: 2026-09-09

Identity: `rmr_cross_scale_pullback_parent_integrity_v2`

This anchor preserves the superseded specialist selection/holdout implementation before removing it from the current repository surface.

## Exact historical surface

The final pre-cleanup tree is preserved at commit:

`5fc178352fe0fefdaa8415881dc6e7aa5d2ba3a5`

At that commit the completed specialist surface still contained:

- `docs/research/rmr_R1_parent_integrity_v2_preanalysis_20260908.md`
- `docs/research/reversal_mean_reversion_R1_parent_integrity_v2_selection_adjudication_20260908.md`
- `docs/research/reversal_mean_reversion_R1_parent_integrity_v2_holdout_adjudication_20260908.md`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_selection_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_selection_execution_freeze_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_holdout_protocol_v1.json`
- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_holdout_execution_freeze_v1.json`
- `docs/governance/cloud_session_20260908_rmr_R1_parent_integrity_v2_parameter_freeze_v1.json`
- `scripts/run_rmr_R1_parent_integrity_v2_selection.py`
- `scripts/evaluate_rmr_R1_parent_integrity_v2_holdout.py`
- `tests/test_rmr_R1_parent_integrity_v2_selection.py`
- `tests/test_rmr_R1_parent_integrity_v2_holdout.py`

## Why this surface is superseded

The project subsequently moved to the permanent reusable three-role data policy and rebuilt the certified R1 reproduction path. Current R1 authority is now carried by:

- `docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_state_v1.json`
- `docs/governance/reversal_mean_reversion_R1_reusable_blackbox_protocol_v1.json`
- `docs/governance/rmr_R1_reusable_blackbox_parameter_freeze_v1.json`
- `docs/research/rmr_R1_reusable_validation_adjudication_20260908.md`
- `docs/research/rmr_R1_reusable_blackbox_certification_20260908.json`
- `scripts/run_rmr_R1_reusable_dev_validation.py`
- `scripts/certify_rmr_R1_reusable_blackbox.py`

The certified final bundle is:

`41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`

The older cloud-session bundle `e618a5a06a803f4464267e69e39f98fa316fd572f40efcb3f9e40fc25df2779c` is historical and must not override the reusable final bundle.

## Governance

Removing the old specialist surface does not alter the R1 scientific conclusion, frozen scale identity, certified bundle, BLACKBOX query #1 decision, or production authority. Git history plus this anchor preserves exact reproduction of the superseded stage.

No BLACKBOX query is performed by this cleanup. Completed BLACKBOX query count remains 3. `production_authority=false`.
