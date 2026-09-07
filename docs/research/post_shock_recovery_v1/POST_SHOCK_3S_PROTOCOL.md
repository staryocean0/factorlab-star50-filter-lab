# Post-shock 3-second recovery prediction protocol

Date: 2026-09-07. Written after the minute-only release model showed ranking signal but no >=0.80 release probability.

Goal: at exactly +5 minutes after a first shock, test whether the observed 3-second path since the shock improves prediction that the **next 10 minutes** will remain stably below pre-shock background.

## Split and target

- Fit pooled 2024 events, evaluate pooled 2025 events.
- Target `stable_next10=1` when the next two non-overlapping five-minute minute-return blocks each have RMS / pre-shock `sigma_pre < 1.0`.
- Exclude session-truncated/unknown targets; never convert them to safe.

## Nested feature sets

**E0 event-only:** absolute event z-score, log pre-shock sigma, quiet-first flag, index flag, event-minute 3s top-3 increment share, event-minute 3s path efficiency.

**E2:** E0 plus post-shock first 2 minutes of raw 3-second path descriptors: RMS increment / sigma, max absolute increment / sigma, net move / sigma, observed range / sigma, path efficiency, top-3 share, sign-change rate.

**E5:** E2 plus the same descriptors computed over the first 5 post-shock minutes.

A post-shock path window is eligible only when source observations cover the interval without same-second ambiguity and without source gaps >3 seconds; otherwise its features are Unknown. No interpolation.

## Estimator and thresholds

For each nested set separately: `StandardScaler + LogisticRegression(C=1, class_weight=None, max_iter=2000, random_state=20260907)`. No hyperparameter search or feature selection.

Release thresholds remain fixed at predicted `P(stable_next10)>=0.80` and strict sensitivity `>=0.90`.

## Evaluation

Report 2025 row count, event count, stable base rate, AUC, Brier, release coverage and stable-release precision at 0.80/0.90. E2/E5 must be compared with E0 on the same eligible event set. Do not select the best model by 2025 outcome.

All history is consumed development. This is post-shock recovery research only; no pre-first-shock prediction or trading claim.
