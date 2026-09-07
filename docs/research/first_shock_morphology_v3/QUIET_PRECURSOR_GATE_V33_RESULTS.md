# STAR50 quiet-first precursor gate v3.3 — frozen-score full-universe test

Date: 2026-09-08  
Branch: `research/star50-quiet-precursor-gate-v33-20260908`  
Preregistered protocol commit: `5953dcb6623f68bda7d76b5d46f1226be359cc1b`  
Frozen scientific implementation/test ref: `baaffa2b3c75d304fa7604e2c81db27b9680e080`  
Successful Actions run: `34143072827`  
Workflow-only dependency fix commit: `c4f456ae47109905aa9a9f3a9ceb6111f2c157be`  
Tests: **6 passed**. No 2026 read, no classifier fit, no new morphology feature, no trading/P&L/OOS evaluation.

## Question

V3.2 found that STAR50 quiet-first tail events had an elevated preregistered cross-scale score at `e-2` versus volatility-matched quiet controls. V3.3 asked a stricter operational question: can that *same frozen score*, without a classifier or new feature, rank future quiet-first-tail risk over the full eligible quiet-time decision universe?

The score remained exactly:

`0.5 * [(logE30-logE240) + (logE60-logE240)]`

2022–2023 were used only to set morning/afternoon × minute 80th-percentile thresholds. Labels were not used in calibration. 2024 and 2025 were evaluated separately with those frozen thresholds. The future label was a frozen V3 quiet-first-tail event in `t+2..t+15` within the same half-session. A common-volatility comparator used the same calibration design on `log_sigma_pre`.

## Primary result

| year | eligible rows | positive rows | scale risk coverage | risk label rate | Clean label rate | risk-Clean diff | risk ratio | score AUC | event recall | permutation tail fraction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 20,155 | 104 | 16.05% | 0.989% | 0.426% | +0.564 pp | 2.325 | 0.634 | 6/13 = 46.15% | 18.80% |
| 2025 | 21,559 | 15 | 18.04% | 0.0257% | 0.0792% | **-0.0535 pp** | 0.325 | **0.432** | 1/2 = 50.00% | 55.24% |

The primary gate therefore **fails the preregistered promotion condition**. The full-universe relationship is positive in 2024 but does not repeat in 2025; the 2025 row-level ordering reverses. No threshold was changed after observing this result.

Event-level evidence is also support-limited: 2024 had 14 frozen quiet-first events, 13 with any eligible strict prewindow and only 2 with a complete prewindow; 2025 had only 2 events and neither had a complete prewindow. Thus 2025 is too small to support a strong negative mechanism claim. It is nevertheless sufficient to fail the frozen requirement that the gate repeat in both evaluation years.

For the scale gate, median maximum strict lead among hit events was 14.5 minutes in 2024 and 4 minutes in 2025. These are descriptive conditional-on-hit quantities, not deployable lead-time guarantees.

## Common-volatility comparator

The simple `log_sigma_pre` 80th-percentile comparator was itself unstable:

- 2024: 28.57% coverage, AUC 0.444, risk-Clean difference -0.139 pp, event recall 6/13.
- 2025: 29.92% coverage, AUC 0.713, risk-Clean difference +0.144 pp, event recall 2/2, but only two eligible events.

This reinforces that the two evaluation years differ materially in both event prevalence and state composition. It does **not** rescue the scale gate.

## Relation to V3.2

The v3.3 failure does not erase the V3.2 event-vs-control diagnostic. V3.2 conditioned each event on same-year/same-half/same-minute quiet controls matched in `(log sigma_pre, log rv480)`; STAR50 event percentiles were 92.96% (2022, n=1), 63.00% (2023, n=2), 63.50% (2024, n=14), and 69.00% (2025, n=2). In contrast, V3.3 intentionally used the raw frozen score against a historical time-of-day threshold in the full decision universe.

The discrepancy suggests a specific follow-up hypothesis: the useful quantity, if any, may be the cross-scale score **conditional on the common volatility state**, rather than its raw level. That hypothesis is post-v3.3 and must be tested only in a newly frozen diagnostic; it cannot be used to reinterpret v3.3 as a success.

## Decision

Status: **NOT PROMOTED**.

- Do not create a STAR50 risk gate from the raw V3.2 score.
- Do not scan alternative quantiles on 2024/2025.
- Do not fit a classifier to these sparse quiet-first events.
- Preserve V3.2 as a consumed-history precursor-existence diagnostic and V3.3 as the negative full-universe raw-score translation test.
- A legitimate next test may operationalize the *already-existing V3.2 volatility matching* using only historical calibration controls, with no new morphology feature or label-based threshold fitting.

All results remain consumed historical development (`fresh_oos=false`) and provide no trading or production authority.
