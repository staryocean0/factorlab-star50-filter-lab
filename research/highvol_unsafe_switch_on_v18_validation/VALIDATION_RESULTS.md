# V18 causal UNSAFE switch-on — reusable Validation result

## Decision

**PASS — `full_validation_supported=true`.**

The exact frozen V18 `E-15s` switch-on measurement validated on the repository's existing 2024–2025 3s coverage without refitting, threshold/feature search, lead-time selection, subgroup selection, or target changes.

Frozen primary rule:

`E-15s switch_on_signal = (frozen V9 partial_state == UNSAFE)`

This remains an intrabar causal risk-state measurement, not a pre-evidence first-shock forecast and not a trading rule.

## Execution authority

- branch: `research/highvol-unsafe-switch-on-v18-validation-20260911`
- execution commit: `35af3b86082791155ae1ba3bf96345c492214d86`
- run: `34607566312`
- job: `103289664712`
- artifact: `10265993683`
- artifact SHA256: `55a9a3873ce7fb2514183736a5eadb9ce5dfe7e85f2c77162e5f6aa5992398e6`
- frozen V18 runner blob: `62c207badff1c3e37cbb1a8e17ef89feeea611d8`
- frozen V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`

## Validation boundary

- scored years: 2024 and 2025 only
- queried 3s years: 2024 and 2025 only
- no 2026 3s file was checked out or queried
- BlackBox was not queried
- `production_authority=false`

The unchanged V9 causal reference boundary excluded 485 rows per symbol lacking same-session previous-close/background/prior-window support; no overnight repair was introduced.

## Primary E-15s result

Across 43,793 evaluable candidate bars:

- true new `UNSAFE` switch-ons: `810`
- checkpoint coverage: `1.000000`
- signal rows: `757`
- TP / FP / FN / TN: `720 / 37 / 90 / 42946`
- precision: **`0.9511228534`**
- recall: **`0.8888888889`**
- false-positive rate: **`0.0008608054`**
- specificity: `0.9991391946`

All pooled preregistered thresholds passed.

## Annual stability

| Year | candidates | true switch-ons | precision | recall | FPR |
|---|---:|---:|---:|---:|---:|
| 2024 | 21,816 | 418 | 0.951899 | 0.899522 | 0.000888 |
| 2025 | 21,977 | 392 | 0.950276 | 0.877551 | 0.000834 |

Both annual slices passed the frozen minimum precision/recall and maximum FPR gates.

## Symbol stability

| Symbol | candidates | true switch-ons | precision | recall | FPR |
|---|---:|---:|---:|---:|---:|
| `000688.SH` | 21,875 | 412 | 0.950131 | 0.878641 | 0.000885 |
| `000852.SH` | 21,918 | 398 | 0.952128 | 0.899497 | 0.000836 |

Both symbols have nonzero true events and nonzero E-15s true positives.

## Source-state decomposition

- `NORMAL -> UNSAFE`: 550 true events; E-15s precision `0.936170`, recall `0.880000`, FPR `0.000836`.
- `RECOVERING -> UNSAFE`: 260 true events; E-15s precision `0.983333`, recall `0.907692`, FPR `0.001133`.

Final switch-on pathways:

- shock entry: `612`
- recovery re-escalation: `198`

No pathway-specific rule was fitted.

## Frozen evidence-accumulation curve

The non-primary checkpoints remain diagnostics only:

| checkpoint | recall |
|---|---:|
| E-60s | 0.587654 |
| E-30s | 0.764198 |
| **E-15s** | **0.888889** |
| E-6s | 0.959259 |
| E-3s | 0.996296 |

Earliest detection counts among the 810 true switch-ons:

- E-60s: 476
- E-30s: 171
- E-15s: 99
- E-6s: 46
- E-3s: 15
- undetected by E-3s: 3

`87` events first formed after E-15s. Among events detected at any frozen checkpoint, the signal remained UNSAFE at all later checkpoints at rate `0.936803`.

This curve supports the original interpretation: V18 measures intrabar accumulation of causal risk evidence; it does not claim that all later-forming switch-ons were knowable at E-15s.

## Governance conclusion

Every preregistered acceptance item passed. Therefore the supported entry-side object is now:

> At the frozen E-15s checkpoint, the unchanged V9 provisional state can be used as a validated causal `UNSAFE` switch-on annotation for 2024–2025 available 3s coverage.

No 2026 realtime authority is claimed. No PnL, payoff, routing, sizing, leverage, or trading rule was computed.
