# Next independent snapshot protocol

Frozen: 2026-09-07, **before any same-semantics data after 2026-08-21 are opened for this task**.

Purpose: preserve the scientific value of the next incremental data snapshot. This protocol does not authorize trading or production use.

## Data boundary

The current consumed validation snapshot ends at 2026-08-21.

The next independent time extension begins with the first complete same-semantics trading day after 2026-08-21 delivered by DataHub. Do not inspect outcome summaries from those days before this protocol is applied.

Use the append-only 1m index data for:

- `000688.SH` STAR50
- `000852.SH` CSI1000

3s data are optional audit material and are not required for the primary state validation.

## Frozen event/state definitions

Do not change:

- operational first-shock definition;
- pre-shock `sigma_pre` construction;
- same-half-session episode boundary;
- five-minute rolling RMS numerator;
- fixed denominator `sigma_pre` for the whole episode;
- state boundary `Unsafe >= 1.5`;
- Recovering analytical sub-band boundary at 1.0;
- missing/repair input -> Unknown;
- no online `Clean` transition.

## Primary forward-state test

At +5/+10/+15/+20 minute checkpoints after each eligible first shock:

1. compute current `recovery_ratio` from the latest five completed valid minutes;
2. compute following-five-minute realized ratio using the same fixed `sigma_pre`;
3. classify current and following ratios into:
   - Recovering-low <1.0;
   - Recovering-high 1.0..1.5;
   - Unsafe >=1.5.

Primary table: full 3x3 current-to-next state transition matrix with raw counts.

Primary ordered hypothesis:

`P(next Unsafe | current Unsafe) > P(next Unsafe | Recovering-high) > P(next Unsafe | Recovering-low)`.

Do not change bins to improve this ordering.

## Primary continuous-score test

Report:

- Spearman correlation between current ratio and following-five-minute ratio;
- log-risk RMSE of simple persistence `predicted next ratio = current ratio`;
- event-cluster bootstrap interval for
  `P(next Unsafe | Unsafe) - P(next Unsafe | Recovering-low)`.

Bootstrap unit is the complete first-shock episode, not individual checkpoints. Use 10,000 resamples, seed 20260907.

## Minimum evidence policy

Always report the data even when small, but distinguish evidence strength:

- fewer than 10 pooled eligible first-shock events: descriptive only;
- 10-19: limited validation;
- at least 20 pooled events: primary pooled validation may be interpreted, while each index still reports its own count;
- do not invent extra event definitions to reach a sample threshold.

No minimum count turns the study into production acceptance.

## Secondary reports

Without selecting among them:

- STAR50 and CSI1000 separately;
- quiet-first vs prior-active event taxonomy if 3s path support is available;
- transition probabilities by +5/+10/+15/+20 checkpoint;
- right-censor/quality-loss counts.

Cross-index other-index volatility is not a primary feature because it did not show stable historical increment. Event-close severity descriptors are metadata only.

## Explicitly forbidden on the new snapshot

Before the primary report is sealed, do not:

- refit a recovery model;
- tune 1.0/1.5 thresholds;
- choose 2m/5m/10m after looking at outcomes;
- select the best checkpoint;
- reopen `Clean`;
- change first-shock thresholds;
- use new data to choose constituent/microstructure features;
- silently revise prior snapshots.

## Decision after the snapshot

The stable state abstraction is strengthened only if the forward ordering remains directionally coherent and the continuous recovery ratio retains positive forward association.

A failure must be retained. It should trigger investigation of data semantics or state nonstationarity, not immediate retuning on the same snapshot.

`Clean` remains disabled regardless of this primary test. Reopening `Clean` requires its own future protocol and materially more independent events or materially different information.
