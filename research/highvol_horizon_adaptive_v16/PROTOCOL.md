# HighVol recovery V16 — monotone horizon-adaptive surface (Development)

## Purpose

V15 Development established a horizon-dependent information structure: `current_state` adds robust predictive value beyond recent-shock age at 15m and 30m, while the 60m increment is not robust under the preregistered trading-day clustered bootstrap.

V16 constructs one deterministic multi-horizon recovery object from that result, entirely in Development.

## Frozen inputs

- Development: 2021-2023; 2020 warm-up only.
- Symbols: `000688.SH`, `000852.SH`.
- Same V11 common cohort; expected rows: `7327`.
- States: `UNSAFE`, `RECOVERING`.
- Age buckets: `LT15`, `M15_25`, `M30_40`, `GE45`.
- Horizons: `15m`, `30m`, `60m`.
- Same shock-reset clock and state thresholds.

V15 decisive authority: run `34497176574`, artifact `10160290575`, receipt `research/highvol_horizon_composite_v15/DECISIVE_RECEIPT.json`.

No Validation result is used as a fitted probability or parameter.

## Fixed component models

Within each leave-one-year-out fold and for the final full-Development surface:

- 15m raw probability: Laplace-smoothed `(current_state, age_bucket)` table;
- 30m raw probability: Laplace-smoothed `(current_state, age_bucket)` table;
- 60m anchor probability: Laplace-smoothed `age_bucket` table only.

There is no model menu and no feature search.

## Deterministic monotone construction

For every state×age cell or scored row, define:

- `p60 = raw_age_only_60`;
- `p30 = min(raw_state_age_30, p60)`;
- `p15 = min(raw_state_age_15, p30)`.

This is a backward cap only. It never increases a short-horizon probability and never changes the 60m age-only anchor. Therefore the emitted cumulative recovery curve always satisfies `p15 <= p30 <= p60`.

No alternative projection, weight, interpolation, or isotonic tuning is authorized.

## Fixed Development support rule

V16 is eligible to freeze for reusable Validation only if all are true:

1. cohort row count is exactly `7327`;
2. every state×age training cell in leave-one-year-out has `n >= 50`;
3. every out-of-fold emitted row satisfies `p15 <= p30 <= p60`;
4. all 8 cells in the full-Development emitted surface satisfy the same monotonicity;
5. the 60m emitted probability is state-invariant within each age bucket and exactly equals the age-only 60m anchor;
6. pooled LOYO Brier for the adaptive surface beats age-only at 15m and 30m;
7. pooled LOYO LogLoss beats age-only at 15m and 30m;
8. annual held-out Brier beats age-only in at least 2 of 3 years at both 15m and 30m;
9. at 60m the adaptive surface is exactly score-equivalent to age-only (Brier and LogLoss difference within `1e-12`);
10. any monotonicity adjustment is downward-only and leaves `p60` unchanged;
11. state thresholds, age buckets, horizons, cohort and shock-reset clock are unchanged;
12. Validation and BlackBox are not queried;
13. no PnL, payoff, routing or trading rule is created.

A failure cannot be rescued by changing the projection, dropping a horizon/year, or changing state/age definitions.

## Boundary

A Development PASS authorizes freezing this exact surface and one reusable Validation. It does not create production authority.

`production_authority=false`.
