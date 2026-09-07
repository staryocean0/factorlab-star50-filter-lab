# Next independent snapshot protocol

Frozen: 2026-09-07, **before any same-semantics data after 2026-08-21 are opened for this task**.

Purpose: preserve the scientific value of the next incremental data snapshot. This protocol does not authorize trading or production use.

See `VALIDATION_READINESS.md` for the frozen event-count tiers and planning evidence.

## Data boundary

The current consumed validation snapshot ends at 2026-08-21.

The next independent time extension begins with the first complete same-semantics trading day after 2026-08-21 delivered by DataHub. Do not inspect post-shock outcome summaries from those days before the formal snapshot is sealed.

Use append-only native 1m index data for:

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
- Recovering display-band boundary at 1.0;
- missing/repair input -> Unknown;
- no online `Clean` transition.

Do not add elapsed time, dwell time, shock direction, background-sigma terms, other-index headline volatility, or static shock-severity grades to rescue a future result. Those additions did not show stable consumed-history increment.

## Readiness rule

The stopping/readiness unit is the **eligible first-shock episode**, not checkpoint rows.

- fewer than 10 pooled events: descriptive only;
- 10-19: limited validation;
- at least 20 pooled events: minimum formal core validation;
- at least 30 pooled events: preferred formal snapshot when practical.

For cross-index interpretation, require at least 6 eligible events from each index at the minimum tier, preferably 10 each at the preferred tier. If that representation floor is not met, report pooled results but do not call the result cross-index confirmation.

State-band row counts are reported after opening the formal snapshot; they are not used as an outcome-driven stopping rule.

## Primary core state test

At +5/+10/+15/+20 minute checkpoints after each eligible first shock:

1. compute current `recovery_ratio` from the latest five completed valid minutes;
2. compute the following-five-minute realized ratio using the same fixed `sigma_pre`;
3. classify current state as:
   - `Recovering`: ratio <1.5;
   - `Unsafe`: ratio >=1.5.

Primary table: 2x2 current-state vs following-five-minute Unsafe/Recovering transition matrix with raw counts.

Primary hypothesis:

`P(next Unsafe | current Unsafe) > P(next Unsafe | current Recovering)`.

Use 10,000 whole-event bootstrap resamples, seed 20260907. At a formal-tier snapshot, strengthening the durable state abstraction requires the 95% lower bound for this probability difference to be greater than zero.

## Primary continuous-score test

Report:

- Spearman correlation between current `recovery_ratio` and following-five-minute realized ratio;
- log-risk RMSE of simple persistence `predicted next ratio = current ratio`;
- event-cluster bootstrap interval for the core Unsafe-minus-Recovering next-Unsafe probability difference.

A positive continuous association is required for strengthening the current state abstraction.

## Secondary display-band diagnostics

Without changing the primary result, also report the existing display bands:

- Recovering-low <1.0;
- Recovering-high 1.0..1.5;
- Unsafe >=1.5.

Provide the full 3x3 transition matrix and the directional ordering

`Unsafe > Recovering-high > Recovering-low`

for next-Unsafe probability, but **do not use a small-sample reversal between Recovering-high and Recovering-low as the sole reason to reject the durable two-state abstraction**. Those bands are analytical displays, not separate causal states.

Also report:

- STAR50 and CSI1000 separately;
- transition probabilities by +5/+10/+15/+20 checkpoint;
- 15-minute future risk burden as a secondary diagnostic;
- right-censor/quality-loss counts;
- quiet-first vs prior-active taxonomy only if compatible 3s support is available.

## Formal acceptance interpretation

The stable state abstraction is strengthened only if, without retuning:

1. the core Unsafe-minus-Recovering next-Unsafe contrast is positive;
2. its event-cluster 95% lower bound is >0 at a formal-tier snapshot;
3. current ratio vs next ratio Spearman association is positive;
4. both index-specific point estimates are disclosed and any sign reversal is flagged.

Exact historical probabilities are not targets. A new snapshot may have different calibration while preserving the state ordering.

## Explicitly forbidden on the new snapshot

Before the primary report is sealed, do not:

- refit a recovery model;
- tune 1.0/1.5 thresholds;
- choose 2m/5m/10m after looking at outcomes;
- select the best checkpoint;
- reopen `Clean`;
- change first-shock thresholds;
- add previously rejected hidden variables to rescue results;
- use new data to choose constituent/microstructure features;
- silently revise prior snapshots.

## Failure policy

A formal-tier failure must be retained. First investigate data semantics, event incidence, censoring, and state nonstationarity. Do not immediately retune on the same snapshot.

`Clean` remains disabled regardless of this test. Reopening Clean requires its own future protocol and materially more independent events or materially different information.