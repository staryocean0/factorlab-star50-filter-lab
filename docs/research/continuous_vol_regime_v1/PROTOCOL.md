# Continuous volatility regime V1 — frozen protocol

Date: 2026-09-08
Status: development/validation research only; no black-box query; no production authority.

Governance: future-use policy on `main` commit `e383ae4a5cd5a41eda378b81be1b517ccd519d5f`, `docs/governance/DATA_USAGE_POLICY_V2.md`.

## Question

The earlier first-shock `Unsafe` state is too sparse for stable trading-frequency research. Test the broader owner hypothesis directly: when the market is already in a causally observable high-volatility environment, does the economically useful trading frequency become shorter because price movement can cover higher turnover costs?

## Data roles

- Development pool: 2021-01-01 through 2023-12-31. Candidate nomination and all selection happen here only.
- Validation pool: 2024-01-01 through 2026-08-21. No fitting/selection for the candidate under test. After the frozen candidate is evaluated, detailed validation diagnostics are allowed.
- BlackBox-V1: not queried.
- Subjects: `000688.SH`, `000852.SH`.
- 2020 data, where present, are warm-up only.

## Continuous causal regime

Within each 120-minute half-session, use official valid 1-minute closes only. Never bridge lunch, overnight, invalid/repaired rows, or missing minutes.

For minute close `t`:

- `r_t = 1e4 * log(close_t / close_{t-1})` if both adjacent minutes are valid, else unknown.
- `fast5_t = RMS(r_{t-4}, ..., r_t)`.
- `background30_t = RMS(r_{t-34}, ..., r_{t-5})`.
- Windows are non-overlapping and require complete finite returns.
- `vol_ratio_t = fast5_t / max(background30_t, 1 bp)`.
- `HighVol` iff `vol_ratio_t >= 1.5`.
- `NormalVol` iff known and `< 1.5`.
- otherwise `Unknown`.

The threshold `1.5` and 1bp background floor are inherited from the already-frozen post-shock state work; no threshold search is allowed in V1.

This state is deliberately **not** conditioned on a first-shock trigger.

## Strategy surface

Reuse the already-tested physical-scale strategy implementation:

- scales: 1, 2, 3, 5, 10, 15 minutes;
- families:
  - `scaled_clock`: 12-bar low-pass period and 48-bar volatility memory at every scale (physical clock shrinks with sampling);
  - `fixed_physical`: approximately 60-minute low-pass and 240-minute volatility memory (`period=60/scale`, `window=240/scale`);
- original one-bar OHLC aggregation semantics from the Phase-2 exact-equivalent grid;
- original two-bar execution delay;
- positions forced flat at every half-session boundary;
- no cross-gap return;
- abstract one-way cost stresses 0.5/1/2/3/5 bp.

Gates reported for every menu item:

- `Ungated`;
- `HighVol` only;
- `NormalVol` only.

## Development-only nomination rule

For each symbol separately:

1. Use only 2021-2023 `HighVol` rows.
2. Compute pooled `net_bp_per_exposure_min_cost_1` for all 12 `(family, scale)` menu items.
3. A menu item is eligible only if it has positive `net_bp_per_exposure_min_cost_1` in at least 2 of the 3 development years and nonzero HighVol exposure in all 3 years.
4. Among eligible items, nominate the highest pooled development value. If none is eligible, nominate `NONE`.
5. Tie-breaker: lower scale first, then `fixed_physical` before `scaled_clock`.

No validation result may change this nomination.

## Primary validation questions

For the development-nominated candidate, evaluated unchanged on 2024, 2025 and 2026-through-08-21:

1. Is HighVol net performance after 1bp one-way abstract cost positive in at least 2 validation slices and pooled validation?
2. Is HighVol break-even one-way cost above 1bp pooled validation?
3. Does the candidate outperform the same candidate in NormalVol on `net_bp_per_exposure_min_cost_1` pooled validation?
4. Does it outperform the original 5-minute anchor in HighVol pooled validation?

These are research diagnostics, not a production promotion rule.

## Secondary diagnostics

After the primary candidate validation is recorded, the full validation menu may be inspected because the period is a reusable Validation pool. Any new pattern discovered there must return to Development for a new candidate/protocol before being called a new result.

## Guardrails

- No BlackBox-V1 access.
- No first-shock predictor claim.
- No parameter/threshold search on Validation for the candidate under test.
- No ETF/futures execution claim from index bars.
- No production/live promotion.
