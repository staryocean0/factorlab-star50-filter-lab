# Post-result benchmark — what if V3.2 matched percentiles were treated like a gate?

Date: 2026-09-07  
Status: **post-result diagnostic only; not a deployable gate and not a preregistered V3.3 outcome**.

Purpose: after the frozen V3.3 raw-score gate was weak, quantify how much additional concentration was present in V3.2's matched-control percentiles before spending another model version on conditional normalization.

## Why this is only a favorable benchmark

V3.2 measures the score at `e-2`, but builds each event's control pool using an anchor at the eventual event minute `e`: same year / half-session / exact event clock minute, `quiet_pre == True`, no first event, and explicitly `~near_first_tail_30m`. The latter depends on first-tail events within ±30 minutes and therefore contains future event information relative to e-2. The control pool also uses same-year history rather than a past-only frozen reference library.

Therefore its event percentile is valid as a mechanism/existence diagnostic but **cannot be used as an online e-2 risk score**. The numbers below are deliberately treated as a favorable retrospective benchmark, not as production performance.

## STAR50 event concentration

V3.2 has 19 eligible STAR50 quiet-first events. Treating percentile thresholds 0.90 / 0.80 / 0.70 as hypothetical top 10/20/30% conditional gates gives:

| Hypothetical conditional budget | All 19 events caught | Recall | Nominal lift |
|---:|---:|---:|---:|
| 10% | 5/19 | 26.32% | 2.63x |
| 20% | 7/19 | 36.84% | 1.84x |
| 30% | 9/19 | 47.37% | 1.58x |

Restricting descriptively to the same 2024–2025 16 events used by V3.3:

| Hypothetical conditional budget | Events caught | Recall | Nominal lift |
|---:|---:|---:|---:|
| 10% | 4/16 | 25.00% | 2.50x |
| 20% | 5/16 | 31.25% | 1.56x |
| 30% | 7/16 | 43.75% | 1.46x |

The raw V3.3 score and V3.2 matched percentile are strongly aligned on these 16 events: Pearson correlation ≈ **0.9751**. At the hypothetical top-20 cutoff, four of the five matched-percentile events are exactly the four events caught by V3.3's raw 20% gate; at top-30, six of seven overlap the six raw-gate events. Thus the matched normalization mostly compresses alarm-time scale rather than revealing a new event population.

The top-10 matched benchmark is superficially stronger (4/16 at a nominal 10% rank cutoff) while V3.3's absolute top tail catches 0/16. However this comparison cannot be promoted because V3.2's per-event percentile uses the non-causal control construction above.

## Decision

This benchmark does **not** justify threshold retuning or a complex classifier. It does justify one last narrow test of whether conditional normalization itself is causally implementable:

- fixed STAR50 V3.2 score only;
- exact e-2 feature time;
- reference library restricted to 2022–2023;
- match only on information available at feature time (clock / half-session and causal background state);
- never use `quiet_pre` at the future anchor, `near_first_tail`, event labels, or 2024–2025 distribution when constructing the conditional rank;
- retain the same 10/20/30% budgets with 20% primary.

If that strictly causal conditional-rank version does not materially improve on V3.3 under the frozen primary rule, close the single-score pre-first-shock gate route rather than adding model complexity.
