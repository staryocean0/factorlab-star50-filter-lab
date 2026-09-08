# STAR50 turnover-pressure V12 — Development only

## Hypothesis

Raw turnover intensity (V11) was not a stable cost-covering router.  Test a different participation question without adding a threshold menu: whether the latest 5-minute STAR50 price direction is supported by the direction of monetary turnover.

At each causal `NormalVol -> HighVol` onset on `000688.SH`:

- compute the latest five 1-minute close-to-close log returns `r_t`;
- compute ordinary `net5 = sum(r_t)`;
- compute turnover-weighted pressure `P5 = sum(r_t * amount_t) / sum(amount_t)`;
- `TurnoverSupported` when `sign(P5) == sign(net5)`;
- `TurnoverOpposed` when the signs differ.

There is no fitted magnitude threshold.

Execution diagnostic is fixed: next-minute open entry, fixed 3-minute hold, same half-session, full valid path, non-overlapping accepted events. Report continuation and reversal relative to `sign(net5)` for 2021, 2022, 2023 and pooled.

A view is only tagged `mechanism_promising` if every Development year has at least 15 events and either continuation or reversal is positive after 1 bp per leg in all three years. This does not nominate a candidate.

Governance: Development 2021–2023 only; 2020 warm-up allowed; no Validation; no BlackBox; `candidate_nominated=false`.
