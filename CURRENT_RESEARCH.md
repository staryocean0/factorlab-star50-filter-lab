# Current research entry

## 2026-09-11 current authority

**Current task: STAR50 / CSI1000 bottom-layer K-line risk-state research only.**

The research product of this bucket is a causal risk annotation/gate. It is not a directional trading strategy.

## Current switch-on research authority — V18 Development

V18 fills the entry-side gap in the risk-state machine. It asks when causal evidence already available **inside a still-forming 5m bar** is sufficient for the unchanged frozen V9 state machine to switch from final previous state `NORMAL` or `RECOVERING` into `UNSAFE`.

V18 does **not** reopen the failed ordinary-session first-shock forecasting problem. It does not claim to predict the shock before any within-bar evidence appears.

### Frozen V18 authority

- branch: `research/highvol-unsafe-switch-on-v18-20260911`;
- execution commit: `542b11857baeaebd43d93dc5ac866c6c3316e477`;
- run: `34606023820`;
- job: `103284525209`;
- artifact: `10266486662`;
- artifact SHA256: `7071121c24c65f877f5e76faf875a86ee25da051fde0ffbf8e1d35934933d8ec`;
- exact frozen V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`;
- Development: 2021-2023 only;
- `development_supported=true`;
- `validation_queried=false`;
- `validation_eligible_but_not_authorized=true`.

The causal-evaluable cohort contains **65,431** bars. There are **1,361** true new `UNSAFE` entries:

- shock entry: `970`;
- `RECOVERING` re-escalation without a final shock: `391`.

The first 5m bar of a trading day remains outside the V18 evaluable cohort whenever the frozen V9 same-day previous-close/reference chain is unavailable. V18 does not import an overnight previous close and does not create an opening-bar exception.

### Frozen E-15s primary result

At the preregistered primary checkpoint `E-15s`:

- checkpoint coverage: `1.0`;
- TP / FP / FN / TN: `1257 / 38 / 104 / 64032`;
- precision: **`0.9706564`**;
- recall: **`0.9235856`**;
- false-positive rate: **`0.0005931`**;
- specificity: `0.9994069`.

All preregistered annual gates passed:

- 2021: 490 events; precision `1.0000`, recall `0.9918`, FPR `0.000000`;
- 2022: 469 events; precision `0.9729`, recall `0.9190`, FPR `0.000566`;
- 2023: 402 events; precision `0.9290`, recall `0.8458`, FPR `0.001203`.

Both symbols passed with nonzero events and true positives:

- `000688.SH`: 720 events; precision `0.9661`, recall `0.9097`, FPR `0.000723`;
- `000852.SH`: 641 events; precision `0.9757`, recall `0.9392`, FPR `0.000465`.

Source-state decomposition at E-15s:

- from `NORMAL`: 876 true entries; precision `0.9636`, recall `0.9064`;
- from `RECOVERING`: 485 true entries; precision `0.9830`, recall `0.9546`.

### Fixed evidence-accumulation curve

The full fixed curve is descriptive only and cannot be used to replace a failure at E-15s:

| Checkpoint | Precision | Recall | FPR |
|---|---:|---:|---:|
| E-60s | 0.8078 | 0.5805 | 0.002934 |
| E-30s | 0.9277 | 0.8486 | 0.001405 |
| E-15s | **0.9707** | **0.9236** | **0.000593** |
| E-6s | 0.9849 | 0.9603 | 0.000312 |
| E-3s | 0.9993 | 0.9956 | 0.000016 |

Earliest first detection among the 1,361 true switch-ons:

- E-60s: `790`;
- E-30s: `389`;
- E-15s: `103`;
- E-6s: `45`;
- E-3s: `28`;
- undetected by E-3s: `6`.

Among events detected at any checkpoint, `96.75%` remain `UNSAFE` at every later fixed checkpoint after first detection. There are `98` true switch-ons not yet signalled at E-15s that form only at E-6s or E-3s.

Primary sealed V18 evidence:

- `research/highvol_unsafe_switch_on_v18/PROTOCOL.md`;
- `research/highvol_unsafe_switch_on_v18/DEVELOPMENT_RESULTS.md`;
- `research/highvol_unsafe_switch_on_v18/DECISIVE_RECEIPT.json`.

The decisive V18 action is:

`FREEZE_E15S_SWITCH_ON_MEASUREMENT_AND_STOP_BEFORE_VALIDATION`

A reusable Validation is scientifically eligible but has **not** been authorized or run.

## Current validated realtime recovery authority — V17

V17 remains the validated **recovery-side** realtime authority on available 2024-2025 3s coverage. At exactly `E-15s`, it transfers the frozen V16 multi-horizon recovery object without refit:

- `15m = frozen V16 state + recent-shock age`, using the frozen V9 provisional partial-bar state;
- `30m = frozen V16 state + recent-shock age`, using the frozen V9 provisional partial-bar state;
- `60m = frozen V16 recent-shock-age-only anchor`.

V17 reusable Validation authority:

- run: `34604089926`;
- job: `103278189791`;
- artifact: `10265472702`;
- artifact SHA256: `65783daff1ca83217ad8159b52e2c4f9d6c79f8195a11aa4b1c4af80aa2d1714`;
- Validation period: 2024-2025 only;
- common cohort: `4540` rows;
- realtime-scored rows: `4516`;
- coverage: `0.9947136564`;
- exact realtime/final state agreement: `0.9918069088`;
- 15m probability MAE `0.000824551`, Brier degradation `-0.000006965`;
- 30m probability MAE `0.000637991`, Brier degradation `+0.000171425`;
- 60m probability/Brier/LogLoss difference exactly `0.0`;
- `full_validation_supported=true`.

All emitted Validation curves satisfy `p15 <= p30 <= p60`.

The authorized 3s physical contract ends at `2025-12-31`. V17 therefore has no 2026 realtime authority and no 2026 3s data was queried or synthesized.

Primary sealed V17 evidence:

- `research/highvol_realtime_horizon_adaptive_v17/FROZEN_REALTIME_TRANSFER.json`;
- `research/highvol_realtime_horizon_adaptive_v17/DECISIVE_RECEIPT.json`;
- `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md`;
- `research/highvol_realtime_horizon_adaptive_v17_validation/DECISIVE_RECEIPT.json`.

## Current validated final-5m recovery authority — V16

V16 remains the final-5m recovery authority through `2026-08-21`:

- 15m = `current_state + time-since-most-recent-shock`;
- 30m = `current_state + time-since-most-recent-shock`;
- 60m = `time-since-most-recent-shock only`.

V16 reusable Validation authority:

- run: `34602527314`;
- artifact: `10264689647`;
- artifact SHA256: `e28a877d40c3bd2464b4f09b1078cdfae83a7ecebcc8bbd34fdb7bad4e8d82f5`;
- common scored rows: `5908`;
- year rows: `2024=2339`, `2025=2201`, `2026=1368` through `2026-08-21`;
- `full_validation_supported=true`.

V16's authorized 2026 final-5m construction does not create 2026 3s realtime data for V17 or V18.

## Current supported causal risk process

The supported architecture is now:

`causal switch-on evidence -> UNSAFE -> RECOVERING -> Normal`

with two distinct authorities:

1. **entry / switch-on:** V18 Development supports the frozen E-15s partial-state measurement for new `UNSAFE` entries, but Validation is not yet authorized;
2. **recovery:** V16 final-5m and V17 E-15s realtime recovery surfaces are already validated within their stated data boundaries.

The recovery clock rule remains:

> Every new shock resets the recovery clock. Recovery risk is indexed by time since the most recent shock, not time since the first shock of the episode.

## Completed evidence chain that must not be casually reopened

- V3-V6 established and validated the post-shock recovery-state / recent-shock-age mechanism;
- V7 failed the frozen 1m realtime recall gate;
- V8-V10 established the 3s realtime state/probability transfer and E-15s checkpoint;
- V11-V15 established horizon-dependent state value and rejected a unified state+age 60m surface;
- V16 froze and validated the horizon-adaptive 5m surface;
- V17 validated its E-15s realtime transfer on 2024-2025 3s;
- V18 now supports the entry-side E-15s switch-on measurement in Development only.

Do not rerun these versions merely to reconfirm them.

## Scope-repaired bucket authority

This repository owns bottom-layer causal K-line risk-state research only, including:

- volatility level / expansion;
- shock isolation and recurrence;
- `Unsafe / Recovering / HighVol` state evolution;
- switch-on, persistence, recovery and recovery probability;
- cross-scale 3s / 1m / 5m risk attributes and failure cases.

The current task is **not** to optimize a directional trading strategy, holding period, stop/target, sizing, account overlay or payoff router.

Historical HighVol Router V1, historical directional STAR50 V10-V17 sign-flip work, half-day slope work, drawdown/account/payoff diagnostics and misplaced R1/R2 material remain preserved but are not current authority. Historical payoff V17 branches are unrelated to the risk-state V17 and must not be revived.

Correct neighboring buckets:

- `factorlab-two-wave-strategy-lab`: causal parent-structure classification into range / uptrend / downtrend from completed same-scale waves;
- `factorlab-trend-reversion-regime-lab`: concrete reversal / mean-reversion strategy research including R1/R2.

## Data and governance

Read before new work:

- `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`;
- `docs/governance/DATA_USAGE_POLICY_V2.md`;
- `docs/governance/data_usage_declaration.json`;
- `docs/governance/blackbox_query_ledger.json`.

Forward data roles:

- 2020: warm-up only where needed;
- Development: 2021-2023;
- reusable 5m Validation: 2024 through 2026-08-21 only under separately authorized protocols;
- realtime 3s Validation coverage: 2024-2025 only under separately authorized protocols;
- protected BlackBox-V1: strictly after the cutoff under its frozen aggregate-only protocol.

No prior payoff or risk-state result automatically authorizes BlackBox access.

## Current breakpoint

The current decisive state is:

`V18_E15S_UNSAFE_SWITCH_ON_DEVELOPMENT_SUPPORTED_VALIDATION_NOT_AUTHORIZED`

Do **not** run V18 Validation unless separately authorized. Do not alter the frozen E-15s checkpoint, target, cohort boundary, V9 state thresholds, or opening-bar exclusion after seeing the Development result.

Do not rerun V11-V17, refit V16, alter V17 gating, synthesize/fabricate 2026 3s coverage, inspect protected post-2026-08-21 data, or query BlackBox.

`v18_validation_queried=false`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`pnl_computed=false`.
`production_authority=false`.
