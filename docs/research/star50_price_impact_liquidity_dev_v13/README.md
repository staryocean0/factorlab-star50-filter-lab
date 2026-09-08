# STAR50 price-impact/liquidity V13 — Development only

At each causal STAR50 `NormalVol -> HighVol` onset, compare recent price impact per yuan of turnover with the preceding non-overlapping background.

`impact_recent = sum(abs(r_t), last 5m) / sum(amount_t, last 5m)`

`impact_prior = sum(abs(r_t), prior non-overlap 30m) / sum(amount_t, prior non-overlap 30m)`

`impact_ratio = impact_recent / impact_prior`

Fixed states, with no threshold menu:
- `ImpactAmplified`: ratio >= 1.0
- `ImpactDamped`: ratio < 1.0

Economic interpretation: amplified impact means the volatility burst is large relative to monetary participation (thin-liquidity style); damped impact means turnover rises enough to absorb the price movement.

Direction reference is latest 5-minute net return sign. Execution diagnostic is next-minute open, fixed 3-minute hold, same half-session, complete valid path, non-overlapping events. Report continuation and reversal for 2021/2022/2023 and pooled at 1 bp per leg.

A mechanism is tagged promising only if every Development year has >=15 events and either continuation or reversal is net positive in all three years. No candidate is automatically nominated.

Development only; 2020 warm-up allowed; Validation and BlackBox are not queried.
