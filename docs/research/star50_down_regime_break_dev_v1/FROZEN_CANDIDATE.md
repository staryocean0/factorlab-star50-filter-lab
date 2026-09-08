# Frozen candidate — STAR50 downside regime break V1

Frozen before re-opening the reusable Validation pool.

## Candidate identity

- Subject: `000688.SH`.
- Continuous `NormalVol -> HighVol` transition.
- Recent 5m net return is negative.
- Preceding non-overlapping 30m net return is positive.
- 5m path efficiency `>= 0.60`.
- Last-2m absolute movement share `< 0.60`.
- Enter short at the next minute open.
- Hold exactly 5 minutes and exit at the following open.
- Same half-session, complete valid execution path only.
- Selected trades cannot overlap.
- Exactly two execution legs per completed trade.

## Development receipt — 2021-2023 only

Primary abstract friction: 1 bp per leg.

- 2021: 32 trades; mean gross `+3.4469 bp`; mean net1 `+1.4469 bp`; one-way break-even `1.7234 bp`.
- 2022: 19 trades; mean gross `+4.0482 bp`; mean net1 `+2.0482 bp`; one-way break-even `2.0241 bp`.
- 2023: 26 trades; mean gross `+2.8807 bp`; mean net1 `+0.8807 bp`; one-way break-even `1.4404 bp`.
- pooled: 77 trades; mean gross `+3.4041 bp`; mean net1 `+1.4041 bp`; one-way break-even `1.7020 bp`; hit rate `49.35%`.

All registered Development acceptance conditions passed.

## Reusable Validation acceptance

Validation period: 2024-01-01 through 2026-08-21.

The frozen candidate is Validation-supported only if all are true:

1. at least 30 completed Validation trades pooled;
2. pooled mean net after 1 bp per leg is positive;
3. at least 2 of the 3 Validation slices (2024, 2025, 2026-through-2026-08-21) have positive mean net after 1 bp per leg;
4. pooled one-way break-even cost is > 1 bp;
5. no candidate parameter is changed during this Validation pass.

Secondary cost stresses: 0.5, 1.5 and 2.0 bp per leg.

This is reusable Validation evidence under the repository three-pool policy. It is not BlackBox evidence. BlackBox-V1 is not queried.
