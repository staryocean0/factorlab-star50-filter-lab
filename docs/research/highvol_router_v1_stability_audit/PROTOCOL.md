# HighVol Router V1 stability audit protocol

Role: diagnostic-only robustness audit of the already frozen HighVol Router V1.

This audit cannot change the router, candidate selector, entry, hold, exit, thresholds, routing table, position concurrency rule, or acceptance decision. It creates no new candidate and does not query BlackBox-V1.

## Frozen object

Use the exact Router V1 mechanics already frozen in `docs/research/highvol_router_v1_validation/FROZEN_ROUTER_V1.json` and implemented by `docs/research/highvol_router_v1_dev/run_router_dev.py`.

Routes remain:

- `000852.SH`: frozen active long 3-minute module;
- `000688.SH`: `NO_TRADE`;
- all other HighVol contexts: `NO_TRADE`.

## Data roles

- Development diagnosis: 2021-01-01 through 2023-12-31.
- Reusable Validation diagnosis: 2024-01-01 through 2026-08-21.
- 2020 may be loaded only as warm-up for state construction.
- BlackBox-V1: forbidden / not queried.

## Pre-fixed diagnostics

For Development and Validation separately:

1. Exact frozen trade count and primary 1 bp/leg economics.
2. Cost stress with per-leg costs exactly `{0.5, 1.0, 1.5, 2.0}` bp.
3. Leave-one-year-out pooled mean net at 1 bp/leg.
4. Daily-block bootstrap of mean net per trade at 1 bp/leg:
   - resampling unit: complete trading day, including zero-trade days;
   - draws: 10,000;
   - RNG seed: `20260909`;
   - report mean, 2.5%/97.5% percentile interval and probability mean net > 0.
5. Positive-day concentration sensitivity at 1 bp/leg:
   - remove the top 1, top 3 and top 5 positive daily PnL days;
   - report remaining trade count, total net and mean net/trade.

These are diagnostics, not new acceptance gates. No threshold or cost level may be chosen after seeing results and then relabelled as frozen Router V1.

## Interpretation rule

The audit may describe the edge as robust or fragile only with respect to these pre-fixed diagnostics. A negative bootstrap lower bound, high cost sensitivity, or top-day dependence does not retroactively change the prior reusable Validation PASS; it limits the strength of any production/stability claim.

`production_authority=false`. No live execution, ETF/options mapping, sizing, leverage, or BlackBox query is authorized by this audit.
