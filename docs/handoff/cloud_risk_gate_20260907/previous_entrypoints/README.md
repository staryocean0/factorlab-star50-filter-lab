# FactorLab STAR50 Filter Lab

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
