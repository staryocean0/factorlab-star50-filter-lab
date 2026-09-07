# Post-shock release model protocol

Date: 2026-09-07. Written after fixed release rules R1/R2/R3 were evaluated and found to have high false-release leakage, but before fitting this model.

Purpose: test whether a small, fixed, causal model can identify a subset of post-shock states that is safe enough to release. No hyperparameter or feature search.

## Split

- Fit on pooled 2024 events from both indices.
- Evaluate only on pooled 2025 events; report each index separately as descriptive small-n slices.
- All history is consumed development; this is sequential historical validation, not fresh OOS.

## Decision checkpoints

Only +5, +10, +15, +20 minutes after the first-shock minute. No per-minute best-time search.

## Features available by checkpoint

- elapsed minutes since shock: 5/10/15/20;
- trailing 5-minute RMS / pre-shock sigma;
- trailing 5-minute max absolute minute return / pre-shock sigma;
- trailing 2-minute RMS / pre-shock sigma;
- absolute event-minute return / pre-shock sigma;
- log pre-shock sigma;
- quiet-first indicator from the sealed taxonomy;
- index indicator;
- event-minute 3-second path top-3 increment share;
- event-minute 3-second path efficiency.

All are known by the checkpoint. Path descriptors use the already-corrected sealed event ledger; no hindsight control attributes enter the model.

## Target

`stable_next10 = 1` only when the two immediately following non-overlapping 5-minute blocks both have RMS / pre-shock sigma < 1.0. Missing/session-truncated outcomes are excluded from fitting/scoring, not treated as unsafe or safe.

## Estimator and release thresholds

`StandardScaler + LogisticRegression(C=1, class_weight=None, max_iter=2000, random_state=20260907)`.

No tuning. Candidate release probabilities are fixed at `P(stable_next10) >= 0.80` and strict sensitivity `>=0.90`.

## Evaluation

For 2025 report: decision-row coverage, stable-release precision, false-release share, event-level fraction with at least one release opportunity, median earliest release checkpoint, Brier score and ROC AUC when defined. A model that has high precision only by almost never releasing is not considered adequate.

Do not overwrite the negative fixed-rule results. If this model also fails, the next direction is conservative fixed Unsafe duration plus richer post-shock observations, not more threshold search on the same 77 events.
