# HighVol realtime detection V8 — Validation results

## Decision

The frozen 3-second detector **passes the physically available 2024-2025 Validation subset**. It is therefore frozen as a validated 2024-2025 realtime risk-state detector component.

This is **not** a complete 2024-2026-08-21 Validation result because repository 3-second data ends at 2025-12-31. No 2026 3-second Validation data was queried. BlackBox was not queried. Production authority remains false.

## Authority and evidence

- Development source commit: `07bfa63018fe4d1a1afa4f108a14d9be5ae86777`
- Development run: `34426934097`
- Development artifact: `10133063809`
- Validation execution commit: `98a2c2ace8bc070506f2d6f8ea8b949f559104cd`
- Validation run: `34438385207`
- Validation job: `102748118248`
- Validation artifact: `10137043121`
- Validation artifact ZIP SHA256: `db8f97e7fec5bfc073fa350b282f0746aab243e0568c2eef473c868e9f4aefbd`

All governance guards, physical-boundary guards, and frozen-contract tests passed. State thresholds and checkpoint rules were unchanged. No threshold search, PnL, payoff, trading rule, or BlackBox access occurred.

## Primary checkpoint: E-3s

Pooled 2024-2025, both symbols:

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

UNSAFE confusion counts: true=1,806, predicted=1,803, TP=1,802, FP=1, FN=4.

Annual UNSAFE stability at E-3s:

| year | coverage | precision | recall |
|---|---:|---:|---:|
| 2024 | 100.0000% | 99.8933% | 99.7868% |
| 2025 | 100.0000% | 100.0000% | 99.7696% |

The frozen acceptance rule therefore passes for the available Validation subset.

## Causal lead curve

Pooled UNSAFE recognition versus final completed 5-minute state:

| checkpoint before 5m close | precision | recall |
|---|---:|---:|
| 60s | 90.1203% | 78.7929% |
| 30s | 95.1555% | 88.0952% |
| 15s | 97.0387% | 94.3522% |
| 6s | 98.6041% | 97.7852% |
| 3s | 99.9445% | 99.7785% |

For 810 true final UNSAFE onsets, cumulative recognition was 58.77% by 60s, 79.88% by 30s, 92.10% by 15s, 97.78% by 6s, and 99.63% by 3s.

## Interpretation

The earlier 1-minute study failed because newly forming Unsafe/shock episodes often materialize during the last minute of a 5-minute bar. The 3-second study resolves that measurement gap without changing the validated 5-minute state definition. This does not establish pre-shock forecasting; it establishes causal same-bar recognition immediately before the reference bar completes.

The primary detector remains the preregistered **E-3s** checkpoint. Although E-15s and E-6s are strong, Validation results must not be used to replace the frozen checkpoint post hoc.

## Governance state

- `available_2024_2025_validation_subset_pass=true`
- `complete_validation_pass=false` because 2026 3s data was not available/queried
- `validation_2026_queried=false`
- `blackbox_queried=false`
- `candidate_nominated=false`
- `production_authority=false`
