# HighVol realtime horizon-adaptive recovery V17 — Development results

Status: **PASS — FREEZE EXACT E-15s TRANSFER AND RUN ONE REUSABLE 2024-2025 VALIDATION**

V17 transferred the already-frozen V16 15/30/60m recovery surface to the already-frozen V9/V10 `E-15s` realtime state measurement. No probability, threshold, projection, lead time, horizon, payoff, or trading variable was fitted or selected.

## Execution authority

- branch: `research/highvol-realtime-horizon-adaptive-v17-20260911`
- execution commit: `5ae8d6adab6c4afb617ed14ae44327d722e3db49`
- run: `34603682244`
- job: `103276864733`
- artifact: `10265262086`
- artifact SHA256: `759eda3d30900742bedd9494fef9c64ed91af66068892aceaa01e610a684101c`
- frozen V16 surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`
- frozen V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`
- frozen V11 cohort builder blob: `713f0dcc41e7f32f75934fc7709a406ff71579e6`

## Frozen Development boundary

- 5m reference/warm-up: 2020-2023 only;
- scored Development: 2021-2023;
- 3s inputs: 2021-2023 only;
- symbols: `000688.SH`, `000852.SH`;
- exact V11 common multi-horizon cohort: **7,327 rows**;
- 2024+, reusable Validation, and BlackBox were physically excluded.

V11 and V9 final 5m states aligned exactly on all 7,327 cohort rows.

## Pooled E-15s transfer

- reference rows: `7327`;
- realtime-scored rows: `7310`;
- coverage: **0.9976798144**;
- exact realtime/final state agreement on scored rows: **0.9954856361**;
- unscorable fresh partial shocks: `9`;
- unscorable provisional NORMAL rows: `8`;
- missing 3s checkpoints: `0`;
- missing reference windows: `0`.

| Horizon | Probability MAE vs frozen V16 | Exact probability-cell agreement | Brier degradation | LogLoss degradation |
|---|---:|---:|---:|---:|
| 15m | 0.000381438 | 0.995486 | +0.000042377 | +0.000175181 |
| 30m | 0.000406241 | 0.995486 | +0.000099892 | +0.000327652 |
| 60m | **0.000000000** | **1.000000** | **0.000000000** | **0.000000000** |

All 7,310 emitted realtime rows satisfy `p15 <= p30 <= p60`. The realtime 60m probability is exactly the frozen V16 age-only anchor on every scored row (`max_abs_diff=0.0`).

## Annual guards

Coverage:

- 2021: `1.0000000`;
- 2022: `0.9985267`;
- 2023: `0.9939139`.

15m Brier degradation:

- 2021: `0.0`;
- 2022: `+0.0001745725`;
- 2023: `-0.0000770076`.

30m Brier degradation:

- 2021: `0.0`;
- 2022: `+0.0000092251`;
- 2023: `+0.0003321705`.

All preregistered Development gates passed.

## Decision

`validation_eligible=true`.

The exact V17 `E-15s` transfer is frozen. The next and only authorized decisive action is one reusable Validation using the repository's existing **2024-2025 3s coverage**. The 2026 3s contract does not exist and is not inferred or synthesized.

No Validation data was queried in this Development run. `blackbox_queried=false`; `pnl_computed=false`; `trading_rule_created=false`; `production_authority=false`.
