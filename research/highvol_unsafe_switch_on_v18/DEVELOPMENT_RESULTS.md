# V18 causal UNSAFE switch-on — Development results

Status: **SUPPORTED IN DEVELOPMENT**

V18 measures when the already-frozen V9 partial-bar state machine has accumulated enough causal evidence inside a still-forming 5m bar to justify a new `UNSAFE` switch. It does not predict a shock before evidence appears and does not create a trading rule.

## Authority

- branch: `research/highvol-unsafe-switch-on-v18-20260911`
- execution commit: `542b11857baeaebd43d93dc5ac866c6c3316e477`
- run: `34606023820`
- job: `103284525209`
- artifact: `10266486662`
- artifact SHA256: `7071121c24c65f877f5e76faf875a86ee25da051fde0ffbf8e1d35934933d8ec`
- exact frozen V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`

Development only: 2021-2023. Validation and BlackBox were not queried.

## Cohort

The causal-evaluable cohort contains **65,431** final 5m bars whose prior final state is `NORMAL` or `RECOVERING` and for which the frozen V9 partial-state construction has its required same-day reference inputs.

Each symbol has 727 source-state rows outside the evaluable cohort because the frozen V9 same-day previous-close/reference chain is unavailable there. V18 does not import an overnight previous close or create an opening-bar exception.

True new `UNSAFE` switch-ons: **1,361** (`2.0801%` of evaluable bars).

Pathways:

- shock entry: **970**;
- `RECOVERING` re-escalation without a final shock: **391**.

## Primary E-15s result

The preregistered primary checkpoint is `E-15s`.

- candidate rows: `65,431`;
- checkpoint coverage: **1.0000**;
- true switch-ons: `1,361`;
- signals: `1,295`;
- TP / FP / FN / TN: `1257 / 38 / 104 / 64032`;
- precision: **0.9706564**;
- recall: **0.9235856**;
- false-positive rate: **0.0005931**;
- specificity: **0.9994069**.

All preregistered pooled and annual acceptance gates passed.

Annual E-15s:

| Year | Events | Precision | Recall | FPR |
|---|---:|---:|---:|---:|
| 2021 | 490 | 1.0000 | 0.9918 | 0.000000 |
| 2022 | 469 | 0.9729 | 0.9190 | 0.000566 |
| 2023 | 402 | 0.9290 | 0.8458 | 0.001203 |

Both symbols also passed with nonzero events and true positives:

- `000688.SH`: precision `0.9661`, recall `0.9097`, FPR `0.000723`;
- `000852.SH`: precision `0.9757`, recall `0.9392`, FPR `0.000465`.

Source-state decomposition at E-15s:

- from `NORMAL`: 876 true entries; precision `0.9636`, recall `0.9064`;
- from `RECOVERING`: 485 true entries; precision `0.9830`, recall `0.9546`.

## Fixed evidence-accumulation curve

The other checkpoints were fixed diagnostics and were not eligible to replace E-15s.

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

Among events detected at any checkpoint, **96.75%** remain `UNSAFE` at every later fixed checkpoint after first detection. There are `98` true events that are not yet signalled at E-15s but become signalled at E-6s or E-3s.

## Interpretation

The result supports a causal evidence-accumulation view rather than a first-shock forecasting claim. Roughly 58% of eventual switch-ons already satisfy the frozen `UNSAFE` rule one minute before 5m close; the fraction rises monotonically to about 92% at E-15s and 99.6% at E-3s.

The E-15s checkpoint is therefore supported as a high-precision/high-recall **switch-on measurement** within the frozen V9 state machine. This complements, rather than replaces, V17: V18 addresses entering `UNSAFE`; V16/V17 address recovery-state probabilities after risk is active.

## Decision

`development_supported=true`.

`validation_eligible_but_not_authorized=true`.

No reusable Validation was started. A later Validation requires separate authorization and must preserve the exact target, cohort boundary, V9 thresholds, E-15s primary checkpoint, and acceptance logic.

`validation_queried=false`  
`blackbox_queried=false`  
`pnl_computed=false`  
`trading_rule_created=false`  
`production_authority=false`
