# Unified parent-state router program review — 2026-09-08

Program context: two complementary mechanisms are already independently certified under the reusable three-role data policy:

- R1 `rmr_cross_scale_pullback_parent_integrity_v2` — trend-like intact parent, BLACKBOX PASS;
- R2 `rmr_range_boundary_parent_integrity_v2` — range-like intact parent, BLACKBOX PASS.

R5-C failed BLACKBOX and is closed. The tested R1/R2 simple index-level economic execution families failed detailed VALIDATION and are also closed.

## Review decision

Approve exactly one non-economic synthesis identity:

`rmr_unified_parent_normal_state_router_v1`

This is **not** a new broad indicator lane. It may use only features and event geometries already present in the two certified mechanisms.

## Scientific question

> Can one signed parent-state consistency variable explain restoration probability across both certified mechanism families after each family's local event geometry is already accounted for?

If yes, the project gains one common parent-state axis rather than two unrelated specialist scores. That would provide a principled architecture for later routing or instrument research without tuning the closed economic implementations.

## Frozen parent-state axis

Use one common DEV-fitted standardization for the already-certified parent features:

- `abs_drift`
- `overlap`
- `parent_eff`

Define:

`trend_axis = (z(abs_drift) - z(overlap) + z(parent_eff)) / 3`

For an R1 event:

`state_consistency = +trend_axis`

For an R2 event:

`state_consistency = -trend_axis`

Thus positive `state_consistency` always means that the parent structure matches the event family's normal-state hypothesis:

- R1: trend-like intact parent;
- R2: range-like intact parent.

No weights, sign, threshold or normalization window may be searched.

## Frozen event families

Use only original certified event/outcome geometry:

- R1 PAIR_A: S1 inside S2, recovery vs failure;
- R1 PAIR_B: S2 inside S3, recovery vs failure;
- R2 PAIR_A: S1 outside S2, re-entry vs continuation;
- R2 PAIR_B: S2 outside S3, re-entry vs continuation.

Recode each positive outcome as `restoration=1`, each negative outcome as `restoration=0`.

## Local geometry baselines

Fit one DEV-only baseline probability model per cell:

- R1 cells: `severity` only;
- R2 cells: `outside_ratio + break_speed + local_vol_ratio`.

Each local baseline uses `StandardScaler + LogisticRegression(C=1, L2, lbfgs)`.

Convert each event's DEV-frozen local baseline probability to:

`base_logit = logit(clip(p_base, 1e-6, 1-1e-6))`.

## Pooled router comparison

Pool the four cells after local baseline scoring.

Baseline pooled model:

`base_logit + lane_R2 + pair_B`

Candidate pooled model:

`base_logit + lane_R2 + pair_B + state_consistency`

where:

- `lane_R2 = 1` for R2 and `0` for R1;
- `pair_B = 1` for the coarse S2/S3 pairing and `0` for the fine S1/S2 pairing.

Both pooled models use `StandardScaler + LogisticRegression(C=1, L2, lbfgs)`.

No interactions, calibration search, threshold search, model-family search or hyperparameter search are allowed.

## Data roles

- DEV: `2015-01-05 .. 2020-12-31`
- VALIDATION: `2021-01-01 .. 2025-12-31`
- reusable BLACKBOX: `2026-01-05 .. 2026-08-21`

BLACKBOX may not be read during development or detailed validation.

## Detailed VALIDATION gates

Minimum resolved counts:

- R1_A >= 800
- R1_B >= 300
- R2_A >= 250
- R2_B >= 80

All of the following are required:

1. pooled candidate Brier < pooled baseline Brier;
2. pooled candidate log-loss < pooled baseline log-loss;
3. R1-lane pooled candidate Brier and log-loss both improve;
4. R2-lane pooled candidate Brier and log-loss both improve;
5. candidate Brier improves in each of the four individual cells;
6. pooled annual Brier improvement is positive in at least 4 of 5 years (2021–2025);
7. DEV candidate coefficient on `state_consistency` is strictly positive.

Failure of any gate closes router v1 before BLACKBOX.

## Final refit and BLACKBOX

Only after full VALIDATION PASS may the exact frozen recipe be refit once on DEV+VALIDATION through 2025-12-31.

If reached, BLACKBOX query number = 4.

Minimum BLACKBOX resolved counts:

- R1_A >= 80
- R1_B >= 30
- R2_A >= 30
- R2_B >= 10

BLACKBOX PASS requires:

- pooled Brier and log-loss improve;
- both R1 and R2 lane pooled Brier and log-loss improve;
- each of the four cells has lower Brier under the candidate.

If any cell is below minimum sample: `INSUFFICIENT`.
Otherwise any gate failure: `FAIL`.
Otherwise: `PASS`.

Public BLACKBOX output remains only `PASS / FAIL / INSUFFICIENT`. No counts, metrics, subperiods, events or failure details may be released.

## Explicitly forbidden

- new indicators or additional parent features;
- changing the three signed axis weights;
- choosing a state-consistency cutoff;
- interactions between lane and state score;
- scale search;
- probability calibration search;
- PnL, entry, exit, cost or portfolio optimization;
- modifying R1 or R2 certified event definitions;
- BLACKBOX detail inspection;
- router v2 rescue based on hidden recent-period behavior.

## Program consequence

If router v1 passes BLACKBOX, treat the common signed parent-state axis as a certified synthesis layer above R1/R2. Economic work still remains separately unproven.

If router v1 fails or is insufficient, retain R1 and R2 as separate certified mechanisms and do not infer which lane or period caused the failure.

Production authority remains false.
