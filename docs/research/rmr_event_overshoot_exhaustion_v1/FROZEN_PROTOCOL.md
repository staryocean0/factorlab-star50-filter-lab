# RMR event-time overshoot exhaustion V1 — FROZEN PROTOCOL

Status at freeze: results not read.

## Mechanism class

Test whether a **causally established directional-change move** becomes more likely to reverse after it completes one additional full-threshold overshoot beyond its confirmation point.

This is an intrinsic/event-time mechanism. It does not require a parent trend (R1), parent range (R2), HighVol state, cross-index residual, or activity filter.

## Data

- subjects: `000688.SH`, `000852.SH`;
- frequency: native 1-minute close;
- Development only: 2021–2023;
- each morning/afternoon half-session processed independently;
- only source-eligible price rows;
- no Validation, BlackBox, PnL or instrument mapping.

## Directional-change engine

Use two **predeclared measurement scales**:

- 20 bp;
- 40 bp.

Thresholds are measurement scales, not strategy parameters and are not searched.

For one half-session:

1. begin with direction unknown and track running high/low;
2. an upward directional change is confirmed when the observed close rises by at least `delta` from the running low;
3. a downward directional change is confirmed when the observed close falls by at least `delta` from the running high;
4. after upward confirmation, track the running peak until a downward directional change is confirmed by a `delta` drawdown from that peak; mirror for downward mode;
5. all decisions use only closes observed at or before the current minute.

No future extrema are used to label an event at decision time.

## Event types

### Confirmation event

The close at which a new up/down directional change is first confirmed.

### Full overshoot event

Within that active directional-change episode, the first close at which price has extended another **one full `delta`** beyond the confirmation close in the active direction.

Only one full-overshoot event is admitted per directional-change episode.

## Outcome

Primary horizon: next 5 minutes, same half-session.

`F5 = log(close[t+5] / close[t]) * 1e4`

`signed_F5 = active_direction * F5`

- negative = reversal against the active directional-change move;
- positive = continuation.

Secondary diagnostic: same definition over next 15 minutes. It cannot rescue a failed 5-minute primary result.

## Shallow gate per symbol × scale

A fixed scale passes only if all are true:

1. full-overshoot events >=100 pooled and >=20 in each Development year;
2. full-overshoot median `signed_F5 < 0` in 2021, 2022 and 2023;
3. pooled full-overshoot reversal probability exceeds confirmation-event reversal probability by >=5 percentage points;
4. pooled full-overshoot median `signed_F5` is at least 2 bp lower than confirmation-event median `signed_F5`;
5. pooled up-overshoot and down-overshoot each have >=30 events and negative median `signed_F5`.

The broad mechanism is `broad_signal_source_supported` only if at least one of the two predeclared scales passes for **both indices at the same scale**.

If only one index or one unmatched scale passes, record descriptive evidence but do not hand off the mechanism.

## Forbidden rescue

- changing 20/40 bp scales after results;
- testing half-threshold or multiple-threshold overshoots inside V1;
- adding parent-state, HighVol, activity, clock or direction filters;
- changing the 5-minute primary horizon;
- PnL/Sharpe/costs/positions;
- Validation or BlackBox.

`production_authority=false`.
