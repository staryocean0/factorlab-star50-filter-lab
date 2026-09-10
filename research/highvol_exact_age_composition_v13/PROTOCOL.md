# HighVol exact recent-shock-age composition V13 — Development protocol

Purpose: explain the V11 60-minute state-rank crossover without changing the validated risk-state thresholds, recovery horizons, or coarse age buckets.

V11 showed `RECOVERING > UNSAFE` for cumulative normalization at 15m and 30m, but `UNSAFE > RECOVERING` at 60m in all four coarse recent-shock-age buckets. V12 rejected a simple deterministic 12-bar RV-window expiry spike as the explanation.

## Frozen question

Does the V11 60m crossover arise from different **exact recent-shock-age composition** inside/alongside the coarse age buckets (a Simpson-style composition effect)?

## Data boundary

- symbols: `000688.SH`, `000852.SH`;
- 2020: warm-up only;
- Development measured years: 2021, 2022, 2023;
- no 2024+, Validation, or BlackBox data;
- no PnL, payoff, routing, sizing, or trading rule.

## Inherited state and sample

Reuse V11 exactly:

- 5m log returns;
- `rv12 = std(last 12 valid 5m returns, ddof=0)`;
- `bg48 = std(previous 48 valid 5m returns, ddof=0)`;
- shock if `abs(ret_5m)/bg48 >= 3.0`;
- `UNSAFE` if shock or active-state `rv12/bg48 >= 1.50`;
- `RECOVERING` if active-state `1.10 < rv12/bg48 < 1.50`;
- `NORMAL` at `rv12/bg48 <= 1.10`;
- every new shock resets `recent_shock_age_bars`;
- common cohort requires a full 60 trading minutes of same-day support;
- fixed outcomes: Normal within 15m / 30m / 60m.

No state threshold, horizon, age definition, or sample rule may change.

## Exact-age standardization

For each exact integer `recent_shock_age_bars`, report state counts and cumulative recovery rates at 15/30/60m.

Primary standardization uses every exact age for which both `UNSAFE` and `RECOVERING` are observed. At each age, estimate the state-specific cumulative probability using the same Beta(1,1) smoothing used by V11. Weight exact ages by their pooled combined (`UNSAFE + RECOVERING`) frequency, so both states are evaluated under the **same exact-age distribution**.

Also report a deterministic in-window view for ages 1..11, corresponding to the period before the most recent shock leaves the fixed 12-bar `rv12` window. This is descriptive and cannot replace the primary all-common-age result.

Repeat the same exact-age standardization separately for 2021, 2022, and 2023 using each year's own common exact-age support and combined-age weights.

## Frozen interpretation rule

`exact_age_composition_explains_60m_crossover=true` only if all are true:

1. the unstandardized pooled 60m gap on common exact-age support is `RECOVERING - UNSAFE < 0`;
2. the exact-age-standardized pooled 60m gap is `> 0`;
3. exact-age standardization produces a positive 60m gap in at least 2 of the 3 Development years;
4. state thresholds/sample/horizons are unchanged;
5. Validation and BlackBox remain unqueried.

If the standardized 60m gap remains negative, the crossover is not explainable as a simple exact-age composition artifact; `UNSAFE/RECOVERING` must be treated as horizon-dependent states rather than a horizon-invariant ordinal severity ranking.

No Validation is authorized by V13 itself. V13 is a Development mechanism adjudication only.

`production_authority=false`.
