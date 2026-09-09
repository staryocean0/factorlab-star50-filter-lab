# Unified parent-state router v1 VALIDATION adjudication — 2026-09-08

Research identity: `rmr_unified_parent_normal_state_router_v1`

Decision:

`VALIDATION_FAIL_BLACKBOX_NOT_QUERIED_CLOSE_ROUTER_V1`

## Audit note before the scientific run

The first workflow attempt failed before event construction because the implementation incorrectly tried to re-estimate the directional-change volatility scale under the later reusable DEV window. R1/R2 scale identity was already frozen by the certified mechanisms.

No router outcome was opened in that failed attempt and no BLACKBOX access occurred. The implementation was corrected to use the already-frozen `DEV_median_rvol20 = 0.013783308018456928`; the router protocol, state axis, models and gates were unchanged.

The corrected run passed 13 boundary tests before empirical execution.

## Frozen hypothesis

A single common DEV-fitted parent-feature standardization defined:

`trend_axis = (z(abs_drift)-z(overlap)+z(parent_eff))/3`

with:

- R1 `state_consistency = +trend_axis`;
- R2 `state_consistency = -trend_axis`.

Each of four cells first received its own local geometry baseline. A pooled baseline used `base_logit + lane_R2 + pair_B`; the only candidate increment was `state_consistency`.

## Detailed VALIDATION results

Total resolved validation events: **4,852**.

### Pooled

- baseline Brier: `0.1705735875`
- candidate Brier: `0.1684461772`
- improvement: `+0.0021274103`
- baseline log-loss: `0.5192986498`
- candidate log-loss: `0.5152452377`
- improvement: `+0.0040534121`

Pooled annual Brier improvement was positive in 2022, 2023, 2024 and 2025, and slightly negative in 2021. The predeclared 4/5 annual pooled gate therefore passed.

DEV coefficient on `state_consistency`: `+0.2552725902`, also passing its sign gate.

### R1 lane

Validation n = **1,800**.

- Brier `0.1833091950 -> 0.1762966522`, improvement `+0.0070125429`;
- log-loss `0.5455211307 -> 0.5295714035`, improvement `+0.0159497273`.

Both R1 cells improved:

- R1_A Brier improvement `+0.0067429168`;
- R1_B Brier improvement `+0.0076816535`.

### R2 lane

Validation n = **3,052**.

- Brier `0.1630624166 -> 0.1638161461`, deterioration `-0.0007537294`;
- log-loss `0.5038332286 -> 0.5067959919`, deterioration `-0.0029627634`.

Both R2 cells deteriorated:

- R2_A Brier improvement `-0.0005170085`;
- R2_B Brier improvement `-0.0012482556`.

## Gate result

Passed:

- all four sample minimums;
- pooled Brier;
- pooled log-loss;
- R1 lane Brier/log-loss;
- 4/5 annual pooled Brier direction;
- positive DEV state-consistency coefficient.

Failed:

- R2 lane Brier/log-loss;
- all-four-cells Brier improvement.

Therefore router v1 fails detailed VALIDATION.

## Scientific interpretation

R1 and R2 remain individually BLACKBOX-certified and qualitatively complementary, but the stronger synthesis claim is not supported:

> the two mechanisms cannot be collapsed into one common standardized signed parent-state axis under this frozen representation.

The pooled improvement is dominated by R1. Treating R2 as the exact numeric negative of R1's common-standardized state axis loses information that the dedicated R2 representation preserved.

This does **not** invalidate either certified mechanism. It rejects only the proposed common numeric router.

## BLACKBOX boundary

Because detailed VALIDATION failed:

- no final router refit was performed;
- BLACKBOX query #4 did **not** occur;
- the reusable query ledger remains at three completed mechanism queries;
- no 2026 router metrics, counts, subperiods or event details exist.

Production authority remains false.
