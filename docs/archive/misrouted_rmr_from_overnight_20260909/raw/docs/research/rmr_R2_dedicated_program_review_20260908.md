# R2 dedicated specialist program review — 2026-09-08

Decision:

`APPROVE_ONE_BOUNDED_R2_DEDICATED_SPECIALIST_IDENTITY`

Proposed identity:

`rmr_range_boundary_parent_integrity_v2`

## Why R2 is eligible for one dedicated review

Broad Stage-1 did **not** close R2. It placed R2 on HOLD:

- fine-scale behavior was unstable;
- the coarse combined model showed mild positive information;
- the parent-range state by itself did not cleanly isolate the mechanism from excursion geometry.

R2 therefore differs from the closed R3/R4/R5-A/R5-B/R6/R7 identities. It also differs from inventing an R8/R9 indicator: this is a dedicated test of an already registered broad mechanism class.

The historical R2 event is retained unchanged:

> Price has moved outside the high/low envelope formed by the last two completed parent-scale directional-change waves by one lower-scale threshold, but has not yet reached the frozen parent-scale continuation boundary. The outcome is first re-entry to the old range edge versus continuation to the parent-scale boundary.

## What was wrong with the broad comparison

The broad comparison used:

- `outside_ratio` alone;
- parent-state features alone;
- a large combined object containing excursion, parent state, break speed and local volatility.

That made it difficult to answer the clean causal question:

> Does an intact parent **range** add information beyond the geometry and speed of the attempted breakout itself?

## Dedicated v2 representation

The breakout-geometry baseline is fixed as:

`outside_ratio + break_speed + local_vol_ratio`

The only added state variable is a one-dimensional parent-range-integrity score:

`range_integrity = (-z(abs_drift) + z(overlap) - z(parent_eff)) / 3`

where the three z-scores are fit on DEV only for detailed VALIDATION.

Theory:

- lower absolute parent drift = more range-like;
- higher overlap = stronger confinement;
- lower path efficiency = less trend-like parent structure.

Higher `range_integrity` is preregistered to increase re-entry-first probability.

## Frozen scope

- scales: S1 outside S2 and S2 outside S3, both co-primary;
- event/outcome geometry: identical to the broad R2 engine;
- DEV: 2015-01-05 .. 2020-12-31;
- VALIDATION: 2021-01-01 .. 2025-12-31;
- BLACKBOX: 2026-01-05 .. 2026-08-21, only if detailed VALIDATION passes;
- model: StandardScaler + LogisticRegression(C=1, L2, lbfgs);
- exactly two model objects per scale: geometry baseline vs geometry + range_integrity;
- no interactions, scale search, breakout-distance threshold search, speed-window search, vol-window search or PnL.

## VALIDATION gates

Each scale must satisfy all of:

- pooled resolved: S1 >= 250; S2 >= 80;
- each 2021–2025 year: S1 >= 30; S2 >= 10;
- augmented pooled Brier strictly below baseline;
- augmented pooled log-loss strictly below baseline;
- annual Brier improvement positive in at least 4 of 5 years;
- fitted DEV `range_integrity` coefficient strictly positive.

Both scales must pass. Only then may one preregistered DEV+VALIDATION refit be frozen and submitted to the reusable BLACKBOX.

## BLACKBOX policy

If reached, BLACKBOX output is only `PASS / FAIL / INSUFFICIENT` under the permanent three-role policy. No scale-specific or subperiod breakdown may be released.

A BLACKBOX FAIL/INSUFFICIENT closes this v2 identity. It may not be rescued using hidden recent-period information.

## Budget decision

Approve this **one** R2 dedicated identity because it directly repairs an identification problem already visible in the broad design. Do not automatically create an R2 v3 or another broad lane if this identity fails.

Production authority remains false.
