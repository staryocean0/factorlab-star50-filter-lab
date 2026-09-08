# STAR50 slow-trend-quality Development study V4

Role: **Development only (2021-2023)**. Validation and BlackBox are not queried.

## Hypothesis

The failed V2/V3 work suggests that a fast efficient downside move is not sufficient to define a durable regime break. The next question is whether the *slow rise being broken* was itself a coherent trend or merely noisy drift.

At STAR50 `NormalVol -> HighVol` onsets require only:

- prior non-overlapping 30-minute net return > 0;
- recent 5-minute net return < 0;
- recent 5-minute path efficiency >= 0.60.

For the prior 30 completed one-minute returns define:

- `slow30_efficiency = slow30_net / sum(abs(slow30_returns))`;
- `slow30_up_share = fraction(slow30_returns > 0)`.

These are causal at onset.

Natural coarse bands are frozen before results:

- efficiency: `<0.20`, `0.20-0.40`, `0.40-0.60`, `>=0.60`;
- up-share: `<0.55`, `0.55-0.60`, `0.60-0.65`, `>=0.65`.

Nested efficiency thresholds inspected for candidate nomination: `>=0.20`, `>=0.40`, `>=0.60` only. Up-share is a mechanism robustness proxy and cannot directly nominate a candidate in this round.

## Outcome and gates

Short at next-minute open, hold 3 minutes, same half-session, complete valid path, non-overlapping trades. Primary economics use 1bp/leg.

A threshold can nominate V4 only if Development 2021/2022/2023 satisfies all:

- pooled trades >= 60;
- every year trades >= 15;
- every year mean net @1bp/leg > 0;
- pooled mean net @1bp/leg > 0;
- pooled one-way break-even > 1bp.

No gate may be relaxed after results.

## Governance

The workflow must physically contain only STAR50 2020 warm-up and 2021-2023 Development files. 2024+ files must be absent. BlackBox remains untouched.
