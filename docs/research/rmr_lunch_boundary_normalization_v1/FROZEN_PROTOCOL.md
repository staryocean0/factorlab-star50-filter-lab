# RMR lunch-boundary normalization V1 — FROZEN PROTOCOL

Status at freeze: results not read.

## Mechanism class

Test whether the midday market closure creates a repeatable **closure-boundary displacement followed by early-afternoon normalization**.

This is related to Overnight at the mechanism-family level (a market closure separates two continuous trading sessions), but is scientifically distinct because the closure is intraday, shorter, and occurs within one trading day.

## Data

- `000688.SH`, `000852.SH`;
- native 1-minute OHLC;
- Development only: 2021–2023;
- no Validation / BlackBox / PnL.

## Lunch displacement

For every complete trading day with 120 valid morning and 120 valid afternoon minutes:

- morning anchor = close of the final morning minute;
- afternoon reopen price = open of the first afternoon minute;
- `lunch_gap_bp = log(afternoon_first_open / morning_last_close) * 1e4`.

The gap is observable at afternoon reopen. This study is mechanism-only and does not claim that the reopen price is an executable fill.

## Pre-boundary scale

Use the final 30 one-minute morning close-to-close returns, all ending before the lunch closure.

- `sigma_pre = max(RMS(last30_morning_returns), 1 bp)`
- `Z = abs(lunch_gap_bp) / sigma_pre`

Fixed magnitude bands:

- `low`: Z <= 1;
- `mid`: 1 < Z <= 2;
- `high`: Z > 2.

The primary “material lunch displacement” set is **Z > 1** (mid + high). No threshold search is allowed.

## Outcome

Gap direction = sign of `lunch_gap_bp`.

Starting from the afternoon reopen price:

- `F5 = log(close of afternoon minute 5 / afternoon reopen open) * 1e4`
- `F15 = log(close of afternoon minute 15 / afternoon reopen open) * 1e4`
- `signed_F5 = gap_direction * F5`
- `signed_F15 = gap_direction * F15`

Negative = normalization/reversal against the lunch gap; positive = continuation.

Primary horizon = 5 minutes. 15 minutes is diagnostic only.

Recovery fraction at 5m:

`recovery_fraction_5 = -signed_F5 / abs(lunch_gap_bp)`.

## Shallow signal-source gate per index

For the material set `Z > 1`, all must hold:

1. n >= 100 pooled and >= 20 in each Development year;
2. median `signed_F5 < 0` in 2021, 2022 and 2023;
3. pooled `P(signed_F5 < 0) >= 0.55`;
4. UP-gap and DOWN-gap groups each have >=30 pooled observations and negative median `signed_F5`;
5. pooled median recovery fraction > 0;
6. pooled material-gap reversal probability exceeds low-Z reversal probability by >=5 percentage points.

The broad source is `broad_signal_source_supported` only if both indices pass.

If supported, the interpretation is not “trade every lunch gap”; it is evidence for a broader `market-closure boundary normalization` source family worth specialist research.

## Forbidden rescue

- changing Z=1 primary boundary or the Z bands after results;
- clock/day/month filters;
- HighVol, activity, parent-state or direction filters;
- changing the 5-minute primary horizon;
- PnL/Sharpe/costs/positions;
- Validation/BlackBox.

`production_authority=false`.
