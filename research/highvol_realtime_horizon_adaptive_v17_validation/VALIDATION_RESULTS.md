# HighVol realtime horizon-adaptive recovery V17 — reusable Validation results

Status: **PASS — REALTIME E-15s MULTI-HORIZON RISK ANNOTATION SUPPORTED ON AVAILABLE 2024-2025 3s COVERAGE**

This is the single reusable Validation authorized by the frozen V17 Development protocol. The exact frozen V16 15/30/60m recovery surface was transferred at the preregistered `E-15s` checkpoint using the exact frozen V9 realtime state measurement. No probability, threshold, projection, lead time, horizon, payoff, or trading variable was fitted or selected after inspecting Validation.

## Execution authority

- Validation branch: `research/highvol-realtime-horizon-adaptive-v17-validation-20260911`
- execution commit: `a35a9f496c7772bf9a81a7b85b0cd0b3d6fccfe2`
- run: `34604089926`
- job: `103278189791`
- artifact: `10265472702`
- artifact SHA256: `65783daff1ca83217ad8159b52e2c4f9d6c79f8195a11aa4b1c4af80aa2d1714`
- frozen V17 transfer blob: `5aca30ff398f73173a5424aa14b535bd461df5b4`
- frozen V17 runner blob: `397d80037806ba11cadf7f77717d36d55fbafc91`
- frozen V16 surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`
- frozen V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`
- frozen V11 cohort builder blob: `713f0dcc41e7f32f75934fc7709a406ff71579e6`

## Physical Validation boundary

- 5m reference/warm-up: 2020-2025;
- scored reusable Validation: 2024-01-01 through 2025-12-31;
- 3s inputs queried: **2024 and 2025 only**;
- symbols: `000688.SH`, `000852.SH`;
- 2026 3s inputs were not queried and were physically absent;
- BlackBox was not queried.

Common frozen Validation cohort: **4,540 rows**:

- 2024: `2,339`;
- 2025: `2,201`.

V11 and V9 final 5m states aligned exactly on all 4,540 cohort rows.

## Pooled E-15s transfer

- reference rows: `4540`;
- realtime-scored rows: `4516`;
- realtime coverage: **0.9947136564**;
- exact provisional/final state agreement on scored rows: **0.9918069088**;
- fresh partial-shock unscorable rows: `8`;
- provisional-NORMAL unscorable rows: `16`;
- missing 3s checkpoint rows: `0`;
- missing reference-window rows: `0`.

| Horizon | Probability MAE vs frozen final-5m V16 | Exact probability-cell agreement | Brier degradation | LogLoss degradation |
|---|---:|---:|---:|---:|
| 15m | **0.000824551** | 0.991807 | **-0.000006965** | +0.000006648 |
| 30m | **0.000637991** | 0.991807 | **+0.000171425** | +0.000543736 |
| 60m | **0.000000000** | **1.000000** | **0.000000000** | **0.000000000** |

All 4,516 emitted realtime curves satisfy `p15 <= p30 <= p60`. The 60m probability remains exactly the frozen V16 age-only anchor on every scored row (`max_abs_diff=0.0`).

## Annual guards

2024:

- coverage: `0.9961522018`;
- 15m Brier degradation: `+0.0001094188`;
- 30m Brier degradation: `+0.0003170053`.

2025:

- coverage: `0.9931849159`;
- 15m Brier degradation: `-0.0001310164`;
- 30m Brier degradation: `+0.0000162543`.

Both years pass the frozen coverage and Brier-degradation gates.

## Symbol coverage

- `000688.SH`: coverage `0.9939733104`;
- `000852.SH`: coverage `0.9954894001`.

## Decision

`full_validation_supported=true`.

The validated realtime object is therefore:

- at exactly `E-15s`, use the frozen V9 partial state measurement;
- 15m recovery probability = frozen V16 `state + recent-shock age` cell using the realtime partial state;
- 30m recovery probability = frozen V16 `state + recent-shock age` cell using the realtime partial state;
- 60m recovery probability = frozen V16 recent-shock-age-only anchor;
- fresh partial shock, provisional `NORMAL`, missing checkpoint, or missing reference window => realtime annotation unavailable.

This authority is limited to the available **2024-2025 3s Validation coverage**. It does not imply 2026 realtime support because the repository has no authorized 2026 3s physical contract. It does not authorize earlier lead times, BlackBox access, payoff optimization, or production use.

`queried_2026_3s=false`; `blackbox_queried=false`; `pnl_computed=false`; `trading_rule_created=false`; `production_authority=false`.
