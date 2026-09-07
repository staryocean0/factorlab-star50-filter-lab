# Trigger-severity diagnostic

Date: 2026-09-07. Exploratory diagnostic on consumed 2024-2025 history; no new model or threshold is promoted.

## Question

At the close of the first-shock minute, can static information about that shock reliably tell us how severe the following 15-minute risk episode will be?

Candidate information already available at the shock close included:

- standardized shock amplitude `abs(event_return)/sigma_pre`;
- pre-shock background sigma;
- pre-five-minute path range/net/efficiency and concentration;
- event-minute 3-second path concentration/efficiency and largest observed increment;
- event context taxonomy (`quiet_first`, `prior_directional`, `prior_roundtrip_or_active`);
- clock position.

Outcome summaries use the already-defined following-15-minute realized risk ratio and Unsafe-window burden. Events later than minute105 are excluded from the full-15-minute comparison.

## Main finding

No static trigger descriptor is stable enough to justify an event-close severity tier.

The standardized shock amplitude has a modest pooled association with following risk, but it is not stable across index/year cells:

- STAR50 2024: essentially no monotone association with mean next-15m risk;
- STAR50 2025: positive association;
- CSI1000 2024: positive association;
- CSI1000 2025: only five complete events and no usable stable inference.

In the pooled 73 events with complete 15-minute futures, shock amplitude has Spearman correlation around +0.27 with mean post-shock risk and around +0.30 with excess-risk area. This is too heterogeneous to promote a hard severity bucket.

The event-minute path concentration and efficiency measures are weaker: their pooled monotone associations with following risk are close to zero. The pre-five-minute path context also has no simple universal ordering:

- `prior_directional` has the highest average 15-minute burden in this sample;
- `quiet_first` is intermediate;
- `prior_roundtrip_or_active` is lower;

but group sizes are small and this ordering is descriptive, not stable enough for a state rule.

Clock position shows some association with realized post-shock risk, but this can mix intraday volatility seasonality and remaining-session support. It should not be turned into a severity grade without a separate clock-normalized protocol.

## 2026 consistency note

The already-opened 2026 validation has only 14 first-shock events. Standardized shock amplitude is positively associated with immediate and short-lag post-shock risk in that tiny sample, but the uncertainty is large. Because 2026 outcomes have already been inspected, this is only a consistency observation and not an independent validation of a new severity rule.

## Decision

Do **not** add `mild / severe first shock` or similar trigger-level state labels.

The stronger and more stable signal is the **evolving post-shock state itself**:

`current trailing-5m RMS / fixed pre-shock sigma_pre`

This means the state machine should adapt from realized post-shock activity rather than attempting to decide the entire episode severity from the first minute.

Future independent data may revisit trigger severity only under a new frozen protocol. Until then, event amplitude/path descriptors remain diagnostic metadata, not state transitions.
