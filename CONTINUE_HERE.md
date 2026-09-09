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

**Current supported payoff router:** HighVol Router V1 is Validation-supported as a research candidate. It routes only the frozen CSI1000 (`000852.SH`) long 3-minute continuation module and explicitly routes STAR50 (`000688.SH`) plus all unsupported HighVol contexts to `NO_TRADE`. Development reproduced 104 trades; reusable Validation produced 129 trades with pooled net `+0.5463 bp/trade` after 1 bp per leg, one-way break-even `1.2731 bp`, and 2/3 positive annual slices. The 2026-through-2026-08-21 slice was slightly negative. Read `docs/research/highvol_router_v1/VALIDATION_RESULTS.md`, `FROZEN_ROUTER_V1.json`, and `DECISIVE_RECEIPT.json` before modifying this lane.

**Stability qualification:** the same frozen 104/129 trade sets were audited without changing the candidate. Validation day-block bootstrap 95% interval is `[-1.9855,+3.0590] bp/trade` with `P(mean>0)=67.04%`; at 1.5 bp/leg the pooled Validation mean becomes `-0.4537 bp/trade`; removing the top 3 positive PnL days makes the remaining mean `-0.2833 bp/trade` (top 5: `-0.7510`). All leave-one-year-out Validation estimates remain positive, so the weakness is not a single-year artifact, but the cost margin and strong-day dependence are material. Read `docs/research/highvol_router_v1/STABILITY_AUDIT.md` and `STABILITY_RECEIPT.json`. The correct state is therefore: **research acceptance passed; production-quality stability not established**.

The separate STAR50 V10–V17 sign-flip program remains closed with no empirical candidate. Do not reinterpret the CSI1000 Router V1 result as a rescue of that STAR50 line, and do not generalize Router V1 into a generic HighVol strategy.

The router remains research-only. `production_authority=false`. Do not add sizing, leverage, confirmation waits, stops, tail thresholds, hold changes, date censoring, or other payoff changes under the name Router V1. Any materially new payoff hypothesis must return to Development first. Tradable-instrument mapping may be audited separately, but must not be presented as if the index return itself were executable. BlackBox-V1 remains untouched and query count remains zero; do not query it merely because reusable Validation passed.

`Unsafe` and HighVol remain useful causal risk annotations, but historical routing improvements can be sparse and year-concentrated. Reuse the pools deliberately: Development to invent/fit, Validation to diagnose/iterate, BlackBox only when a separately frozen blinded test is explicitly authorized.

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
