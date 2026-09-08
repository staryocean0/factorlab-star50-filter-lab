# Continuous HighVol direction V1 — frozen protocol

Date: 2026-09-08
Status: development/validation research only; no BlackBox-V1 query; no production authority.

Governance follows repository data-use policy V2 on `main`: Development=2021-2023, Validation=2024-2026-08-21, BlackBox not touched.

## Question

The continuous HighVol regime V1 found no viable candidate in the existing Butterworth/hysteresis trend family. Determine whether short-horizon price motion in the same causal HighVol state is better captured by **momentum** or **reversal**, and whether any simple actionable rule survives a 1bp one-way abstract cost stress.

## State

Use exactly the continuous regime frozen in `docs/research/continuous_vol_regime_v1/PROTOCOL.md`:

- `fast5 = RMS` of the most recent 5 complete 1m close-to-close returns;
- `background30 = RMS` of the preceding non-overlapping 30 complete 1m returns;
- `vol_ratio = fast5 / max(background30, 1bp)`;
- `HighVol` iff `vol_ratio >= 1.5`;
- `NormalVol` iff known and `<1.5`;
- otherwise Unknown;
- never cross lunch, overnight, repaired/invalid rows, or gaps.

No state threshold search.

## Strategy menu

At minute close `t`, after observing the state and all closes through `t`:

- lookbacks `L = 1, 2, 3, 5, 10` minutes;
- `past_move = log(close_t / close_{t-L}) * 1e4`, requiring every source minute in the lookback to be valid;
- momentum target = `sign(past_move)`;
- reversal target = `-sign(past_move)`;
- zero/unknown past move => flat target;
- HighVol gate: target is allowed only when state at decision minute `t` is HighVol;
- NormalVol gate is reported as a state-specific diagnostic for the identical rule;
- Ungated is also reported.

Execution delays:

- `1m`: decision at close `t` becomes position at the next minute open;
- `2m`: decision becomes position two minutes later, matching the conservative latency used in prior strategy work.

Position is updated every minute and held until the delayed desired position changes. Every half-session starts and ends flat. No lunch/overnight return is booked.

Menu size per symbol: `2 directions × 5 lookbacks × 2 delays = 20`.

## Costs

Report zero-cost gross and abstract one-way cost stresses `0.5, 1, 2 bp` per unit turnover. This is an index-research economics test, not a claim about ETF/futures realized costs.

## Development-only nomination

For each symbol separately, use only 2021-2023 HighVol results.

A candidate is eligible iff:

1. HighVol exposure is nonzero in all three development years;
2. `net1bp_per_exposure_min > 0` in at least 2 of 3 development years;
3. pooled development HighVol break-even one-way cost is `> 1 bp`.

Among eligible candidates, nominate the one with highest pooled development `net1bp_per_exposure_min`.

Tie-breakers in order:

1. shorter lookback;
2. shorter execution delay;
3. reversal before momentum (deterministic only; no scientific prior implied).

If none is eligible, nominate `NONE`.

## Validation

Apply the development nomination unchanged to Validation 2024, 2025 and 2026-through-08-21.

Primary diagnostics:

1. pooled validation HighVol net after 1bp is positive;
2. at least 2 validation slices have positive HighVol net1/min;
3. pooled validation break-even one-way cost >1bp;
4. the same rule performs better in HighVol than NormalVol after 1bp.

After the frozen candidate decision is recorded, the reusable Validation pool may be inspected in detail. Any newly discovered variant must return to Development under a new protocol.

## Guardrails

- BlackBox-V1 not queried.
- No first-shock prediction claim.
- No validation-driven change to this V1 candidate.
- No production/live promotion.
