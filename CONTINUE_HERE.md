# Continue here — STAR50 / CSI1000 K-line risk-state bucket

## Read first

1. `CURRENT_RESEARCH.md`
2. `research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md`
3. `research/highvol_unsafe_switch_on_v18_validation/DECISIVE_RECEIPT.json`
4. `research/highvol_unsafe_switch_on_v18_validation/FROZEN_VALIDATION_CONTRACT.json`
5. `research/highvol_unsafe_switch_on_v18/DEVELOPMENT_RESULTS.md`
6. `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md`
7. `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json`
8. `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`
9. `docs/governance/DATA_USAGE_POLICY_V2.md`
10. `docs/governance/data_usage_declaration.json`
11. `docs/governance/blackbox_query_ledger.json`
12. `AGENTS.md`

Then run:

`python scripts/validate_data_usage_policy.py`

## Current breakpoint

V18 causal `UNSAFE` switch-on measurement has completed Development and its single authorized reusable Validation.

Current decisive state:

`V18_E15S_UNSAFE_SWITCH_ON_REUSABLE_VALIDATION_SUPPORTED_2024_2025`

Frozen validated V18 object:

- candidate source state = final previous `NORMAL` or `RECOVERING`;
- target = final 5m `risk_state == UNSAFE`;
- primary checkpoint = exactly `E-15s`;
- signal = `(frozen V9 partial_state == UNSAFE)`;
- first/session-boundary bars without the frozen same-session reference chain remain excluded; no overnight repair.

Reusable Validation authority:

- execution commit `35af3b86082791155ae1ba3bf96345c492214d86`;
- run `34607566312`;
- job `103289664712`;
- artifact `10265993683`;
- artifact SHA256 `55a9a3873ce7fb2514183736a5eadb9ce5dfe7e85f2c77162e5f6aa5992398e6`;
- Validation years `2024-2025` only;
- evaluable bars `43,793`;
- true switch-ons `810`;
- E-15s TP / FP / FN / TN = `720 / 37 / 90 / 42946`;
- precision `0.9511228534`;
- recall `0.8888888889`;
- FPR `0.0008608054`;
- 2024 and 2025 annual gates both passed;
- both indices passed;
- `full_validation_supported=true`.

Frozen diagnostic recall curve on Validation: E-60 `0.587654`, E-30 `0.764198`, E-15 `0.888889`, E-6 `0.959259`, E-3 `0.996296`. These later checkpoints remain diagnostics and must not be selected post hoc to replace E-15s.

V18 does **not** claim to predict the first shock before evidence appears. It validates an intrabar causal risk-state switch-on measurement.

## Existing validated recovery authority

V17 remains the validated realtime recovery authority on available 2024-2025 3s coverage. At E-15s it emits the frozen V16 horizon-adaptive recovery object with no refit:

- 15m = state + recent-shock age;
- 30m = state + recent-shock age;
- 60m = recent-shock age only.

V16 remains the final-5m recovery authority through `2026-08-21`. V17/V18 realtime authority does **not** extend to 2026 because authorized 3s coverage ends at 2025-12-31.

## Do not reopen

Do not rerun/refit V11-V18 merely to reconfirm them. Do not change V18 target, cohort boundary, V9 thresholds or primary checkpoint; do not choose E-6s/E-3s after seeing Validation; do not alter V17 gating or refit V16.

Do not synthesize/fabricate 2026 3s coverage, inspect protected post-2026-08-21 data, or query BlackBox.

## Current research question

This bucket studies **when K-line conditions causally justify entering, staying in, or leaving a risk state**. The output is a risk-state annotation/gate, not a directional payoff strategy.

## Data-use regime

- Development: 2021-01-01 through 2023-12-31;
- reusable 5m Validation: 2024-01-01 through 2026-08-21 when separately authorized;
- realtime 3s Validation coverage: 2024-2025 only when separately authorized;
- BlackBox-V1: protected post-cutoff aggregate-only regime under its frozen protocol.

No V19 protocol has been authorized or started.

`v18_validation_queried=true`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`production_authority=false`.
