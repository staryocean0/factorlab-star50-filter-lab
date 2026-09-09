# R1_B temporal impulse completion v1 — DEV adjudication

Date: 2026-09-08  
Identity: `rmr_R1B_temporal_impulse_completion_v1`  
Candidate: `R1B_S2_PARENT_IMPULSE_CONFIRM_EXIT`  
Decision: **DEV_CLOSE**  
VALIDATION opened: `false`  
BLACKBOX opened: `false`  
Production authority: `false`

## Execution authority

The preregistered DEV-only identity was executed by GitHub Actions run `34229441615` at commit `a0801a7905f96b8bf7f075fe60a4a4d20052ef53`.

- job `102071584287`: `completed / success`;
- 7/7 frozen-boundary tests passed;
- artifact ID: `10057144842`;
- artifact ZIP SHA256: `523d566b4ec2e8565fb4a6a7b4cacaa5ffe6c1fd8330886ed197c9a85415fa7c`;
- maximum read date: `2020-12-31`;
- certified R1_B event population matched the retained mechanism engine exactly;
- no probability filter, refit, threshold/horizon search, VALIDATION read or BLACKBOX access occurred.

## Frozen temporal theory tested

A certified R1_B event is an S2 pullback opposite an intact S3 parent direction. At confirmation of that counter-parent S2 wave, the existing directional-change engine has already switched into a new S2 wave in the parent direction.

The candidate therefore held the unchanged next-bar entry until the first subsequent parent-aligned S2 wave was **causally confirmed**, unless the original S3 structural failure boundary was crossed first. The S2 wave extreme was never used because it is not knowable at that time. The inherited 1200-bar horizon was only a safety censor.

This was a genuinely different temporal object from the closed original-target first-passage execution and introduced no new numeric parameter.

## DEV evidence

There were `726` certified R1_B events and `682` next-bar-tradeable events (`93.94%`).

### Candidate

- mean gross: `+20.59bp`;
- mean net after fixed 10bp: `+10.59bp`;
- median net: **`-32.11bp`**;
- win rate: **`37.10%`**;
- mean / median / p90 hold: `110.4 / 55 / 273.8` bars;
- exit classes: `637` parent-aligned S2 impulse confirmations, `40` parent failures, `5` censors.

### Closed structural-first-passage baseline on the same tradeable events

- mean gross: `+8.72bp`;
- mean net: `-1.28bp`;
- median net: `+30.91bp`;
- win rate: `67.01%`.

The candidate improved pooled mean net by `+11.87bp`, but did so by changing the payoff distribution from frequent smaller wins / rare large losses toward infrequent large right-tail winners and a negative typical event.

## Annual DEV evidence

Candidate mean net was positive in 5 of 6 years:

| Year | Candidate net | Baseline net | Candidate - baseline |
|---|---:|---:|---:|
| 2015 | +8.41bp | -9.01bp | +17.42bp |
| 2016 | -3.99bp | +0.59bp | -4.58bp |
| 2017 | +24.94bp | +31.61bp | -6.67bp |
| 2018 | +5.57bp | +1.97bp | +3.61bp |
| 2019 | +25.62bp | +7.31bp | +18.31bp |
| 2020 | +20.19bp | -9.98bp | +30.16bp |

This is meaningful evidence that the delayed R1_B markout motivation was not spurious. However, it is not enough to pass the preregistered identity.

## Predeclared DEV gate

| Gate | Result |
|---|---|
| pooled candidate mean net > 0 | PASS |
| pooled candidate mean net > baseline | PASS |
| pooled candidate median net > 0 | **FAIL** |
| positive candidate mean-net years >= 4/6 | PASS |

Overall decision: **FAIL / DEV_CLOSE**.

The median gate was frozen before execution. It may not be removed after observing that the mean is positive.

## Mechanistic interpretation

The result clarifies why the prior fixed-horizon markouts could look attractive without yielding a robust causal execution identity.

A parent-aligned S2 wave is only confirmed after price has moved far enough in the parent direction to form an extreme and then retraced by the frozen S2 directional-change threshold. Therefore `impulse completion confirmation` is deliberately late relative to the best price reached during the impulse. That causal giveback is not a bug; it is the cost of knowing that the impulse has completed.

The positive mean plus negative median / low win rate shows that the candidate captures a right-tail subset of large trend restorations, but a typical event loses by the time completion is causally confirmed. The candidate is therefore not a broad temporal translation of certified R1_B restoration probability.

This also means the DEV evidence must **not** be rescued by:

- exiting at the unobservable S2 extreme;
- choosing a partial-recovery threshold;
- choosing 30/60/120/240 bars;
- adding a probability filter to isolate the right tail;
- changing the entry delay, cost, S2/S3 scales or failure boundary;
- selecting favorable years/regimes.

Each would be a post-result redesign of the closed identity.

## Program consequence

`rmr_R1B_temporal_impulse_completion_v1` closes on DEV. Its VALIDATION is permanently unopened under this identity.

The scientific conclusion is narrower than “R1_B has no economic information”: DEV shows a positive right-tail temporal payoff component. But the single preregistered causal completion mapping does not convert it into a sufficiently broad event-level execution distribution.

No second temporal candidate is automatically authorized by this result. A future economic identity would require a separate program review with an independently stated payoff/instrument theory, not a repair of this candidate.

BLACKBOX query count remains exactly 3. Query #4 does not exist and is not authorized.
