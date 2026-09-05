# Continue here

1. Read `docs/user/cloud_execution_prompt.md` and `docs/governance/data_usage_declaration.json`.
2. Validate `python scripts/validate_theme_package.py`.
3. Current baseline: 5m+0, 1-hour 1st-order Butterworth lowpass, vol-scaled
   hysteresis k=1. Remaining problem is working-band saw vs slower drift.
4. Do not use 2026 to pick parameters.
5. First takeover drawdown study: `docs/research/drawdown_conditions/report.md`.
   Baseline exactly reproduced (sigma population std, ddof=0). Fixed slow-conflict
   half-exposure diagnostic reduces zero-cost primary-view MDD 14.32% to10.68%,
   but is not promoted: available_at gap, offset4 and2023/2025 counterexamples.
   All five reviewed sessions are sealed; do not overwrite or retune them.
6. Validate `python scripts/validate_drawdown_study.py`. Resolve data availability
   and tradable execution before any stronger causal or production claim.
