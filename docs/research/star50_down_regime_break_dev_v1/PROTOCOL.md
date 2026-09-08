# STAR50 downside regime-break candidate — Development V1

Development-only candidate test. Validation and BlackBox are not queried in this stage.

## Hypothesis generated from the frozen STAR50 HighVol mechanism map

STAR50 differs from CSI1000. The most coherent economically sized Development cell is a **downside regime break** rather than an upside acceleration:

- continuous `NormalVol -> HighVol` transition;
- recent 5m net return is negative;
- preceding non-overlapping 30m net return is positive, so the 5m direction is opposite the slow trend;
- recent 5m path efficiency `abs(net5)/sum(abs(1m returns)) >= 0.60`;
- recent 2m absolute movement share `< 0.60`, so the move is not a last-two-minute concentration spike;
- enter short at the next minute open;
- hold exactly 5 minutes, exit at the following open;
- same half-session, complete valid path;
- selected trades cannot overlap;
- exactly two execution legs.

No parameter menu is searched in this study. This is one mechanism-derived identity.

## Development role

- Subject: `000688.SH`.
- Horizon: 2021-01-01 through 2023-12-31 only.
- Primary friction: 1 bp per execution leg (2 bp round-trip abstraction).

## Development acceptance

The candidate is eligible to be frozen for reusable Validation only if all are true:

1. at least 60 pooled completed trades;
2. at least 15 completed trades in each of 2021, 2022 and 2023;
3. annual mean net return after 1 bp per leg is positive in all three years;
4. pooled mean net return after 1 bp per leg is positive;
5. pooled one-way break-even friction is greater than 1 bp.

Report annual and pooled trade count, gross bp/trade, net bp/trade at 0.5/1.0/1.5/2.0 bp per leg, hit rate, and one-way break-even.

If Development passes, write a separate frozen-candidate receipt before opening Validation. If it fails, do not open Validation.
