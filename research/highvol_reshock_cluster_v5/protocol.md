# HighVol re-shock cluster v5 — frozen Development protocol

Purpose: test whether the first recurrent shock inside an active `UNSAFE/RECOVERING` episode marks a distinct clustered-risk process. Risk-state research only; no PnL or trading rules.

## Inheritance and data

Reuse the v3 state engine and de-overlapped episode definition unchanged. Development-only: 2020 warm-up, 2021–2023 measured episodes, STAR50 and CSI1000 common-day support. Physically exclude 2024+ and BlackBox.

## Frozen anchor design

For every shock-triggered episode identify:

1. `INITIAL`: the episode-start shock;
2. `FIRST_RECURRENT`: the first later `shock=True` before the episode reaches `NORMAL`, if one exists.

Ignore second/later recurrent shocks as anchors so one highly clustered episode cannot contribute arbitrarily many recurrent-anchor observations.

At each anchor report:

- episode age in bars at anchor;
- time to first subsequent Normal, if observed;
- `P(Normal within next 15m / 30m / 60m)` with proper right-censoring;
- `P(another shock before Normal within next 15m / 30m)`; the anchor bar itself is not counted.

Summaries are pooled and by year for each symbol and anchor type.

## Fixed diagnostics

Compare `FIRST_RECURRENT` minus `INITIAL` for:

- Normal-within-15/30/60 probabilities;
- next-shock-within-15/30 probabilities;
- median observed bars to Normal.

Also report the distribution of bars from initial shock to first recurrence.

This is a mechanism diagnostic, not an optimization. No threshold is promoted. If first recurrent shocks consistently show slower recovery and/or elevated further-shock probability across both indices and years, a later Development study may test a distinct `CLUSTERED` state. Otherwise recurrence remains an event annotation rather than a state-machine branch.

`production_authority=false`; `validation_queried=false`; `blackbox_queried=false`.
