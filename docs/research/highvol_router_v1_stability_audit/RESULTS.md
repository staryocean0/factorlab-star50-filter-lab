# HighVol Router V1 stability audit — results

Status: **PRIMARY-COST EDGE POSITIVE WITH MATERIAL STABILITY FRAGILITY**.

This is a diagnostic qualification of the already frozen HighVol Router V1. It does not alter the prior reusable Validation PASS, creates no new candidate, changes no parameter or routing rule, and grants no production authority. BlackBox-V1 was not queried.

## Execution receipt

Dedicated run: `34346275786` — success.
Job: `102448499259`.
Head commit: `ba17c5ee5fdb05e60fb6790c80207f3d4072ffe7`.
Artifact ID: `10101828676`.
Artifact ZIP SHA256: `730af4ad3667698ae106b1c49795ae664b07558de96ff73ab1a290ac46acca5a`.

Governance, physical data-boundary guard, frozen-audit tests and exact trade-identity guard all passed. The audit reproduced the same 104 Development and 129 Validation frozen trades.

## Cost stress

Mean net bp per trade after the stated per-leg cost:

| period | 0.5 bp/leg | 1.0 bp/leg | 1.5 bp/leg | 2.0 bp/leg | one-way BE |
|---|---:|---:|---:|---:|---:|
| Development | +1.737746 | +0.737746 | -0.262254 | -1.262254 | 1.368873 |
| Validation | +1.546255 | +0.546255 | **-0.453745** | -1.453745 | **1.273128** |

The primary 1 bp/leg result is positive, but the economic margin is narrow: the pooled Validation break-even is only 1.2731 bp per leg, and the preset 1.5 bp/leg stress is negative.

## Day-block bootstrap

Resampling unit was the complete trading day, including zero-trade days; 10,000 draws; seed `20260909`.

| period | bootstrap mean net bp/trade | 95% percentile interval | P(mean net > 0) |
|---|---:|---:|---:|
| Development | +0.731730 | [-0.970458, +2.535181] | 79.72% |
| Validation | +0.553690 | **[-1.985521, +3.058996]** | **67.04%** |

Both intervals cross zero. The Validation evidence therefore supports positive realized pooled mean at the primary cost, but not a tight claim that the conditional expected net return is reliably positive under day-level resampling.

## Positive-day concentration sensitivity

At 1 bp/leg, remove the strongest positive daily PnL days without changing any trade rule:

| period | removed top days | remaining trades | remaining total net bp | remaining mean net bp/trade |
|---|---:|---:|---:|---:|
| Development | 1 | 103 | +39.162627 | +0.380220 |
| Development | 3 | 101 | -21.221470 | -0.210114 |
| Development | 5 | 99 | -62.639122 | -0.632718 |
| Validation | 1 | 128 | +30.664559 | +0.239567 |
| Validation | 3 | 126 | **-35.699886** | **-0.283332** |
| Validation | 5 | 123 | **-92.370610** | **-0.750981** |

Thus the realized edge is materially dependent on a small number of strong days in both pools. This is a stability warning, not a post-hoc instruction to censor those days or add a regime filter.

## Leave-one-year-out

At 1 bp/leg, every leave-one-year-out pooled estimate remains positive:

### Development

- exclude 2021: +0.724847 bp/trade;
- exclude 2022: +0.559907;
- exclude 2023: +0.941369.

### Validation

- exclude 2024: +0.812310 bp/trade;
- exclude 2025: **+0.120677**;
- exclude 2026: +0.687904.

So the weakness is not simply a single-calendar-year artifact. However, removing 2025 leaves only a very small positive Validation mean, showing that 2025 contributes materially to the pooled margin.

## Annual primary-cost reminder

Validation at 1 bp/leg:

- 2024: 58 trades, +0.220568 bp/trade;
- 2025: 49 trades, +1.241076;
- 2026 through 2026-08-21: 22 trades, -0.142671.

## Pre-fixed fragility flags

All four preset fragility flags triggered:

1. Validation day-block bootstrap interval crosses zero;
2. Validation mean net is non-positive at 1.5 bp/leg;
3. Validation mean net is non-positive after removing the top 5 positive days (indeed after top 3);
4. 2026 Validation slice is non-positive.

Diagnostic conclusion: `PRIMARY_COST_EDGE_POSITIVE_WITH_MATERIAL_STABILITY_FRAGILITY`.

## Authority and next interpretation

The prior Router V1 reusable Validation PASS remains exactly what it was: a research candidate that passed the frozen acceptance gates at 1 bp/leg. This audit prevents upgrading that PASS into a production-quality or broadly stable edge claim.

Do **not** rescue the result by changing tail thresholds, HighVol definition, hold, confirmation, stop, sizing, or by censoring strong/weak dates. Router V1 remains frozen. Any materially new payoff hypothesis must start in Development as a new identity.

`production_authority=false`. BlackBox query count remains zero.
