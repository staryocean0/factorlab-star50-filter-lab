# Next-snapshot validation readiness

Frozen: 2026-09-07, before same-semantics post-2026-08-21 outcomes are opened for this task.

Purpose: decide when the next independent time extension contains enough first-shock episodes to justify one formal validation run. This is a planning rule, not a production acceptance rule and not permission to tune thresholds.

## What is being validated

The durable object is deliberately simple:

`observed first shock -> post-shock episode {Unsafe <-> Recovering}`

with

`recovery_ratio = RMS(last 5 completed valid 1m returns) / fixed pre-shock sigma_pre`.

Primary causal state boundary remains `Unsafe >= 1.5`. `Recovering-high` (1.0..1.5) and `Recovering-low` (<1.0) are diagnostic display bands only. `Clean` remains disabled.

## Why event count, not checkpoint count, controls readiness

Each first-shock episode contributes several +5/+10/+15/+20 checkpoints, so checkpoint rows are dependent. The readiness unit is therefore the **eligible first-shock episode**, not individual rows.

State-band row counts are reported after the run, but they are not used as an outcome-driven stopping rule.

## Empirical planning calculation

Using already-consumed 2024-2026 episodes only for sample-size planning, whole events were resampled with replacement while retaining all checkpoints inside each event.

This is **not formal power analysis** and assumes the future event mix resembles the consumed history. It is only a practical stability guide.

Observed pooled consumed-history next-Unsafe probabilities were approximately:

- current Unsafe: 53.9%;
- current Recovering (all values <1.5): 15.3%;
- difference: about +38.6 percentage points.

For the more extreme display-band contrast Unsafe minus Recovering-low, the observed difference was about +43 percentage points.

Empirical event-resampling stability for the Unsafe-minus-Recovering-low difference:

| Resampled first-shock events | median difference | 2.5%-97.5% empirical range | strict three-band order retained |
|---:|---:|---:|---:|
| 10 | +42.7pp | +6.2 to +69.5pp | ~67.7% |
| 15 | +43.1pp | +15.7 to +65.0pp | ~76.5% |
| 20 | +43.3pp | +19.7 to +62.8pp | ~79.8% |
| 25 | +42.7pp | +22.9 to +60.6pp | ~81.5% |
| 30 | +43.2pp | +25.2 to +60.0pp | ~85.0% |
| 40 | +43.4pp | +27.2 to +57.7pp | ~89.0% |

The continuous current-ratio / next-ratio association stayed positive in essentially all of these consumed-history resamples. Again, these percentages are planning diagnostics, not future guarantees.

The important implication is that **the durable two-state contrast is much easier to validate than requiring Recovering-high to sit strictly between Unsafe and Recovering-low in every small snapshot**. Since high/low are not causal states, the next protocol should not fail the core state abstraction solely because those display bands reverse under small-sample noise.

## Frozen readiness tiers

Count only eligible first-shock episodes produced by the already-frozen event definition.

- `<10 pooled events`: descriptive only; do not interpret as an independent validation.
- `10-19`: limited validation; publish results but do not strengthen or weaken the durable state abstraction from sampling noise alone.
- `>=20 pooled events`: **minimum formal core validation threshold**.
- `>=30 pooled events`: **preferred validation snapshot**; use this if accumulation can continue without a materially important delay.
- `>=40 pooled events`: stronger stability tier, but do not wait indefinitely or cherry-pick calendar endpoints merely to reach it.

Cross-index wording also requires representation from both indices:

- at least 6 eligible first-shock events from each index for minimum cross-index interpretation;
- preferably at least 10 from each index for the preferred tier.

If the pooled threshold is met but one index is below its floor, run and report the snapshot, but call it pooled validation with an underpowered per-index view—not cross-index confirmation.

## Primary acceptance criteria for the next formal snapshot

The next formal snapshot strengthens the durable state abstraction only when all of the following hold without retuning:

1. **Core state contrast:**
   `P(next 5m Unsafe | current Unsafe) > P(next 5m Unsafe | current Recovering)`.
2. Event-cluster bootstrap (10,000 resamples, seed 20260907) for the above probability difference has a **95% lower bound > 0** at the formal tier.
3. Continuous `recovery_ratio` has a **positive Spearman association** with the following-five-minute realized ratio.
4. The same signs are not produced solely by one index; both index-specific point estimates are reported and any sign reversal is explicitly flagged.
5. Quality/censoring losses and state-support counts are disclosed; Unknown is never converted to Recovering.

The following are secondary diagnostics, **not core pass/fail conditions**:

- strict `Unsafe > Recovering-high > Recovering-low` next-Unsafe ordering;
- exact calibration percentages matching 2024-2026;
- multi-horizon 15-minute burden ordering;
- per-index confidence intervals when the per-index sample is small.

A failure of a secondary display-band ordering does not invalidate the two-state abstraction by itself.

## Failure policy

If the core probability contrast reverses, its event-cluster interval includes zero at an adequately sized snapshot, or the continuous association turns non-positive:

- retain the failure;
- first audit data semantics / event incidence / regime shift;
- do not change 1.5, 5m, sigma_pre, checkpoints, or event thresholds on that same snapshot;
- do not add elapsed time, shock direction, background sigma, other-index volatility, or static shock-severity variables merely to rescue the result.

## Clean remains out of scope

Meeting any event-count tier does **not** validate `Clean`.

Reopening online Clean requires a separate preregistered protocol plus either materially more independent episodes or materially different information. The current next-snapshot test is only for persistence and continuous recovery-state measurement.

## Operational note for data accumulation

The data tool may continue delivering immutable complete-day snapshots after 2026-08-21. A readiness check may count frozen first-shock events and basic quality support, but must not inspect or optimize post-shock outcome summaries before the chosen formal snapshot is sealed.

Monthly incremental delivery remains sufficient.