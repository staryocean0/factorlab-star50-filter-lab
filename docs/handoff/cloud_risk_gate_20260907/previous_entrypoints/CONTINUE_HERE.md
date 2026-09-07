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
7. Second round: `docs/research/execution_counterexamples/report.md`.
   All five annual sessions are sealed. Do not overwrite them or retune rules.
   One-minute delayed, 3bp primary account: baseline CAGR16.80%/MDD26.10%;
   slow-conflict half17.74%/24.56%; matched constant13.78%/22.22%.
   Slow-conflict MDD advantage beyond constant exposure is not robust to delay.
   2025 zero-cost delayed slow-conflict MDD14.15% exceeds baseline12.84%.
8. Exact minute/coarse endpoint bridge handles six-minute first-session offset
   bars and first-observed quotes following synthetic missing-minute repair.
   Source publication semantics and tradable execution remain unresolved.
   Validate `python scripts/finalize_execution_audit.py --validate-only`.
   The current scientific status remains `infrastructure or measurement gap`.
