# R1 / R2 certified-mechanism synthesis — 2026-09-08

## Current certified mechanism set

The reusable three-role program now has two BLACKBOX-certified mechanisms:

1. `rmr_cross_scale_pullback_parent_integrity_v2` — R1 trend-parent pullback recovery;
2. `rmr_range_boundary_parent_integrity_v2` — R2 range-parent boundary re-entry.

R5-C event density passed detailed VALIDATION but failed BLACKBOX and is closed under v2.

## Common structure

R1 and R2 are not unrelated signals. They are complementary tests of the same higher-level question:

> Is the parent normal state intact, and if so, what kind of normal state is it?

R1's parent-integrity orientation rewards:

- higher absolute parent drift;
- lower overlap;
- higher path efficiency.

R2's range-integrity orientation rewards the opposite:

- lower absolute parent drift;
- higher overlap;
- lower path efficiency.

Conceptually, they form two sides of a parent-state continuum:

`trend-like intact state  <——>  range-like intact state`

Observed lower-scale deviations then have different recovery objects:

- inside an intact trend: counter-move recovery toward the prior lower-wave start;
- outside an intact range: failed breakout / re-entry toward the old range edge.

## Program decision

Stop automatic mechanism discovery. The project already has two complementary certified mechanisms and one failed secondary specialist.

The next scientific budget should address **economic translation**, not create a third weak state indicator.

R1's first economic family was already tested and closed after three low-capacity implementations failed detailed VALIDATION. That family should not be tuned further.

R2 has not yet received economic translation. Its event geometry is particularly suitable because both economic sides are known causally at event time:

- re-entry target = old range edge;
- continuation/failure boundary = parent-scale continuation level.

Therefore approve one bounded R2 economic identity before any unified router or portfolio allocation work.

## Approved next identity

`rmr_R2_range_reentry_economic_translation_v1`

It must use one fixed candidate only:

- next observed 1m close entry;
- mean-reversion direction toward the old range edge;
- original R2 re-entry edge / continuation boundary exits;
- fixed 1200-bar censor horizon;
- fixed 10bp round-trip cost;
- R2 geometry-baseline and range-integrity probabilities frozen by DEV for VALIDATION;
- select a trade only when range-integrity increases re-entry probability **and** candidate structural expected net return is positive.

No probability threshold, expected-return threshold, entry delay, stop/target, cost, scale or time-of-day search is allowed.

## Why structural expectancy is used immediately

R1 economic research already established on reusable VALIDATION that a probability improvement can fail to translate economically when reward/loss geometry is asymmetric. That is a general economic lesson, not BLACKBOX information.

R2 therefore starts directly from its causally known two-sided geometry rather than repeating a probability-edge-only economic v1.

## Gate philosophy

The R2 economic identity must pass detailed 2021–2025 VALIDATION before any additional BLACKBOX query. A VALIDATION failure closes this one economic identity; do not create v2/v3 automatically.

If it passes, one DEV+VALIDATION final refit may be frozen and submitted as the next low-bandwidth BLACKBOX candidate.

Production authority remains false.
