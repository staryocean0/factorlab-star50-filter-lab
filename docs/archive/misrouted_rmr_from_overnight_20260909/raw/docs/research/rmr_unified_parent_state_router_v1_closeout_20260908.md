# Unified parent-state router v1 closeout — 2026-09-08

Research identity: `rmr_unified_parent_normal_state_router_v1`

Final decision:

`ROUTER_V1_CLOSED_AFTER_DETAILED_VALIDATION_FAIL_NO_BLACKBOX_QUERY`

## What survived

The project still has two separately certified mechanisms:

- R1 trend-parent pullback recovery — BLACKBOX PASS;
- R2 range-parent boundary re-entry — BLACKBOX PASS.

Their qualitative relationship remains useful: one describes restoration inside an intact trend-like parent state and the other restoration after a failed excursion outside an intact range-like parent state.

## What failed

The stronger router hypothesis tried to encode both with one common standardized signed axis:

`state_consistency = lane_sign * (z(abs_drift)-z(overlap)+z(parent_eff))/3`.

That candidate improved pooled metrics and strongly improved R1, but degraded the R2 lane and both R2 cells in detailed 2021–2025 VALIDATION.

Therefore qualitative complementarity must not be simplified into a single common numeric score under this representation.

## No rescue

Do not create router v2 by:

- changing common-scaler population;
- switching to lane-specific standardization after seeing this result;
- altering axis weights;
- adding lane interactions;
- adding thresholds or nonlinear transforms;
- selecting a subset of R2 cells/years;
- using BLACKBOX behavior.

Any future synthesis identity requires a new independent theory and explicit program review.

## BLACKBOX status

Router v1 never reached BLACKBOX. Query #4 did not occur. The query ledger remains at three completed queries:

1. R1 PASS;
2. R5-C FAIL;
3. R2 PASS.

## Program implication

The research architecture should keep R1 and R2 as **separate certified specialists**, not force them into one common router score.

The unresolved problem is economic implementation. The tested simple index-level execution families for both R1 and R2 failed detailed VALIDATION. Further progress therefore requires execution/instrument theory rather than additional state-indicator or router tuning.

Production authority remains false.
