# Unsafe warning-fidelity economic stress — frozen protocol

Frozen: 2026-09-08, before Phase-5 market outputs are opened.

Status: consumed-history sensitivity / upper-bound study. It does **not** show that Unsafe can already be predicted before onset, and it does not authorize trading or production.

## Question

Assume a future warning system can reproduce the already-observed 5m Unsafe mask imperfectly. If warning quality is roughly 80%-90%, how much of the economic effect of the frozen Unsafe routing policies survives after missed Unsafe episodes and false alarms?

This deliberately separates two questions:

1. `observed Unsafe -> economic action` (studied in Phase 4);
2. `past information -> future Unsafe warning` (still awaiting genuinely new predictive data).

Phase 5 addresses only the first question under hypothetical warning fidelity. It is an optimistic conditional-utility stress, not a forecasting result.

## Frozen strategy and policies

Keep Phase-4 settings exactly:

- symbols: `000688.SH`, `000852.SH`;
- 5m bars;
- ~60m first-order causal Butterworth (`period_bars=12`);
- ~240m rolling sigma (`window=48`, ddof=0), hysteresis k=1;
- completed-bar decisions;
- two-bar delayed execution;
- half-session starts/ends flat;
- no lunch/overnight bridge;
- `Clean` disabled;
- true `Unknown` state always blocks admission and targets flat where Phase 4 specified.

Evaluate both frozen state policies without selecting between them:

- `unsafe_hard_off`;
- `unsafe_entry_block`.

`baseline_ungated` remains the common reference.

## Warning-fidelity scenarios

Use contiguous **true Unsafe runs** on quality-valid 5m decision bars as the error unit. A run is consecutive Unsafe decision bars within one half-session.

Scenarios:

- perfect observed state: recall=1.0, run precision=1.0;
- recall=.80, target run precision=.80;
- recall=.80, target run precision=.90;
- recall=.90, target run precision=.80;
- recall=.90, target run precision=.90.

No other fidelity level is examined.

### Misses

For each Monte Carlo draw, retain each true Unsafe run independently with probability equal to the scenario recall. A missed true run is treated as predicted non-Unsafe for routing purposes.

### False alarms

For each retained true run, create one false-alarm attempt with probability

`false_run_ratio = (1 - target_precision) / target_precision`.

Thus the expected number of false runs per retained true run matches the requested **run-level precision** before placement failures/collisions.

A false run must:

- occur in the same symbol and evaluation period;
- match the triggering true run's calendar year, half-session side, start-bar clock position and run length when a valid candidate exists;
- occupy only true non-Unsafe, non-Unknown, quality-valid decision bars;
- never cross lunch/close or overlap a true Unsafe run;
- be unioned with other predicted-Unsafe bars if false runs overlap each other.

Candidate sessions are sampled uniformly from the eligible same-year matched set. If no exact same-clock candidate exists, the false-alarm attempt is dropped and the realized precision is reported rather than silently changing the matching rule.

This design preserves the empirical Unsafe run-length and clock distribution without using outcome PnL to place false alarms.

## Monte Carlo

- 1,000 draws per symbol × period × fidelity scenario;
- seed `20260908`, with deterministic offsets by symbol/period/scenario;
- full two-bar execution and routing are recomputed for each synthetic warning mask.

Periods are kept separate:

- 2021-2025 pooled consumed history;
- 2026-01-05..2026-08-21 already-opened consistency replay.

No post-2026-08-21 data may be read.

## Costs

Keep Phase-4 symmetric index-level one-way friction stress:

- 0.5bp;
- 1.0bp;
- 2.0bp.

Do not insert IM-specific asymmetric fees into the two-index Phase-5 comparison.

## Primary outputs

For every symbol × policy × scenario × period report across Monte Carlo draws:

- median and 95% interval of gross PnL delta vs `baseline_ungated`;
- median and 95% interval of 1bp-cost net PnL delta vs baseline;
- fraction of draws with positive gross delta;
- fraction of draws with positive 1bp-net delta;
- median one-way turnover delta vs baseline;
- realized run recall and run precision distributions;
- median predicted-Unsafe run count / bar count;
- for policies whose perfect-state delta is positive, median fraction of perfect-state economic improvement retained.

Also retain per-draw output. Do not select the best fidelity/policy after viewing results.

## Required anchors

Before interpreting Monte Carlo output:

1. the perfect-state run must reproduce Phase-4 pooled policy deltas versus baseline for both symbols/policies within numerical tolerance;
2. baseline 5m annual fingerprints must continue to match the Phase-2 anchor;
3. false-alarm placement tests must prove no false run overlaps true Unsafe/Unknown or crosses half-session boundaries;
4. recall=precision=1 must create exactly the true Unsafe mask.

Any anchor failure invalidates the run.

## Interpretation

The primary practical question is not whether an 80%/90% classifier sounds accurate. It is whether the economic benefit survives **both misses and false alarms**.

Possible conclusions:

- state routing has a wide enough error budget that an 80%-90% warning could plausibly preserve useful value;
- value survives high recall but requires very high precision / low false-alarm burden;
- perfect-state benefit is too small/unstable to survive realistic warning error, so prediction research should not be justified by routing economics alone.

Even a favorable Phase-5 result does not validate a predictor. The actual warning model must later be frozen and tested on independent data after 2026-08-21.
