# CSI1000 causal minute-close stop-loss Development study V1

Development-only study. Validation and BlackBox are not queried.

## Frozen parent candidate

Use exactly the validated CSI1000 long candidate:

- `000852.SH`;
- `NormalVol -> HighVol`;
- recent 5m net > 0;
- preceding non-overlapping 30m net > 0;
- `tail2_share >= 0.60`;
- `tail1_share < 0.60`;
- next-minute open entry;
- original maximum hold 3 minutes;
- same-half-session complete valid path;
- frozen non-overlap rule.

Development horizon: 2021-01-01 through 2023-12-31. The parent candidate must reproduce 104 trades.

## Causal stop family

Do not use intraminute low/high as an executable stop price.

For each completed parent trade, after the close of held minute 1 and (if still held) held minute 2, compute the signed long return from the frozen entry open to that just-completed minute close.

Fixed loss thresholds, in bp:

`2, 4, 6, 8, 12`

If cumulative close return is `<= -threshold`, set the target to flat and execute the exit only at the **next minute open**. If no stop fires, retain the parent exit at the open after 3 held minutes.

Each trade therefore still has exactly two execution legs. No re-entry. No take-profit. No trailing rule. No state-dependent threshold. No threshold search outside the fixed menu.

`no_stop` is the frozen parent baseline.

## Metrics

For every threshold and `no_stop`, report pooled and 2021/2022/2023:

- completed trades;
- stop count / stop rate;
- mean gross bp/trade;
- mean net bp/trade at 1 bp per leg;
- median gross;
- 10th percentile gross;
- worst gross trade;
- 10% expected shortfall (mean of observations at or below the empirical 10th percentile);
- hit rate;
- mean holding minutes.

## Development nomination

A stop can be nominated only if all are true:

1. all three annual mean net returns at 1 bp/leg are positive;
2. pooled mean net return is **not below** `no_stop`;
3. pooled 10th-percentile net return is strictly better than `no_stop`;
4. pooled worst-trade net return is strictly better than `no_stop`.

If multiple stops qualify, choose deterministically by:

1. highest worst-year mean net;
2. highest pooled mean net;
3. best pooled 10% expected shortfall;
4. lower threshold as final tie-break.

If none qualifies, nominate `NO_STOP` and do not open Validation for this stop family.

This protocol does not change the parent entry signal or the three-pool data governance policy.
