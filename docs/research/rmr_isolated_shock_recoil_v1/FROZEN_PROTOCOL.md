# RMR isolated-shock recoil V1 — FROZEN PROTOCOL

Status at freeze: results not read.

## Mechanism class

Test whether an isolated abnormal one-minute index shock is followed by short-horizon **price recoil against the shock direction**.

This is a price-reversal study. It is separate from existing post-shock `Unsafe / Recovering` risk-state work, which studies future risk decay rather than directional price recovery.

## Data

- `000688.SH`, `000852.SH`;
- native 1-minute closes;
- Development only: 2021–2023;
- same half-session;
- no Validation / BlackBox / PnL.

## Frozen shock definition

Reuse the repository first-shock operational definition:

At minute `t`, shock if:

1. `abs(r_t) > 30 bp`;
2. `abs(r_t) > 4 × trailing_30m_pre_event_RMS`;
3. RMS floor = 1 bp;
4. the preceding 30 known minutes contain no event of the same definition.

Only rows with complete, source-eligible trailing 30 minutes and complete future evaluation support are admitted.

No shock threshold may be changed in V1.

## Outcomes

Shock direction = `sign(r_t)`.

For horizons 1, 3, 5 and 15 minutes:

`F_h = log(close[t+h]/close[t]) * 1e4`

`signed_F_h = shock_direction * F_h`.

Negative = recoil/reversal; positive = extension.

Primary horizon = 5 minutes. Other horizons are diagnostic only.

Additional descriptive recovery fraction:

`recovery_fraction_5 = -signed_F5 / abs(r_t)`.

Positive means some recovery; `>=0.5` means at least half of the shock magnitude was retraced by minute 5.

## Shallow signal-source gate per index

All must hold:

1. eligible isolated shocks >=100 pooled and >=20 in each Development year;
2. median `signed_F5 < 0` in 2021, 2022 and 2023;
3. pooled `P(signed_F5 < 0) >= 0.55`;
4. pooled UP and DOWN shock groups each have >=30 events and negative median `signed_F5`;
5. pooled median recovery fraction is >0.

The broad source is `broad_signal_source_supported` only if both indices pass all gates.

## Forbidden rescue

- changing 30bp, 4×RMS or 30-minute isolation window;
- clock/HighVol/parent-state/activity filters;
- selecting only UP or DOWN after results;
- changing the 5-minute primary horizon;
- PnL/Sharpe/costs/position sizing;
- Validation/BlackBox.

`production_authority=false`.
