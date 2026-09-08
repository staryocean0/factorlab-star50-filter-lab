# CSI1000 HighVol onset-specificity placebo V1

Status: frozen before reading placebo market results.

## Question

The reusable Validation pool supports the frozen CSI1000 long acceleration candidate:

- `NormalVol -> HighVol`;
- recent 5m net return > 0;
- preceding non-overlapping 30m net return > 0;
- `tail2_share >= 0.60`;
- `tail1_share < 0.60`;
- enter at next minute open;
- hold exactly 3 minutes.

This diagnostic asks whether the `NormalVol -> HighVol` **transition itself** adds information, or whether the same slow-aligned two-minute acceleration works similarly at minutes where HighVol is already ongoing.

This is a falsification/interpretation study. It does not promote or retune the candidate.

## Data roles

- Development: 2021-01-01 through 2023-12-31; fully reusable.
- Validation: 2024-01-01 through 2026-08-21; reusable and dissectable under `DATA_USAGE_POLICY_V2`.
- BlackBox-V1: not queried.

## Candidate event rows

Reconstruct the frozen candidate from the 1m causal grid. Within each half-session:

1. current state is `HighVol` and previous minute state is `NormalVol`;
2. last five close-to-close 1m returns are valid and their net sum is positive;
3. the preceding non-overlapping 30 close-to-close 1m returns are valid and their net sum is positive;
4. `tail2_share >= 0.60` and `tail1_share < 0.60`;
5. entry is next minute open and exit is the open three minutes later;
6. all execution-path minutes are valid;
7. selected candidate trades cannot overlap, using the frozen rule `next_allowed_onset = onset_row + 1 + 3`.

The reconstructed candidate counts must match the frozen receipts: 104 Development trades and 129 Validation trades.

## Primary placebo controls

A control row must satisfy the **same price/path structure** and execution contract, except:

- current state is `HighVol`;
- previous minute state is also `HighVol`.

Thus the primary placebo is an already-ongoing HighVol minute, not a fresh onset.

Controls within +/-10 minutes of any selected candidate onset in the same half-session are excluded. A control may be used at most once.

## Matching

No future outcome is used in matching.

For each candidate, in deterministic chronological order:

1. prefer unused controls from the same year, same AM/PM half-session and same 15-minute clock bucket;
2. if unavailable, allow same year and same AM/PM half-session and record fallback tier 1;
3. otherwise leave the candidate unmatched.

Nearest-neighbour distance uses standardized past-only covariates:

- preceding 30m net return;
- recent 5m net return;
- `tail2_share`;
- `tail1_share`;
- current continuous volatility ratio (`5m RMS / preceding non-overlapping 30m RMS`).

Location and scale are computed from the eligible control pool only. No outcome is used to choose or rank controls.

## Primary estimand

For each matched pair:

`paired_diff_bp = candidate_future_3m_gross_bp - matched_control_future_3m_gross_bp`.

Report separately for Development and Validation, and by year:

- candidate count;
- matched count and coverage;
- mean candidate gross;
- mean control gross;
- mean paired difference;
- median paired difference;
- candidate/control hit rates;
- matching-distance summaries and fallback-tier counts.

## Inference

Use a deterministic trading-day block bootstrap of paired differences, 10,000 draws, separately for Development and Validation. Resample candidate trading days with replacement and keep all pairs attached to each sampled candidate day.

Report the 2.5%, 50% and 97.5% quantiles and fraction of bootstrap means > 0.

This is descriptive paired inference, not an exact permutation p-value.

## Interpretation

- Positive candidate-control difference with useful matching coverage: evidence that the HighVol **onset transition** carries incremental information beyond generic slow-aligned acceleration in ongoing HighVol.
- Near-zero difference: the trade structure is better described as generic slow-aligned acceleration; onset should not be treated as essential.
- Negative difference: onset gating is likely harmful relative to waiting until HighVol is established.

No threshold, holding period, direction or matching rule may be changed after seeing this placebo result within V1. BlackBox-V1 remains untouched.
