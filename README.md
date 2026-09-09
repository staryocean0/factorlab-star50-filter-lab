# FactorLab STAR50 Filter Lab

## Current: STAR50 / CSI1000 cross-scale Kline risk research

**Start at [`CONTINUE_HERE.md`](CONTINUE_HERE.md)** and follow the three-pool governance in `docs/governance/DATA_USAGE_POLICY_V2.md`.

Current data roles are:

- Development: 2021-01-01 through 2023-12-31.
- Reusable Validation: 2024-01-01 through 2026-08-21, only after a Development candidate is frozen and without fitting the candidate-under-test on those rows.
- BlackBox-V1: the first 60 complete trading days strictly after 2026-08-21, once available and manifest-frozen. It remains unqueried.

The V10–V17 HighVol sign-flip program is closed with **no empirical candidate** after three Development-passed frozen formulations (V15/V16/V17) were rejected on Validation. See [`docs/research/star50_highvol_sign_flip_closeout_20260909.md`](docs/research/star50_highvol_sign_flip_closeout_20260909.md).

`production_authority=false`. No trading, options, or production authority is implied by this research workspace.

```bash
python -m pip install -e .
python scripts/validate_data_usage_policy.py
python -m pytest -q
```

The 2026 Validation rows through 2026-08-21 are not fresh OOS and must not be treated as Development. Rows strictly after the cutoff belong to the protected BlackBox regime and must not be inspected outside its frozen protocol.

The original package description below is retained as history, not current scope.

Private, bounded cloud workspace for causal filter timing and market-state research on CSI STAR50 (`000688.SH`) with bounded CSI1000 (`000852.SH`) cross-state work. It is **not** the two-wave theme, overnight-open theme, or REAKA multifactor lab. Do not merge those repositories.

Then follow [`docs/user/cloud_execution_prompt.md`](docs/user/cloud_execution_prompt.md) only where it does not conflict with the current mandatory entry and V2 governance.
