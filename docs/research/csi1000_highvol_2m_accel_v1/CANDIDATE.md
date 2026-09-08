# CSI1000 HighVol two-minute acceleration candidate V1

Frozen before opening the repository Validation pool.

## Data roles

- Development: 2021-01-01 through 2023-12-31.
- Validation: 2024-01-01 through 2026-08-21.
- BlackBox-V1: not queried.

## Candidate

Subject: `000852.SH` only.

State onset uses continuous volatility regime V1:

- recent 5 complete 1m close-to-close return RMS;
- divided by the preceding non-overlapping 30m RMS with 1 bp floor;
- HighVol if ratio >= 1.5;
- trigger only on `NormalVol -> HighVol` transition inside one half-session.

Past-path filter at trigger close:

- take the same five 1m returns defining the fast window;
- `tail2_share = (abs(r[-2]) + abs(r[-1])) / sum(abs(last5_returns))`;
- `tail1_share = abs(r[-1]) / sum(abs(last5_returns))`;
- require `tail2_share >= 0.80`;
- require `tail1_share < 0.60`.

Interpretation: the move is concentrated in the final two minutes, but not dominated by a single final-minute spike.

Direction and execution:

- direction = sign of the five-minute net return at the trigger close;
- enter at next minute open;
- hold exactly 10 minutes;
- exit at the following open;
- same half-session only;
- every minute in the execution path must be source-valid;
- no overlapping selected trades: a later trigger is ignored while an earlier selected trade is active.

## Development evidence that motivated freeze

After non-overlap enforcement, 77 eligible Development trades:

- 2021: 29 trades, mean gross `+2.9716 bp`, one-way break-even `1.4858 bp`;
- 2022: 25 trades, mean gross `+4.8665 bp`, one-way break-even `2.4333 bp`;
- 2023: 23 trades, mean gross `+3.1663 bp`, one-way break-even `1.5832 bp`;
- pooled: mean gross `+3.6450 bp`, one-way break-even `1.8225 bp`, net after 1 bp each side `+1.6450 bp/trade`.

Both long- and short-direction triggers were positive in pooled Development, although short-direction triggers contributed more gross edge. No direction-specific filter is added.

## Validation acceptance rule

Primary abstract friction: 1 bp per execution leg (2 bp round trip).

Candidate is considered validation-supported only if all are true:

1. pooled Validation net after 1 bp/leg is positive;
2. at least 2 of the 3 validation slices (2024, 2025, 2026-through-2026-08-21) have positive mean net per trade at 1 bp/leg;
3. pooled one-way break-even cost is > 1 bp;
4. pooled Validation has at least 30 completed trades;
5. both long and short directions are reported separately; neither is used post-hoc to redefine the candidate.

Secondary cost stresses: 0.5, 1.5 and 2 bp per execution leg.

If the rule fails, Validation detail may be inspected under the repository three-pool policy, but this exact candidate is not rescued by changing thresholds or hold duration in the same validation pass.
