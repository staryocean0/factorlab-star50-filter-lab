# HighVol shock-expiry mechanism V12 — Development protocol

Purpose: explain the V11 60-minute state-rank crossover without changing the validated risk-state machine or tuning horizons. Specifically test whether the crossover is concentrated while the most recent shock return is still mechanically present in the fixed 12-bar realized-volatility window.

This is mechanism research only. It creates no PnL, payoff, route, position, or trading rule.

## Inherited authority

Unchanged:

- symbols `000688.SH`, `000852.SH`;
- Development 2021-2023, 2020 warm-up;
- `rv12 = std(last 12 valid 5m returns, ddof=0)`;
- `bg48 = std(previous 48 valid 5m returns, ddof=0)`;
- shock threshold `abs(ret_5m)/bg48 >= 3.0`;
- `UNSAFE` / `RECOVERING` / `NORMAL` thresholds `1.50` and `1.10`;
- recurrent shock resets the recovery clock.

V11 run `34450053409` found that `RECOVERING > UNSAFE` for cumulative normalization at 15m and 30m, but the ordering reversed in all four age buckets at 60m. V11 was therefore not eligible for Validation.

## Structural variable — no fitted threshold

Let `a` be the number of completed 5m bars since the most recent shock.

Because `rv12` contains the last 12 valid returns:

- `shock_in_rv12 = true` iff `1 <= a <= 11`;
- `shock_in_rv12 = false` iff `a >= 12`;
- for in-window rows, `bars_until_shock_exits = 12 - a`.

This cutoff is implied exactly by the inherited 12-bar window and is not a searched parameter.

## Sample and outcomes

Use active-risk observations (`UNSAFE` or `RECOVERING`) before the first return to `NORMAL`. Require 13 complete future 5m bars in the same trading day so that even an age-1 row can be observed through the first 15 trading minutes after its shock leaves `rv12`.

For every row report:

- whether the latest shock is still inside `rv12`;
- `P(Normal within next 60m)` using the next 12 bars;
- if shock is in-window, the deterministic future step when it first leaves `rv12`;
- whether Normal occurs before that expiry;
- conditional on remaining non-Normal through expiry, whether the first Normal occurs during the first 3 bars (15 trading minutes) beginning at the first post-shock-window bar.

Use Beta(1,1) smoothed probabilities for group comparisons.

## Fixed mechanism adjudication

The shock-expiry explanation is supported only if all are true:

1. pooled `UNSAFE` and `RECOVERING` each have at least 100 rows in both `shock_in_rv12=true` and `false` strata;
2. while the shock remains in `rv12`, the pooled 60m gap `P60(RECOVERING)-P60(UNSAFE)` is negative;
3. after the shock has exited `rv12`, the pooled 60m gap is positive;
4. the same sign pattern in items 2-3 holds in at least 2 of 3 Development years for each stratum;
5. among in-window rows that survive non-Normal to the deterministic expiry, pooled post-expiry-15m normalization probability is higher for current `UNSAFE` than current `RECOVERING`;
6. item 5 holds in at least 2 of 3 Development years;
7. inherited state thresholds and `rv12` length are unchanged;
8. no Validation, BlackBox, PnL, payoff or trading variable is used.

This is a mechanism test, not a candidate selector. Even if supported, no Validation is opened automatically. The result may only motivate a separately preregistered risk-state representation in Development.

`production_authority=false`.
