# FactorLab STAR50 Filter Lab

## Current authority: bottom-layer K-line risk-state research

This repository now has one bounded role: **causal K-line volatility / shock / risk-state research for STAR50 (`000688.SH`) with bounded CSI1000 (`000852.SH`) comparison**.

Start at [`CONTINUE_HERE.md`](CONTINUE_HERE.md) and follow the three-pool governance in `docs/governance/DATA_USAGE_POLICY_V2.md`.

Current research objects include:

- volatility level and volatility expansion/contraction;
- isolated shock vs clustered shock;
- `Unsafe / Recovering / HighVol` annotations;
- causal switch-on / persistence / recovery logic for risk state;
- cross-scale 3s/1m/5m risk attributes and failure cases.

## Explicit bucket boundary

This repository does **not** currently own:

- generic parent-structure recognition into `Range / UpTrend / DownTrend` — that belongs to `factorlab-two-wave-strategy-lab`;
- concrete reversal / mean-reversion strategies such as R1/R2 — those belong to `factorlab-trend-reversion-regime-lab`;
- new payoff routers, directional continuation/sign-flip strategies, holding-period optimization, stops/targets, sizing or leverage research.

Historical HighVol Router V1, V10-V17 sign-flip and other payoff experiments remain in Git as evidence but are no longer current bucket authority. See [`docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`](docs/governance/BUCKET_SCOPE_REPAIR_20260909.md). R1/R2 were already migrated out correctly.

## Data governance

- Development: 2021-01-01 through 2023-12-31.
- Reusable Validation: 2024-01-01 through 2026-08-21 under the existing V2 policy.
- BlackBox-V1: protected post-2026-08-21 period under its frozen aggregate-query contract.

Historical payoff reports keep their original evidence status; this scope repair does not upgrade them or erase them.

`production_authority=false`. No trading, options, routing or production authority is implied by this workspace.

```bash
python -m pip install -e .
python scripts/validate_data_usage_policy.py
python -m pytest -q
```
