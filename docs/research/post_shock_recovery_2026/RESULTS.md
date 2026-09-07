# 2026 post-shock recovery held-out validation results

Date: 2026-09-07. Branch: `research/post-shock-recovery-2026-validation`.

**Conclusion: the 2026 held-out snapshot confirms that risk remains elevated after the first shock, but it does not validate any online `Clean` release rule. Keep `Unsafe -> Recovering`; do not promote `Clean`.**

## Execution and input

Owner explicitly authorized 2026 for this research validation. The new independent pack covers 2026-01-05 through 2026-08-21, 154 complete trading days. It contains two 1m partitions (36,960 rows each) and two 3s source-observation partitions (730,261 STAR50 rows; 730,395 CSI1000 rows).

Actions run `34113054287` completed successfully on isolated branch `research/post-shock-recovery-2026-actions-20260907`. All four file SHA256s, row counts and date ranges matched the new manifests. No model was refit or threshold tuned on 2026. Artifact `10015140042` has SHA256 `f31e3019fa7cfad7858529d16bd927b8a16374dd22b4c0d5e46d1836e55b8981`; the cloud session independently rechecked the nine output-manifest files with zero hash/size mismatches.

This snapshot is held-out relative to the prior recovery research, but the repository continues to mark it `fresh_oos=false`: this is historical research validation, not production/live evidence.

## Event count

Frozen event definition produced only 14 eligible first-shock events:

- STAR50: 8 events;
- CSI1000: 6 events.

Context taxonomy: STAR50 2 `quiet_first`, 4 `prior_directional`, 2 `prior_roundtrip_or_active`; CSI1000 3/1/2 respectively. The sample is small, so percentages below are evidence direction, not precise population estimates.

## 1. Post-shock risk remains elevated

Future-five-minute `Unsafe` means RMS >=1.5x the pre-shock background sigma.

| Lag after event close | STAR50 Unsafe | CSI1000 Unsafe |
|---|---:|---:|
| 0m | **75%** (8) | **50%** (6) |
| +5m | **50%** (6) | **50%** (6) |
| +10m | **50%** (6) | **50%** (4) |
| +15m | **50%** (6) | 25% (4) |
| +30m | 20% (5) | 0% (4) |

The central qualitative finding from 2024-2025 therefore survives: the first shock is followed by a materially elevated short-horizon risk state, not an immediate return to normal.

## 2. Recovery duration is not a universal fixed timeout

Censor-adjusted KM median descriptive release-start:

- STAR50: **27 minutes**, with 50% censoring;
- CSI1000: **14 minutes**, with 16.7% censoring.

Because the retrospective release definition needs two consecutive low-volatility five-minute blocks, an online observer could only confirm those median release starts roughly ten minutes later: about 37m and 24m respectively.

These do not match the prior 2024-2025 medians closely enough to justify a universal fixed timer. Small n and session censoring are material.

## 3. Current volatility persistence remains useful, but no single predictor wins stably

At +5/+10/+15/+20 checkpoints, predict next-five-minute risk ratio.

Pooled 2026:

- trailing-5m persistence: log-RMSE **0.536**, Spearman **0.433**;
- previously frozen multivariate ridge: log-RMSE **0.464**, Spearman **0.455**.

In 2025 the simple persistence predictor had been better. In 2026 the frozen ridge is modestly better on RMSE and rank. Because there are only 41 checkpoint rows from 14 events and the ordering reverses across validation periods, do **not** replace the simple state score or refit the ridge from this result. Continue to report both; keep trailing-five-minute activity as the transparent primary state measurement.

## 4. No online Clean release rule passes

Previously frozen simple rules still have high false-release rates. Pooled evaluable precision / false-release share:

- R1: 40.0% / **60.0% false**;
- R2: 44.4% / **55.6% false**;
- R3: 44.4% / **55.6% false**.

Fixed timers are also unstable: +10m precision 20%; +15m and +20m 11.1%; +30m 57.1% on only seven evaluable events.

The previously frozen release logistic has pooled AUC 0.672 but maximum predicted stable probability only **0.605**. It produces **zero** observations at the preregistered 0.80 or 0.90 release thresholds.

The fixed 3s path models also produce zero observations >=0.80/0.90. Their pooled common support is only 10 events; maximum probability across E0/E2/E5 is 0.472. No high-confidence `Clean` transition is supported.

## Research state after 2026 validation

- **Unsafe:** empirically supported immediately after a first shock; risk remains high over the next several minutes.
- **Recovering:** supported as a continuous declining-but-reactivating state. Use current trailing-5m RMS / pre-shock sigma as the transparent primary score; retain the frozen ridge only as a comparator.
- **Clean:** **not validated as an online state transition.** Do not use a fixed timeout, simple cooling rule, frozen release model, or 3s path model as a safe-release gate.

The correct next scientific action is **not** more tuning on 2026. Further `Clean` validation requires additional genuinely independent events after this snapshot or materially different information. The same-semantics source currently ends at 2026-08-21, so no further independent time extension is available in this pack.

No trading/backtest/production authority is granted by this result.
