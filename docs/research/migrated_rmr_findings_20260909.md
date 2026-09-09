# Migrated RMR findings review — 2026-09-09

## Provenance and authority

This review extracts reusable scientific findings from the reversal / mean-reversion work that was mistakenly executed inside `factorlab-overnight-open-lab` after its repository identity was changed on 2026-09-08.

Raw evidence is preserved under `docs/archive/misrouted_rmr_from_overnight_20260909/` at frozen source commit `64bcf6779bb7fead52fbebea8771679f89d55fd1`.

This migration does **not** inherit the source repository's program-wide authority, BLACKBOX ledger, or production decisions. `production_authority=false` remains unchanged here.

## Findings worth retaining

1. **Parent normal-state integrity is the useful high-level abstraction.**
   - R1: intact trend parent + lower-scale counter-move is a pullback-recovery mechanism.
   - R2: intact range parent + boundary break attempt is a range re-entry mechanism.
   - These are complementary parent-state cases, not interchangeable scalar signals.

2. **Do not equate restoration probability with realized-return quality.**
   The completed mechanism-to-execution diagnostic found restoration probability was not monotonic with realized net return. Probability-threshold rescue was therefore unsupported.

3. **Payoff geometry can dominate a statistically valid mechanism.**
   The diagnostic found negative structural expected net across the tested R1/R2 execution cells before overshoot effects; next-bar delay was secondary. This is directly relevant to current research: state/mechanism evidence should precede economic translation, and translation needs its own payoff-object contract.

4. **R1_B showed delayed rather than immediate realization.**
   Its fixed markout term structure strengthened at longer predeclared horizons, while the preregistered temporal impulse candidate later failed its DEV median-net gate. The useful lesson is not a chosen horizon; it is that trend-parent restoration may be path-distributed and should not be reduced automatically to next-bar execution.

5. **R2 directional execution deteriorated with horizon under the tested mapping.**
   A valid range re-entry mechanism did not imply profitable directional persistence from immediate index exposure.

6. **Independent payoff/instrument theory is required before new economic testing.**
   The results-blind review explicitly prohibited horizon, entry-delay, stop/target, probability, cost, and scale searches as rescue paths. Instrument mapping requires its own source, spread, basis, carry, liquidity, convexity/premium, and execution contract.

## Consequence for the current repository

Treat these as reusable research constraints and negative evidence, not as a ready-made strategy. They support the current separation between state/mechanism measurement and later trading-module design, and they argue against tuning economic rules before the payoff object is causally defined.
