# Current research entry

## 2026-09-11 current authority

**Current task: STAR50 / CSI1000 bottom-layer K-line risk-state research only.**

The research product of this bucket is a causal risk annotation/gate. It is not a directional trading strategy.

## Current validated switch-on authority — V18

V18 fills the entry-side gap in the risk-state machine. It measures when causal evidence already available **inside a still-forming 5m bar** is sufficient for the unchanged frozen V9 state machine to switch from final previous state `NORMAL` or `RECOVERING` into `UNSAFE`.

V18 does **not** reopen the failed ordinary-session first-shock forecasting problem. It does not claim to predict a shock before within-bar evidence exists.

### Development authority

- branch: `research/highvol-unsafe-switch-on-v18-20260911`;
- execution commit: `542b11857baeaebd43d93dc5ac866c6c3316e477`;
- run: `34606023820`;
- job: `103284525209`;
- artifact: `10266486662`;
- artifact SHA256: `7071121c24c65f877f5e76faf875a86ee25da051fde0ffbf8e1d35934933d8ec`;
- exact V18 runner blob: `62c207badff1c3e37cbb1a8e17ef89feeea611d8`;
- exact frozen V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`;
- Development: 2021-2023 only;
- evaluable bars: `65,431`;
- true new `UNSAFE` switch-ons: `1,361`;
- E-15s precision / recall / FPR: `0.9706564 / 0.9235856 / 0.0005931`;
- all preregistered Development gates passed.

### Reusable Validation authority

The exact frozen V18 E-15s measurement has now passed its single authorized reusable Validation on existing 2024-2025 3s coverage.

- branch: `research/highvol-unsafe-switch-on-v18-validation-20260911`;
- execution commit: `35af3b86082791155ae1ba3bf96345c492214d86`;
- run: `34607566312`;
- job: `103289664712`;
- artifact: `10265993683`;
- artifact SHA256: `55a9a3873ce7fb2514183736a5eadb9ce5dfe7e85f2c77162e5f6aa5992398e6`;
- Validation period: 2024-2025 only;
- queried 3s years: 2024 and 2025 only;
- evaluable bars: `43,793` (`2024=21,816`, `2025=21,977`);
- true new `UNSAFE` switch-ons: `810`;
- TP / FP / FN / TN: `720 / 37 / 90 / 42946`;
- E-15s precision: **`0.9511228534`**;
- E-15s recall: **`0.8888888889`**;
- E-15s false-positive rate: **`0.0008608054`**;
- specificity: `0.9991391946`;
- `full_validation_supported=true`.

Annual E-15s stability:

- 2024: 418 true events; precision `0.951899`, recall `0.899522`, FPR `0.000888`;
- 2025: 392 true events; precision `0.950276`, recall `0.877551`, FPR `0.000834`.

Both symbols passed:

- `000688.SH`: 412 true events; precision `0.950131`, recall `0.878641`, FPR `0.000885`;
- `000852.SH`: 398 true events; precision `0.952128`, recall `0.899497`, FPR `0.000836`.

Source-state decomposition at E-15s:

- `NORMAL -> UNSAFE`: 550 true events; precision `0.936170`, recall `0.880000`;
- `RECOVERING -> UNSAFE`: 260 true events; precision `0.983333`, recall `0.907692`.

Final switch-on pathways: `shock_entry=612`, `recovery_reescalation=198`. No pathway-specific rule was fitted.

### Frozen evidence-accumulation curve

The other checkpoints remain descriptive diagnostics and cannot replace the frozen E-15s primary checkpoint:

| Checkpoint | Validation recall |
|---|---:|
| E-60s | 0.587654 |
| E-30s | 0.764198 |
| E-15s | **0.888889** |
| E-6s | 0.959259 |
| E-3s | 0.996296 |

Earliest first detection among the 810 Validation switch-ons: `E-60=476`, `E-30=171`, `E-15=99`, `E-6=46`, `E-3=15`, `undetected=3`. There are `87` events that form only after E-15s. Persistence after first frozen-checkpoint detection is `0.936803`.

The unchanged V9 causal boundary remains in force: opening/session-boundary rows without the same-session previous-close/background/prior-window chain are excluded rather than repaired with overnight information.

Primary sealed V18 evidence:

- `research/highvol_unsafe_switch_on_v18/PROTOCOL.md`;
- `research/highvol_unsafe_switch_on_v18/DEVELOPMENT_RESULTS.md`;
- `research/highvol_unsafe_switch_on_v18/DECISIVE_RECEIPT.json`;
- `research/highvol_unsafe_switch_on_v18_validation/PROTOCOL.md`;
- `research/highvol_unsafe_switch_on_v18_validation/FROZEN_VALIDATION_CONTRACT.json`;
- `research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md`;
- `research/highvol_unsafe_switch_on_v18_validation/DECISIVE_RECEIPT.json`.

## Current validated realtime recovery authority — V17

V17 remains the validated recovery-side realtime authority on available 2024-2025 3s coverage. At exactly E-15s it transfers the frozen V16 multi-horizon recovery object without refit:

- 15m = frozen V16 `state + recent-shock age` using frozen V9 provisional state;
- 30m = frozen V16 `state + recent-shock age` using frozen V9 provisional state;
- 60m = frozen V16 recent-shock-age-only anchor.

V17 reusable Validation: run `34604089926`, artifact `10265472702`, 4,540 cohort rows, 4,516 realtime-scored, coverage `0.9947136564`, `full_validation_supported=true`. The 60m realtime prediction is exactly the frozen age-only anchor row-by-row.

Primary sealed V17 evidence:

- `research/highvol_realtime_horizon_adaptive_v17/FROZEN_REALTIME_TRANSFER.json`;
- `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md`;
- `research/highvol_realtime_horizon_adaptive_v17_validation/DECISIVE_RECEIPT.json`.

## Current validated final-5m recovery authority — V16

V16 remains the final-5m recovery authority through `2026-08-21`:

- 15m = `current_state + time-since-most-recent-shock`;
- 30m = `current_state + time-since-most-recent-shock`;
- 60m = `time-since-most-recent-shock only`.

V16 reusable Validation: run `34602527314`, artifact `10264689647`, 5,908 scored rows through 2026-08-21, `full_validation_supported=true`.

V16's authorized 2026 final-5m construction does not create 2026 3s realtime data for V17 or V18.

## Current supported causal risk process

The validated architecture is now:

`V18 causal switch-on evidence -> UNSAFE -> RECOVERING -> V16/V17 multi-horizon recovery -> Normal`

Entry and recovery are separate scientific objects with separate data boundaries:

1. **entry / switch-on:** V18 E-15s is validated on available 2024-2025 3s coverage;
2. **recovery:** V16 final-5m is validated through 2026-08-21, while V17 E-15s realtime recovery is validated on 2024-2025 3s coverage.

The recovery clock rule remains:

> Every new shock resets the recovery clock. Recovery risk is indexed by time since the most recent shock, not time since the first shock of the episode.

## Completed evidence chain that must not be casually reopened

- V3-V6 established and validated the post-shock recovery-state / recent-shock-age mechanism;
- V7 failed the frozen 1m realtime recall gate;
- V8-V10 established the 3s realtime state/probability transfer and E-15s checkpoint;
- V11-V15 established horizon-dependent state value and rejected a unified state+age 60m surface;
- V16 froze and validated the horizon-adaptive 5m recovery surface;
- V17 validated its E-15s realtime recovery transfer on 2024-2025 3s;
- V18 now validates the entry-side E-15s causal UNSAFE switch-on measurement on 2024-2025 3s.

Do not rerun these versions merely to reconfirm them.

## Scope-repaired bucket authority

This repository owns bottom-layer causal K-line risk-state research only, including volatility level/expansion, shock isolation/recurrence, `Unsafe / Recovering / HighVol` state evolution, switch-on, persistence, recovery, recovery probability, and cross-scale 3s/1m/5m risk attributes.

It does **not** own directional payoff optimization, holding period, stop/target, sizing, leverage, account overlays or payoff routers. Historical payoff/router material remains archive evidence only.

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

`V18_E15S_UNSAFE_SWITCH_ON_REUSABLE_VALIDATION_SUPPORTED_2024_2025`

Do **not** rerun or refit V18, select E-6s/E-3s post hoc, alter the target/cohort/V9 thresholds, synthesize 2026 3s coverage, or query BlackBox.

No V19 protocol has been authorized or started.

`v18_validation_queried=true`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`pnl_computed=false`.
`production_authority=false`.
