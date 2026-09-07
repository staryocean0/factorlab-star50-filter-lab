# Continue here

**Current entry supersedes the numbered historical steps below.**

Read first:
1. `docs/research/post_shock_recovery_v1/STABLE_STATE_SPEC.md`
2. `docs/research/post_shock_recovery_2026/RESULTS.md`
3. `docs/ops/data_requirements_star50_risk_research.md`
4. `docs/handoff/cloud_risk_gate_20260907/HANDOFF.md`

Current research line is now frozen as:

`observed first shock -> Unsafe -> continuous Recovering score`

Primary Recovering score: trailing completed-5m RMS divided by the frozen pre-shock `sigma_pre`.

`Clean` is **not** an online validated transition. Do not re-open release-rule/threshold/model tuning on the already-consumed 2024-2025 data or the 2026-01-05..2026-08-21 validation snapshot. Re-open Clean research only with genuinely new independent events after the current same-semantics cutoff (`2026-08-21`) or a new preregistered materially different information layer.

The core state line needs native 1m STAR50/CSI1000 data plus immutable manifest/quality receipts. 3s observations remain important for path/measurement research but are not required to compute the stable recovery score. See the data-requirements document for the shared data-tool contract.

Current work remains market-state research, not strategy/account/production continuation.

---

## Historical steps retained for audit only

1. Read `docs/user/cloud_execution_prompt.md` and `docs/governance/data_usage_declaration.json`.
2. Validate `python scripts/validate_theme_package.py`.
3. Historical baseline: 5m+0, 1-hour 1st-order Butterworth lowpass, vol-scaled
   hysteresis k=1. Remaining problem was working-band saw vs slower drift.
4. Historical instruction said not to use 2026 to pick parameters. A later explicit owner authorization allowed a bounded 2026 held-out recovery-state validation; that later authorization does not permit tuning on the validation outcomes.
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
   The historical scientific status was `infrastructure or measurement gap`.
