# HighVol Router V1 — reusable Validation result

Status: **VALIDATION-SUPPORTED / RESEARCH-ONLY**.

This result does **not** grant production authority. `production_authority=false`. BlackBox-V1 was not queried.

## Frozen router identity

Candidate ID: `highvol_router_v1_csi1000_active_star50_no_trade`.

- CSI1000 (`000852.SH`): the only active HighVol trading module.
- STAR50 (`000688.SH`): `NO_TRADE`.
- Other HighVol contexts: `NO_TRADE`.
- CSI1000 mechanics are unchanged from the previously frozen candidate:
  - continuous `NormalVol -> HighVol` onset;
  - 5m RMS / max(preceding non-overlapping 30m RMS, 1 bp) >= 1.5;
  - current 5m net > 0;
  - preceding non-overlapping 30m net > 0;
  - `tail2_share >= 0.60`;
  - `tail1_share < 0.60`;
  - long next-minute open;
  - hold exactly 3 minutes;
  - same half-session, complete valid path, non-overlap;
  - primary friction = 1 bp per leg.

Frozen router receipt blob: `ea9b00736369f75b8dd5df2661e54afd24516e3b`.
Frozen Development runner blob: `52aa0db330b3489c4196b6e718f8c7f6f8628d13`.
Frozen Development code commit: `33b2654e31ea8ac09711aeb77248ddfe68d9dea5`.

## Development execution audit

Dedicated Development run: `34300072928` (success).
Artifact ID: `10084593028`.
Artifact ZIP SHA256: `ff73b10e04a429d68cf7b383f138699137f3d9cba83fb541dd49567376223145`.

The workflow physically checked out only CSI1000 2020 warm-up plus 2021/2022/2023 minute parquet inputs. Governance and physical-boundary guards passed.

The router exactly reproduced the frozen candidate:

| year | trades | mean gross bp/trade | mean net @1bp/leg | one-way BE bp |
|---|---:|---:|---:|---:|
| 2021 | 37 | 2.761102 | 0.761102 | 1.380551 |
| 2022 | 31 | 3.156527 | 1.156527 | 1.578264 |
| 2023 | 36 | 2.353123 | 0.353123 | 1.176562 |
| pooled | 104 | 2.737746 | 0.737746 | 1.368873 |

Additional portfolio/mechanical audit:

- qualifying before non-overlap: 104;
- accepted trades: 104;
- overlap rejected: 0;
- maximum concurrent positions: 1;
- STAR50 route trades: 0;
- pooled total net: +76.725554 bp;
- pooled max drawdown on the zero-position daily ledger: 44.210856 bp;
- pooled daily Sharpe proxy: 0.487938.

The Development evidence is profitable but payoff remains concentrated in strong days. This concentration is descriptive evidence, not an added threshold or rescue rule.

## Reusable Validation replay

Validation period: 2024-01-01 through 2026-08-21. This is reusable Validation evidence and **not fresh OOS**.

The 2026 parquet was restored from the previously used Validation evidence branch and hash-checked to blob `8de5cd3caab99dbacae229a2c87f15c4ff2f8558`; its last trading day was guarded at `2026-08-21` before strategy execution.

First Validation run `34300476501` failed only while serializing a non-finite diagnostic field (`NaN`) into strict JSON. Governance, data-boundary and frozen-identity tests had already passed. The repair only maps non-finite descriptive diagnostics to JSON `null`; it did not alter candidate mechanics, route identity, acceptance criteria, or data.

Decisive Validation run: `34300569936` (success).
Head commit: `c8994b251323662abb65fe73d3d80123a5502a5e`.
Artifact ID: `10084769189`.
Artifact ZIP SHA256: `4e7d1aea626936c1170ee26d4f9787ff26edd66236241c62be5ac90807a91d71`.

| year | trades | mean gross bp/trade | mean net @1bp/leg | one-way BE bp | total net bp |
|---|---:|---:|---:|---:|---:|
| 2024 | 58 | 2.220568 | +0.220568 | 1.110284 | +12.792946 |
| 2025 | 49 | 3.241076 | +1.241076 | 1.620538 | +60.812747 |
| 2026 through 08-21 | 22 | 1.857329 | -0.142671 | 0.928664 | -3.138765 |
| pooled | 129 | 2.546255 | **+0.546255** | **1.273128** | **+70.466928** |

Portfolio/mechanical Validation audit:

- raw positive HighVol onsets: 1117;
- frozen qualifying signals: 129;
- accepted non-overlap trades: 129;
- overlap rejected: 0;
- maximum concurrent positions: 1;
- STAR50 route trades: 0;
- positive annual slices: 2 of 3;
- pooled hit rate: 58.91%;
- pooled max drawdown on the zero-position daily ledger: 158.587373 bp;
- pooled daily Sharpe proxy: 0.263283.

## Pre-registered acceptance

All gates passed:

1. pooled completed trades >= 30: PASS (129);
2. pooled mean net after 1 bp/leg > 0: PASS (+0.546255 bp/trade);
3. at least 2 of 3 annual slices positive: PASS (2024, 2025);
4. pooled one-way break-even > 1 bp: PASS (1.273128 bp);
5. STAR50 route trade count = 0: PASS;
6. non-overlap and max concurrency <= 1: PASS;
7. candidate parameters unchanged: PASS.

Therefore HighVol Router V1 is **Validation-supported as a research candidate**.

## Interpretation and authority

This is evidence for a sparse router, not for a generic HighVol directional strategy: HighVol only opens the CSI1000 frozen continuation module; STAR50 and all unsupported HighVol contexts remain `NO_TRADE`.

The 2026 slice is slightly negative and pooled payoff remains dependent on episodic positive days. These facts prevent upgrading the result into a stronger stability claim. They do not invalidate the pre-registered reusable Validation acceptance, which passed exactly as frozen.

`production_authority=false`. No live trading, ETF/options execution, leverage, sizing, or BlackBox authority follows from this result. BlackBox query count remains zero.
