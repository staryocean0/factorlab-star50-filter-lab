# HighVol realtime detection V8 — 2024-2025 Validation

## Decision

The frozen V8 3-second partial-bar detector **passes the physically available 2024-2025 Validation subset** and is retained as a validated realtime risk-state detector component.

This is risk-state measurement only. It does not create PnL, payoff, routing, sizing, or production authority.

It is **not** complete Validation through 2026-08-21 because the repository 3-second contract ends at 2025-12-31. No 2026 3-second Validation data was queried. BlackBox was not queried.

## Frozen authority

- Development source commit: `07bfa63018fe4d1a1afa4f108a14d9be5ae86777`
- Development run: `34426934097`
- Development artifact: `10133063809`
- Validation execution commit: `98a2c2ace8bc070506f2d6f8ea8b949f559104cd`
- Validation run: `34438385207`
- Validation artifact: `10137043121`
- Validation artifact ZIP SHA256: `db8f97e7fec5bfc073fa350b282f0746aab243e0568c2eef473c868e9f4aefbd`

The state machine, thresholds, checkpoint set, and causal observation-selection rule were unchanged from Development. No threshold search occurred.

## Primary checkpoint: E-3s

Pooled 2024-2025 across STAR50 and CSI1000:

| metric | result |
|---|---:|
| usable coverage | 100.0000% |
| eligible reference bars | 45,590 |
| exact 3-state accuracy | 99.9890% |
| UNSAFE precision | 99.9445% |
| UNSAFE recall | 99.7785% |
| RECOVERING precision | 99.9475% |
| RECOVERING recall | 99.9738% |
| shock precision | 100.0000% |
| shock recall | 99.7010% |
| UNSAFE-onset precision | 99.8762% |
| UNSAFE-onset recall | 99.6296% |

Annual UNSAFE metrics at E-3s:

- 2024: coverage `1.0`, precision `0.9989328`, recall `0.9978678`;
- 2025: coverage `1.0`, precision `1.0`, recall `0.9976959`.

## Causal lead curve

Pooled UNSAFE recognition versus the final completed 5-minute state:

| lead before close | precision | recall |
|---|---:|---:|
| 60s | 90.1203% | 78.7929% |
| 30s | 95.1555% | 88.0952% |
| 15s | 97.0387% | 94.3522% |
| 6s | 98.6041% | 97.7852% |
| 3s | 99.9445% | 99.7785% |

This resolves the V7 one-minute measurement gap without changing the validated 5-minute risk-state definition. It does **not** establish pre-shock forecasting; it establishes causal same-bar recognition immediately before the 5-minute reference bar completes.

## Governance

- `available_2024_2025_validation_subset_pass=true`
- `complete_validation_pass=false`
- `validation_2026_queried=false`
- `blackbox_queried=false`
- `candidate_nominated=false`
- `production_authority=false`
