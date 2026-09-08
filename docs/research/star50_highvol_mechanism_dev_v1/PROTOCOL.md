# STAR50 continuous-HighVol mechanism map — Development V1

Development-only mechanism study. Validation and BlackBox are not queried. No trading candidate is nominated in this study.

## Data role

- Subject: `000688.SH`.
- Development horizon only: 2021-01-01 through 2023-12-31.
- Frequency: native 1-minute index bars under existing quality rules.
- Continuous state definition remains frozen: `HighVol` when recent 5m RMS / preceding non-overlapping 30m RMS >= 1.5, otherwise `NormalVol` when known.
- Event anchor: `NormalVol -> HighVol` transition within one half-session.

## Event features known at the transition close

Using five completed 1m returns ending at the HighVol transition minute:

- `direction`: sign of 5m net return (`up` / `down`);
- `tail1_share`: last 1m absolute return / 5m total absolute movement;
- `tail2_share`: last 2m absolute returns / 5m total absolute movement;
- `efficiency5`: absolute 5m net return / 5m total absolute movement;
- preceding non-overlapping 30m net return;
- `slow_aligned`: preceding 30m net has the same sign as the 5m event direction;
- `accel_high`: `tail2_share >= 0.60`;
- `efficient_high`: `efficiency5 >= 0.60`;
- `single_spike`: `tail1_share >= 0.60`;
- frozen continuous volatility ratio at the transition.

These are diagnostics, not optimized thresholds. The 0.60 cuts are inherited interpretability cuts already used elsewhere in the research and are not tuned in this study.

## Future outcomes

For each event, enter conceptually at the **next minute open** and calculate signed continuation return in the event direction to the open after:

`1, 2, 3, 5, 10` minutes.

Positive means continuation in the transition direction; negative means reversal. Complete same-half-session valid paths only. No costs are subtracted because this study diagnoses direction structure rather than selecting a strategy.

## Frozen summaries

Report pooled and yearly:

1. all HighVol onsets;
2. `direction`;
3. `direction x slow_aligned`;
4. `direction x accel_high`;
5. `direction x efficient_high`;
6. full `direction x slow_aligned x accel_high x efficient_high` cube.

For each group and horizon report count, mean signed return, median signed return, and continuation hit rate.

Also report 10,000 trading-day block-bootstrap 95% intervals for pooled 3m and 5m mean signed continuation in each cell of the full cube with at least 20 events.

## Interpretation rule

This study does **not** promote a trade. It only answers whether STAR50 HighVol onset has a stable directional mechanism comparable to CSI1000.

A future Development candidate is justified only if the mechanism map shows an interpretable cell with:

- at least 20 pooled Development events;
- the same sign of mean signed continuation in 2021, 2022 and 2023;
- and a coherent 3m/5m horizon shape rather than a single isolated horizon.

Any candidate definition must be frozen in a later protocol before Validation is opened.
