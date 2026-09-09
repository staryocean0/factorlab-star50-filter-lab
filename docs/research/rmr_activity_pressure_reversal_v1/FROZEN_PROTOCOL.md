# RMR activity-pressure reversal V1 — FROZEN PROTOCOL

Status at freeze: results not read.

## Mechanism class

Test whether a severe short-horizon price displacement accompanied by unusually high transaction activity behaves like temporary price pressure and subsequently reverses more than an equally defined displacement with normal activity.

This is distinct from the prior STAR50 HighVol-activity V11 study: no HighVol onset is required, both indices are studied, and the objective is price-path reversal probability rather than a 3-minute economic module.

## Data

- `000688.SH` and `000852.SH`;
- native 1-minute index data;
- Development only: 2021–2023;
- same half-session only;
- no Validation / BlackBox / PnL.

## Causal displacement definition

At minute `t`:

- background window = preceding non-overlapping 30 one-minute returns;
- recent window = latest 5 one-minute returns ending at `t`;
- background RMS floor = 1 bp;
- `R5 = sum(recent 5 returns)`;
- `severity = abs(R5) / (background_RMS * sqrt(5))`.

A severe-displacement **onset** occurs when:

- current severity >= 2.0;
- previous eligible decision severity < 2.0 in the same half-session.

No threshold search is allowed.

## Activity definition

Using the native `amount` field:

`activity_ratio = mean(amount latest 5 minutes) / mean(amount preceding non-overlapping 30 minutes)`.

Fixed states:

- `ElevatedActivity`: ratio >= 1.5;
- `NormalActivity`: ratio < 1.5.

## Outcomes

Direction is sign of `R5`.

Primary horizon: next 5 minutes.

`F5 = sum(next 5 one-minute returns)`

`signed_F5 = sign(R5) * F5`

Negative means reversal; positive means continuation.

Secondary horizon: next 15 minutes, identically defined as `signed_F15`. It is diagnostic only and cannot rescue a failed 5-minute result.

Fixed severity views:

- `moderate`: 2 <= severity < 3;
- `extreme`: severity >= 3.

## Shallow signal-source gate

For each index separately, all must hold:

1. ElevatedActivity severe onsets >= 100 pooled and >= 20 in each Development year;
2. ElevatedActivity median `signed_F5 < 0` in 2021, 2022, and 2023;
3. pooled ElevatedActivity reversal probability `P(signed_F5<0)` exceeds NormalActivity by >= 5 percentage points;
4. within both fixed severity views, ElevatedActivity median `signed_F5` is lower than NormalActivity median `signed_F5` when both cells have >= 30 events;
5. both positive- and negative-R5 ElevatedActivity directions have >= 30 pooled events and negative median `signed_F5`.

The broad mechanism is `broad_signal_source_supported` only if both indices pass.

## Forbidden rescue

- HighVol or state filters;
- time-of-day filters;
- changing 2.0 / 3.0 / 1.5 thresholds;
- changing the 5-minute primary horizon after results;
- PnL, costs, position sizing or instruments;
- 2024+ data;
- BlackBox.

`production_authority=false`.
