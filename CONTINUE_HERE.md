# Continue here — STAR50 / CSI1000 K-line risk-state bucket

## Read first

1. `CURRENT_RESEARCH.md`
2. `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md`
3. `research/highvol_realtime_horizon_adaptive_v17_validation/DECISIVE_RECEIPT.json`
4. `research/highvol_realtime_horizon_adaptive_v17/FROZEN_REALTIME_TRANSFER.json`
5. `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json`
6. `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`
7. `docs/governance/DATA_USAGE_POLICY_V2.md`
8. `docs/governance/data_usage_declaration.json`
9. `docs/governance/blackbox_query_ledger.json`
10. `AGENTS.md`

Then run:

`python scripts/validate_data_usage_policy.py`

## Current breakpoint

V17 realtime horizon-adaptive recovery annotation has completed Development and its one authorized reusable Validation.

Current decisive state:

`V17_E15S_MULTI_HORIZON_REALTIME_VALIDATION_SUPPORTED_2024_2025`

Validated realtime object at exactly `E-15s`:

- `15m = frozen V16 state + recent-shock age`, using frozen V9 provisional state;
- `30m = frozen V16 state + recent-shock age`, using frozen V9 provisional state;
- `60m = frozen V16 recent-shock-age-only anchor`.

Realtime gating remains fixed: fresh partial shock, provisional `NORMAL`, missing checkpoint, or missing reference window => annotation unavailable.

Reusable Validation authority:

- run `34604089926`;
- artifact `10265472702`;
- cohort `4540` rows over 2024-2025;
- realtime-scored `4516` rows;
- coverage `0.9947136564`;
- exact realtime/final state agreement `0.9918069088`;
- 15m probability MAE `0.000824551`, Brier degradation `-0.000006965`;
- 30m probability MAE `0.000637991`, Brier degradation `+0.000171425`;
- 60m probability/Brier/LogLoss difference exactly `0.0`;
- all 4516 emitted curves satisfy `p15 <= p30 <= p60`.

The final-5m V16 object separately remains validated through `2026-08-21`; V17 realtime authority does **not** extend to 2026 because the authorized 3s physical contract ends at 2025-12-31.

Do **not** rerun V11-V17, refit V16, alter V17 gating, test E-30s/E-60s post hoc on the inspected Validation pool, synthesize 2026 3s data, inspect post-2026-08-21 protected data, or query BlackBox.

No V18 protocol has been authorized or started.

## Current research question

This bucket studies **when K-line conditions causally justify entering, staying in, or leaving a risk state**.

Allowed current objects include current/recent volatility, volatility expansion, shock isolation/recurrence, cross-scale 3s/1m/5m risk evidence, `Unsafe / Recovering / HighVol` state evolution, recovery probability, hysteresis, and diagnostics of false/missed risk states.

The output is a risk-state annotation / gate, not a directional payoff strategy.

## Do not continue these as active research here

- HighVol Router V1 payoff optimization;
- historical directional V10-V17 sign-flip/continuation payoff search;
- new hold/stop/target/sizing/leverage/router variants;
- R1/R2 reversal/MR strategies;
- generic `Range / UpTrend / DownTrend` parent-structure classification.

The historical payoff V17 branches are unrelated to current risk-state V17 and must not be revived.

## Data-use regime

- Development: 2021-01-01 through 2023-12-31;
- reusable 5m Validation: 2024-01-01 through 2026-08-21;
- authorized realtime 3s Validation coverage: 2024-2025 only;
- BlackBox-V1: protected post-cutoff aggregate-only regime under its frozen protocol.

`queried_2026_3s=false`.
`blackbox_queried=false`.
`production_authority=false`.
