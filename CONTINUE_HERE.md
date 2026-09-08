# Continue here

## Current mandatory entry: three-pool data-use regime

Before any new research, read:

1. `docs/governance/DATA_USAGE_POLICY_V2.md`
2. `docs/governance/data_usage_declaration.json`
3. `docs/governance/blackbox_query_ledger.json`
4. `AGENTS.md`

Then run:

`python scripts/validate_data_usage_policy.py`

Forward research must use the stable three-pool regime:

- **Development:** 2021-01-01 through 2023-12-31. Open fitting/search/detail pool.
- **Validation:** 2024-01-01 through 2026-08-21. Candidate-under-test is not fit on these rows, but after development freeze the period may be evaluated repeatedly, opened in detail, diagnosed, and used to guide the next development iteration. It remains permanently reusable validation evidence and is not fresh OOS.
- **BlackBox-V1:** the first 60 complete trading days strictly after 2026-08-21, once available and manifest-frozen. It is repeatedly reusable only through pre-registered aggregate metrics. Never inspect dates/events/sessions/paths/best-worst examples from this pool.

Do not call a period "burned" merely because it was used. If black-box detail is exposed, record the exposure and reclassify that snapshot to Validation; it remains usable.

Historical sealed reports retain their historical protocol wording. The V2 policy changes future data use; it does not rewrite old evidence or turn old results into fresh OOS.

## Current research interpretation

The latest state/routing work remains research-only. `Unsafe` is a useful causal risk annotation, but current historical routing improvements are sparse and year-concentrated. Do not continue retrospective parameter/policy search merely because Development/Validation remain reusable. Reuse the pools deliberately: Development to invent/fit, Validation to diagnose/iterate, BlackBox only to answer whether a frozen candidate survives the blinded test.

## Historical handoff entry

The cloud-risk-gate handoff remains available at:
[Cloud risk-gate handoff, 2026-09-07](docs/handoff/cloud_risk_gate_20260907/HANDOFF.md).
Run `python scripts/validate_cloud_risk_gate_package.py` when working on that package.

The numbered material below is historical context and cannot override the current three-pool governance.

1. Read `docs/user/cloud_execution_prompt.md` and `docs/governance/data_usage_declaration.json`.
2. Validate `python scripts/validate_theme_package.py`.
3. Historical baseline: 5m+0, 1-hour 1st-order Butterworth lowpass, vol-scaled hysteresis k=1. Remaining problem was working-band saw vs slower drift.
4. Old instructions saying not to reuse later years are superseded for forward data-use roles by `DATA_USAGE_POLICY_V2.md`; old OOS claims themselves are not upgraded.
5. First takeover drawdown study: `docs/research/drawdown_conditions/report.md`.
   Baseline exactly reproduced (sigma population std, ddof=0). Fixed slow-conflict half-exposure diagnostic reduces zero-cost primary-view MDD 14.32% to10.68%, but is not promoted: available_at gap, offset4 and2023/2025 counterexamples.
6. Validate `python scripts/validate_drawdown_study.py`. Resolve data availability and tradable execution before any stronger causal or production claim.
7. Second round: `docs/research/execution_counterexamples/report.md`.
   Slow-conflict MDD advantage beyond constant exposure was not robust to delay.
8. Exact minute/coarse endpoint bridge handles six-minute first-session offset bars and first-observed quotes following synthetic missing-minute repair. Source publication semantics and tradable execution remain separate measurement questions.
