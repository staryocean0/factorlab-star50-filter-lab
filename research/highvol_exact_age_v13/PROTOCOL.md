# HighVol exact-age standardization V13 — Development protocol

Purpose: determine whether V11's 60-minute `RECOVERING < UNSAFE` crossover is only a composition/Simpson effect caused by different exact recent-shock-age distributions inside the inherited broad age buckets.

This is bottom-layer risk-process diagnosis only. No trading, PnL, payoff, routing, or production authority is created.

## Inherited definitions

All risk-state definitions remain unchanged from V6/V11/V12:

- 5m returns;
- `rv12` / previous-48-bar background volatility;
- shock threshold `3.0`;
- UNSAFE threshold `1.50`;
- NORMAL threshold `1.10`;
- recurrent shock resets the recovery clock.

Use Development 2021-2023 only, with 2020 warm-up. Validation and BlackBox are excluded.

## Exact-age analysis

Restrict to active-risk rows whose most recent shock is still inside `rv12`, i.e. exact recent-shock age `a = 1..11` completed 5m bars. Require the same 13-future-bar support used in V12.

For every exact age `a=1..11` and state `{UNSAFE, RECOVERING}`, estimate Beta(1,1)-smoothed `P(Normal within next 60m)`.

No exact-age binning, threshold search, horizon search, or state change is allowed.

## Direct standardization

Within each evaluation group (pooled Development and each of 2021/2022/2023):

1. retain exact ages at which both states are observed;
2. for each retained age, compute the combined count across the two states;
3. normalize those combined counts into one common exact-age weight distribution;
4. apply the same weights to the age-specific UNSAFE and RECOVERING probabilities;
5. report standardized `P60_RECOVERING - P60_UNSAFE`.

Also report the raw unstandardized in-window gap and all 11 exact-age state probabilities/counts.

## Fixed adjudication

The broad-bucket composition explanation is supported only if all are true:

1. all exact ages 1..11 contain both states in pooled Development;
2. the raw pooled in-window `P60_RECOVERING - P60_UNSAFE` gap is negative, reproducing V12;
3. after exact-age standardization, the pooled gap is non-negative;
4. the standardized gap is non-negative in at least 2 of 3 Development years;
5. inherited state thresholds, rv12 length and 60m outcome remain unchanged;
6. no Validation, BlackBox, PnL, payoff or trading variable is used.

If items 3-4 fail, exact-age composition is rejected as the explanation and the next mechanism must examine path composition inside the 12-bar volatility window rather than retuning age buckets.

`production_authority=false`.
