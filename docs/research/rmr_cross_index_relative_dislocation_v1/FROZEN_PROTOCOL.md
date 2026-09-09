# RMR cross-index relative dislocation V1 — FROZEN PROTOCOL

Status at freeze: results not read.

## Purpose

Test a materially distinct reversal / mean-reversion source: **temporary relative dislocation between STAR50 and CSI1000 after removing their trailing common-index relationship**.

This is a broad signal-source discovery study, not a trading strategy.

## Data role

- subjects: `000688.SH`, `000852.SH`;
- frequency: 1 minute;
- Development only: 2021-01-01 through 2023-12-31;
- no 2024+, no BlackBox;
- same-half-session observations only.

## Causal relationship estimate

At decision minute `t`, estimate STAR50 return as a linear function of CSI1000 return using the **preceding 60 one-minute returns that end before the recent 5-minute displacement window**.

For recent five-minute returns `t-4..t`, the relationship-estimation window is the 60 returns immediately before `t-4`.

OLS with intercept is used. No shrinkage, state filter, or parameter search.

## Relative displacement

Using the frozen trailing `alpha,beta`, define minute residuals:

`e = r_STAR50 - (alpha + beta * r_CSI1000)`.

Recent displacement:

`D5 = sum(e over last 5 minutes)`.

Background residual scale is the sample standard deviation of the 60 OLS residuals.

Standardized dislocation severity:

`Z = abs(D5) / (background_residual_sd * sqrt(5))`.

Rows require finite inputs and background residual SD > 0.

Direction is only descriptive:
- `STAR50_rich` when D5 > 0;
- `STAR50_cheap` when D5 < 0.

## Outcome

Primary future horizon: next 15 minutes, same half-session.

Using the **same frozen alpha,beta from decision time**, calculate future residual sum `F15`.

Signed continuation outcome:

`signed_F15 = sign(D5) * F15`.

- negative = convergence / mean reversion;
- positive = extension.

Primary recovery event:

`recovery50 = signed_F15 <= -0.5 * abs(D5)`.

This is an outcome metric only, not an entry/exit rule.

## Fixed severity bands

- `low`: Z <= 1;
- `mid`: 1 < Z <= 2;
- `high`: Z > 2.

No quantile fitting and no post-result threshold changes.

## Shallow discovery gates

The mechanism is `broad_signal_source_supported` only if all are true:

1. high-Z observations >= 100 in each Development year;
2. high-Z median `signed_F15 < 0` in 2021, 2022, and 2023;
3. pooled high-Z `recovery50` exceeds pooled low-Z `recovery50` by at least 5 percentage points;
4. pooled high-Z median `signed_F15 < 0` separately for `STAR50_rich` and `STAR50_cheap`;
5. each high-Z direction has at least 100 observations pooled.

Anything weaker is descriptive or closed under this V1 identity.

## Forbidden

- PnL/Sharpe;
- cost, stop, target, position sizing;
- threshold or horizon search;
- adding volatility/HighVol filters after results;
- 2024+ data;
- BlackBox;
- production.

`production_authority=false`.
