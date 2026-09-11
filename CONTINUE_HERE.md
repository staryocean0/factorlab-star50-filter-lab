# Continue here — STAR50 / CSI1000 K-line risk-state bucket

## Read first

1. `CURRENT_RESEARCH.md`
2. `research/highvol_unsafe_switch_on_v18/DEVELOPMENT_RESULTS.md`
3. `research/highvol_unsafe_switch_on_v18/DECISIVE_RECEIPT.json`
4. `research/highvol_unsafe_switch_on_v18/PROTOCOL.md`
5. `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md`
6. `research/highvol_realtime_horizon_adaptive_v17_validation/DECISIVE_RECEIPT.json`
7. `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json`
8. `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`
9. `docs/governance/DATA_USAGE_POLICY_V2.md`
10. `docs/governance/data_usage_declaration.json`
11. `docs/governance/blackbox_query_ledger.json`
12. `AGENTS.md`

Then run:

`python scripts/validate_data_usage_policy.py`

## Current breakpoint

V18 causal `UNSAFE` switch-on measurement has completed **Development only** and passed every preregistered gate.

Current decisive state:

`V18_E15S_UNSAFE_SWITCH_ON_DEVELOPMENT_SUPPORTED_VALIDATION_NOT_AUTHORIZED`

Frozen V18 Development authority:

- branch `research/highvol-unsafe-switch-on-v18-20260911`;
- execution commit `542b11857baeaebd43d93dc5ac866c6c3316e477`;
- run `34606023820`;
- artifact `10266486662`;
- artifact SHA256 `7071121c24c65f877f5e76faf875a86ee25da051fde0ffbf8e1d35934933d8ec`;
- evaluable bars `65,431`;
- true new `UNSAFE` switch-ons `1,361`;
- primary checkpoint `E-15s`;
- E-15s precision `0.9706564`;
- E-15s recall `0.9235856`;
- E-15s false-positive rate `0.0005931`;
- all 2021/2022/2023 annual gates passed.

The fixed evidence-accumulation curve is descriptive only: recall rises from `0.5805` at E-60s to `0.8486` at E-30s, `0.9236` at E-15s, `0.9603` at E-6s, and `0.9956` at E-3s. The later checkpoints must not be selected post hoc to replace the frozen E-15s primary checkpoint.

V18 does **not** claim to predict the first shock before evidence appears. It measures when the unchanged frozen V9 partial-bar state machine has accumulated enough within-bar causal evidence to enter `UNSAFE` from final previous state `NORMAL` or `RECOVERING`.

The first 5m bar of each trading day remains outside the V18 evaluable cohort when frozen V9 lacks the same-day previous-close/reference chain. Do not import an overnight previous close or create an opening-bar exception.

The decisive receipt says:

`FREEZE_E15S_SWITCH_ON_MEASUREMENT_AND_STOP_BEFORE_VALIDATION`

Therefore **do not run V18 reusable Validation without separate authorization**. `validation_queried=false` for V18.

## Existing validated recovery authority

V17 remains the validated realtime recovery-probability authority on available 2024-2025 3s coverage. At E-15s it emits the frozen V16 horizon-adaptive recovery object with no refit:

- 15m = state + recent-shock age;
- 30m = state + recent-shock age;
- 60m = recent-shock age only.

V16 remains the final-5m recovery authority through `2026-08-21`. V17 realtime authority does **not** extend to 2026 because authorized 3s coverage ends at 2025-12-31.

Do not rerun V11-V17, refit V16, alter V17 gating, synthesize 2026 3s data, inspect protected post-2026-08-21 data, or query BlackBox.

## Current research question

This bucket studies **when K-line conditions causally justify entering, staying in, or leaving a risk state**.

Allowed current objects include current/recent volatility, volatility expansion, shock isolation/recurrence, cross-scale 3s/1m/5m risk evidence, `Unsafe / Recovering / HighVol` state evolution, switch-on, persistence, recovery probability, hysteresis, and diagnostics of false/missed risk states.

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
- reusable 5m Validation: 2024-01-01 through 2026-08-21 when separately authorized;
- authorized realtime 3s Validation coverage: 2024-2025 only when separately authorized;
- BlackBox-V1: protected post-cutoff aggregate-only regime under its frozen protocol.

`v18_validation_queried=false`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`production_authority=false`.
