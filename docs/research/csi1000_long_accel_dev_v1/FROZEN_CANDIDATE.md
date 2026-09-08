# Frozen candidate — CSI1000 long slow-aligned HighVol acceleration V1

Frozen before re-opening the reusable Validation pool.

## Candidate identity

- Subject: `000852.SH`.
- Trigger: continuous `NormalVol -> HighVol`, where 5m RMS / preceding non-overlapping 30m RMS >= 1.5.
- Current five-minute net return must be positive.
- Preceding 30-minute net return, ending before the current 5m trigger window, must be positive.
- `tail2_share >= 0.60`.
- `tail1_share < 0.60`.
- Enter at the next minute open.
- Hold exactly 3 minutes and exit at the following open.
- Same half-session and complete valid execution path only.
- Selected trades cannot overlap.
- Exactly two execution legs per completed trade.

## Development selection receipt

Candidate was selected only from 2021-2023 under the previously registered 54-identity Development menu and deterministic ranking rule.

Primary abstract friction: 1 bp per leg.

- 2021: 37 trades; mean gross `+2.7611 bp`; mean net1 `+0.7611 bp`; one-way break-even `1.3806 bp`.
- 2022: 31 trades; mean gross `+3.1565 bp`; mean net1 `+1.1565 bp`; one-way break-even `1.5783 bp`.
- 2023: 36 trades; mean gross `+2.3531 bp`; mean net1 `+0.3531 bp`; one-way break-even `1.1766 bp`.
- pooled: 104 trades; mean gross `+2.7377 bp`; mean net1 `+0.7377 bp`; one-way break-even `1.3689 bp`; hit rate `63.46%`.

## Reusable Validation acceptance

Validation period: 2024-01-01 through 2026-08-21.

The candidate is Validation-supported only if all are true:

1. at least 30 completed Validation trades pooled;
2. pooled mean net after 1 bp per leg is positive;
3. at least 2 of the 3 Validation slices (2024, 2025, 2026-through-2026-08-21) have positive mean net after 1 bp per leg;
4. pooled one-way break-even cost is > 1 bp;
5. no candidate parameter is changed during this Validation pass.

Secondary cost stresses: 0.5, 1.5 and 2.0 bp per leg.

This is reusable Validation/tuning evidence, not fresh OOS, because the long/slow-alignment hypothesis was generated after inspecting an earlier Validation failure. BlackBox-V1 is not queried.
