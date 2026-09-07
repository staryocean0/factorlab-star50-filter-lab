# Continue here

**Current entry supersedes the numbered historical steps below.**

Read first:
1. `docs/research/post_shock_recovery_v1/STABLE_STATE_SPEC.md`
2. `docs/research/post_shock_recovery_v1/STATE_TRANSITION_EVIDENCE.md`
3. `docs/research/post_shock_recovery_v1/REACTIVATION_DIAGNOSTIC.md`
4. `docs/research/post_shock_recovery_v1/VALIDATION_READINESS.md`
5. `docs/research/post_shock_recovery_v1/NEXT_SNAPSHOT_PROTOCOL.md`
6. `docs/research/post_shock_recovery_2026/RESULTS.md`
7. `docs/ops/data_requirements_star50_risk_research.md`
8. `docs/handoff/cloud_risk_gate_20260907/HANDOFF.md`

Current supported research line is:

`observed first shock -> post-shock episode {Unsafe <-> Recovering}`

The episode starts Unsafe. Thereafter the primary continuous score is:

`recovery_ratio = trailing completed-5m RMS / frozen pre-shock sigma_pre`

The five-minute window is refreshed every completed minute. Recovering can reactivate to Unsafe; do not lock the episode into monotone recovery.

For analysis/visualization only:
- Recovering-low: ratio <1.0
- Recovering-high: 1.0..1.5
- Unsafe: >=1.5

The durable causal representation remains only Unsafe vs Recovering plus the continuous ratio. Do not promote the high/low display bands to separate causal states.

`Clean` is **not** an online validated transition. Do not re-open release-rule/threshold/model tuning on the already-consumed 2024-2025 data or the 2026-01-05..2026-08-21 validation snapshot.

Consumed-history diagnostics have not justified adding:
- elapsed time since shock;
- time since the latest Unsafe reading;
- event-close mild/severe shock grades;
- shock direction;
- background-sigma terms beyond the fixed normalization;
- cross-index headline-volatility terms;
- trailing2/trailing10 substitutions;
- hysteresis tuned from observed state flips;
- lunch/overnight bridging.

Session boundary termination means censored/outside the current model, not Clean.

## Next independent data

The next genuinely independent same-semantics time extension starts after `2026-08-21`.

Do **not** inspect post-shock outcome summaries while data accumulate. Use the blind readiness gate:

- `docs/research/post_shock_recovery_v1/code/readiness_gate.py`

It accepts only frozen first-shock event IDs/counts and rejects post-shock outcome/state columns.

Frozen readiness tiers:
- <10 pooled eligible first shocks: descriptive only;
- 10-19: limited validation;
- >=20 pooled, with >=6 from each index: minimum formal core validation;
- >=30 pooled, with >=10 from each index: preferred formal snapshot.

At the formal snapshot, apply `NEXT_SNAPSHOT_PROTOCOL.md` once. The primary pass/fail object is now the durable two-state contrast:

`P(next 5m Unsafe | current Unsafe) > P(next 5m Unsafe | current Recovering)`

plus positive continuous current-ratio / next-ratio association. The 3-band strict ordering is secondary because Recovering-high/low are display bands only.

Do not alter the readiness threshold, state boundary, window length, event definition, or acceptance criteria after new outcomes are opened.

Reference implementation / validation harness:
- `docs/research/post_shock_recovery_v1/code/post_shock_state.py`
- `docs/research/post_shock_recovery_v1/tests/test_post_shock_state.py`
- `docs/research/post_shock_recovery_v1/code/state_transition_eval.py`
- `docs/research/post_shock_recovery_v1/tests/test_state_transition_eval.py`
- `docs/research/post_shock_recovery_v1/code/readiness_gate.py`
- `docs/research/post_shock_recovery_v1/tests/test_readiness_gate.py`

The core state line needs native 1m STAR50/CSI1000 data plus immutable manifest/quality receipts. 3s observations remain important for path/measurement research but are not required to compute the stable recovery score.

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
