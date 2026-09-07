# State sufficiency diagnostic results

Date: 2026-09-07. Protocol: `STATE_SUFFICIENCY_PROTOCOL.md`. Actions run `34130330205` succeeded; four frozen evaluator tests passed.

**Conclusion: elapsed time since first shock and recovery dwell age do not provide stable incremental predictive value beyond the current five-minute recovery ratio. Keep the state representation simple.**

## Frozen comparison

Fit pooled STAR50+CSI1000 2024 checkpoints (+5/+10/+15/+20) and evaluate on 2025 without tuning.

Training: 208 checkpoint rows, 54 first-shock episodes, 52 next-Unsafe outcomes.
Evaluation 2025: 81 rows, 22 episodes, next-Unsafe base rate 33.3%.

| Model | Inputs | 2025 log loss | Brier | AUC |
|---|---|---:|---:|---:|
| ratio_only | log(current 5m recovery ratio) | **0.57784** | 0.20188 | **0.73114** |
| plus_elapsed | ratio + elapsed time since shock | 0.58316 | 0.20250 | 0.72977 |
| plus_recovery_age | ratio + elapsed + time since last Unsafe | 0.57928 | **0.19834** | 0.73114 |

Paired event-cluster bootstrap delta log-loss versus `ratio_only` (negative would favor the challenger):

- `plus_elapsed`: point +0.0100; 95% interval **[-0.0140, +0.0334]**;
- `plus_recovery_age`: point +0.0065; 95% interval **[-0.0303, +0.0448]**.

Both intervals include zero and both point estimates worsen log loss. Recovery age has a slightly lower Brier score but no AUC/log-loss gain, so it does not justify an extra state variable.

## Already-opened 2026 consistency replay

This is descriptive only, not a new independent confirmation. 41 checkpoints from 12 events were reconstructable by this exact minute adapter.

| Model | 2026 replay log loss | Brier | AUC |
|---|---:|---:|---:|
| ratio_only | **0.74172** | **0.26734** | **0.72619** |
| plus_elapsed | 0.77936 | 0.28051 | 0.65952 |
| plus_recovery_age | 0.74533 | 0.26862 | 0.68571 |

The same qualitative result holds: adding clocks/history does not improve the simple ratio score.

## State-time strata

Within fixed current-state bands, early (+5/+10) versus late (+15/+20) next-Unsafe rates do not show a stable monotone elapsed-time effect across 2025 and the 2026 replay. Current state remains much more informative than the event clock.

## Implication

Do not add `elapsed_since_shock` or `time_since_last_Unsafe` to the durable state machine. The supported causal state output remains:

`current recovery_ratio = trailing completed-5m RMS / fixed pre-shock sigma_pre`

with `Unsafe >=1.5`, otherwise `Recovering`, and no online `Clean`.

The evidence is compatible with an approximately first-order state abstraction for the current research purpose: the latest activity state captures most of the usable short-horizon information found so far. This is not a proof of a Markov data-generating process.

No threshold, window, event definition or production policy is changed by this diagnostic.
