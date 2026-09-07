# Post-shock state calibration V2 — frozen protocol

Date: 2026-09-08  
Branch: `research/post-shock-state-calibration-v2-20260908`  
Base scientific lineage: `b37775a9be3d1d188bce15fc6f5014866b92070a`

## 1. Question and scope

This is a narrow, results-blind continuation of the already-consumed post-shock recovery work. It does **not** reopen first-shock model selection, morphology tuning, trading, or a hard `Clean` release rule.

Question: after a sealed first shock, does the already-selected simple causal score — current trailing five-minute RMS divided by the event's pre-shock background sigma — calibrate future post-shock risk well enough to support an interpretable `Unsafe -> Recovering` state process? Does elapsed time add material descriptive information after conditioning on the current score state?

No new market data are requested for this experiment. No 2026 observations may be read. All evidence remains consumed historical development evidence, not fresh OOS.

## 2. Inherited frozen event universe

Use exactly the sealed `post_shock_recovery_v1` / V2 first-event universe for calendar years 2024 and 2025:

- STAR50 `000688.SH`: 52 events total across 2024–2025;
- CSI1000 `000852.SH`: 25 events total across 2024–2025.

Do not regenerate the event universe with a changed threshold, remove inconvenient events, add later events, or replace the source with a new carrier. Missing/session-truncated future observations are censored, never reclassified as low risk.

The checkpoint grid is fixed at `+5, +10, +15, +20` trading minutes after the sealed first-shock event, exactly matching the previous continuous recovery-score comparison. Checkpoints that lack the full future horizon because of the session boundary are excluded for that horizon only and counted as censored.

## 3. Fixed current score and states

At checkpoint `t`, define

`z_t = trailing_5m_RMS(t) / sigma_pre(event)`.

No fitted model is used for the primary analysis. State bins are inherited and fixed before V2 outcomes:

- `LOW_CANDIDATE`: `z_t < 1.0`;
- `RECOVERING`: `1.0 <= z_t < 1.5`;
- `UNSAFE`: `z_t >= 1.5`.

`LOW_CANDIDATE` is **not** a validated online `Clean` state. No result from this experiment may rename it `Clean`.

## 4. Fixed horizons and future outcomes

Evaluate horizons `h = 5` and `10` trading minutes.

For each eligible checkpoint, compute the same score at `t+h`, `z_{t+h}`, using only information available by `t+h` and the event's already-fixed `sigma_pre`.

Future state uses the same fixed boundaries. Primary binary risk outcome:

`future_unsafe_h = 1[z_{t+h} >= 1.5]`.

The continuous future score `z_{t+h}` is also reported. Do not replace it with returns, direction, P&L, drawdown, or another economic target.

## 5. Primary tables

For each horizon, report:

1. current-state -> future-state transition counts and row-normalized probabilities;
2. `P(future_unsafe_h | current_state)` with Wilson 95% intervals;
3. median and interquartile range of `z_{t+h}` by current state;
4. eligible checkpoint count, censored checkpoint count, and distinct event count.

Report pooled 2024–2025 only as a descriptive aggregate. The scientific stability checks are by calendar year (`2024`, `2025`) and by symbol where denominators allow.

## 6. Precommitted stability criterion

A cell is considered denominator-sufficient only if it contains at least `10` eligible checkpoint rows from at least `3` distinct events. Insufficient cells are reported but cannot establish or refute stability by themselves.

For a symbol/year/horizon stratum with all three current-state bins denominator-sufficient, risk ordering is `monotone` only if

`P(unsafe_future | LOW_CANDIDATE) <= P(unsafe_future | RECOVERING) <= P(unsafe_future | UNSAFE)`.

No threshold scanning, bin merging, isotonic refit, or post-result redefinition is allowed.

Overall adjudication:

- `state_calibration_supported`: monotone ordering in every denominator-sufficient symbol/year/horizon stratum that contains all three states, and pooled ordering is monotone at both horizons;
- `state_calibration_partially_supported`: pooled ordering is monotone at both horizons but one or more denominator-sufficient symbol/year/horizon strata are non-monotone or not all three bins are sufficiently represented;
- `state_calibration_not_supported`: pooled ordering is non-monotone at either horizon.

This is a calibration/risk-ordering statement only, not a release-policy acceptance.

## 7. Elapsed-time secondary audit

Elapsed time is secondary and cannot change the state thresholds. Use the already-fixed checkpoint values as four categories: `+5`, `+10`, `+15`, `+20` minutes. Do not create new optimized cutoffs.

Within each current state and horizon, report future-Unsafe probability by checkpoint. Elapsed time is considered to carry `residual_descriptive_information` only if, in the pooled table, the max-minus-min future-Unsafe probability across denominator-sufficient checkpoint cells within the same current state is at least `0.10`. This is descriptive; no causal interpretation and no new production timeout may be inferred.

## 8. Dependence and uncertainty

Repeated checkpoints from one shock are dependent. Therefore:

- Wilson intervals are row-level descriptive intervals and must be labelled as such;
- all tables must also report distinct event counts;
- a deterministic event-cluster bootstrap (`2000` resamples, seed `20260908`) is used for the pooled state-risk contrasts `UNSAFE - LOW_CANDIDATE` and `RECOVERING - LOW_CANDIDATE` at each horizon;
- bootstrap resampling unit is the sealed event ID, not checkpoint rows.

Bootstrap intervals are supporting uncertainty diagnostics, not a parameter-selection device.

## 9. Data and implementation gates

Before scientific output:

1. assert years are only 2024/2025;
2. assert symbols are only `000688.SH` and `000852.SH`;
3. assert no duplicate `(event_id, checkpoint_min)` rows;
4. assert checkpoint set is a subset of `{5,10,15,20}`;
5. assert `sigma_pre > 0` and all used RMS values are finite/non-negative;
6. assert the inherited sealed event count is exactly 52 STAR50 + 25 CSI1000 when the full event ledger is loaded;
7. preserve session truncation/censoring; do not bridge lunch or overnight to manufacture a horizon;
8. record input file/blob/hash identities and execution commit.

If the exact inherited event/checkpoint surface cannot be reconstructed or identity-bound from existing repo evidence, fail closed with `inherited_checkpoint_surface_not_reproducible`; do not silently create a new event universe under the V2 name.

## 10. Forbidden outputs and frozen decisions

This experiment does not read or evaluate:

- 2026 data;
- direction labels;
- third-wave labels;
- returns / P&L / drawdown effectiveness;
- fresh OOS;
- trading, sizing, execution, or production.

It also does not change `morphology_replication_not_yet_accepted`, does not resolve the separate v0.6.17 prior-identity blocker, and does not authorize a `Clean` online transition.

Any follow-up model or threshold must be a separately versioned protocol frozen before its outcomes are viewed.
