# FactorLab STAR50 Filter Lab

## Current: STAR50 / CSI1000 cross-scale Kline risk research

**Start at [the 2026-09-07 handoff](docs/handoff/cloud_risk_gate_20260907/HANDOFF.md).**
Includes two-index bounded 3s/1m/5m inputs, current volatility/tail evidence,
the owner's research manuscript and all 15 identified reference works.
Local FactorLab/DataHub remain authoritative storage; cloud is a private research
venue. No new trading, options, production, or 2026 research is authorized.

```bash
python -m pip install -e .
python scripts/validate_cloud_risk_gate_package.py
python -m pytest -q
```

The original package description below is retained as history, not current scope.

Private, bounded cloud workspace for one task: causal filter timing on
CSI STAR50 (`000688.SH`). It is **not** the two-wave theme, overnight-open
theme, or REAKA multifactor lab. Do not merge those repositories.

```bash
python -m pip install -e .
python scripts/validate_theme_package.py
pytest -q
```

Then follow [`docs/user/cloud_execution_prompt.md`](docs/user/cloud_execution_prompt.md).

Production authority is false. 2026 is consumed repeat-audit, not fresh OOS.
