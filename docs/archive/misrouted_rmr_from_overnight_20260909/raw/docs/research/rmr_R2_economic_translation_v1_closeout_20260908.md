# R2 economic translation v1 closeout — 2026-09-08

Research identity: `rmr_R2_range_reentry_economic_translation_v1`

Final decision:

`R2_ECONOMIC_V1_VALIDATION_FAIL_BLACKBOX_NOT_QUERIED_CLOSE_IDENTITY`

## Frozen candidate

The only candidate used:

`R2_STRUCTURAL_EXPECTANCY_POSITIVE_NEXT_BAR_10BP`

Rules were frozen before execution:

- event = certified R2 range-boundary event;
- direction = toward the old range edge, opposite breakout side;
- entry = next observed 1m close after event confirmation;
- re-entry target and continuation loss boundary = original R2 causal boundaries;
- horizon = 1200 observed bars;
- round-trip cost = 10bp;
- probability model = R2 geometry baseline vs range-integrity augmented model;
- select only when `p_candidate > p_baseline` **and** candidate structural expected net return > 0;
- no probability/expectancy threshold, entry, exit, cost, scale, time-of-day or portfolio-weight search.

## Detailed VALIDATION result

### PAIR_A — S1 outside S2

All tradeable-event baseline:

- n = 1,738
- mean net return = `-0.0012680713`
- median net return = `-0.0021245444`
- win rate = `0.2756`

Frozen candidate:

- selected n = 157
- mean net return = `-0.0013019049`
- median net return = `-0.0017350205`
- win rate = `0.0892`
- mean holding = `16.08` bars

Annual candidate mean net return:

- 2021: `-0.0012361`
- 2022: `-0.0017877`
- 2023: `+0.0000211`
- 2024: `-0.0018794`
- 2025: `-0.0011956`

Failed gates:

- pooled minimum selected trades (157 < 200);
- mean net return > 0;
- mean net return > all-event baseline;
- positive annual mean return in >=4/5 years.

### PAIR_B — S2 outside S3

All tradeable-event baseline:

- n = 819
- mean net return = `-0.0012519061`
- median net return = `-0.0019968243`
- win rate = `0.2051`

Frozen candidate:

- selected n = 197
- mean net return = `-0.0012621452`
- median net return = `-0.0018395922`
- win rate = `0.0558`
- mean holding = `28.67` bars

Annual candidate mean net return:

- 2021: `-0.0014548`
- 2022: `-0.0016532`
- 2023: `-0.0016317`
- 2024: `-0.0009373`
- 2025: `-0.0007741`

Failed gates:

- mean net return > 0;
- mean net return > all-event baseline;
- positive annual mean return in >=4/5 years.

Sample gates were otherwise adequate for PAIR_B.

## BLACKBOX boundary

The candidate failed reusable detailed VALIDATION. Therefore:

- no final economic refit was performed;
- reusable BLACKBOX query #4 did **not** occur;
- BLACKBOX query ledger remains at three completed queries;
- no 2026 economic result or detail exists for this identity.

## Scientific interpretation

R2's **probability mechanism remains certified**. The failure is specific to this economic translation.

The result says that under next-minute index-reference entry, original R2 structural boundaries and a fixed 10bp round-trip cost, a positive range-integrity probability increment plus positive structural binary expectancy does not translate into stable realized net return.

Together with the closed R1 economic family, the current evidence supports a separation:

> Certified state-transition probability information is not yet a certified trading implementation under the tested index-level execution geometry.

Do not create automatic R2 economic v2/v3 by changing thresholds, entry delays, stops, costs, scales or time filters against VALIDATION. A new economic identity requires independently motivated execution/instrument theory.

Production authority remains false.
