# STAR50 / CSI1000 AI entry

Read `AGENTS.md`, `CURRENT_RESEARCH.md` and `CONTINUE_HERE.md` first.

Latest scientific state: **`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`**.

Previous M3 state remains **`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**.

Historical research backlog state: **closed; remaining executable legacy backlog = 0**. Do not infer pending work from old branch names. Read `docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json` before proposing to rerun a historical branch.

Primary current authority:

- `research/cross_index_degree_transfer_utility_v1/PROGRAM_STATE.json`
- `research/cross_index_degree_transfer_utility_v1/RESULTS.md`
- `research/cross_index_degree_transfer_utility_v1/DECISIVE_RECEIPT.json`
- `research/cross_index_degree_transfer_utility_v1/EXECUTION_RECEIPT.json`
- `research/cross_index_degree_transfer_utility_v1/evidence/VALIDATION_RESULTS.json`
- `research/cross_index_degree_transfer_utility_v1/evidence/FROZEN_MODELS.json`

Interpret the latest result strictly: after target own D4-style current I/V is known, adding the other index's contemporaneous current I/V produces only tiny incremental loss reductions. Across 12 frozen X-vs-C/L comparisons, every relative improvement is below 1% and every primary 5-day adjusted interval crosses zero. The largest pooled point estimate is only about +0.142% for 60m future tail vs own-C, with absolute Brier gain ~0.000119 < 0.0005. No endpoint/horizon jointly passes.

Do not post-hoc rescue this with one-way STAR50/CSI1000 selection, alternate lags, state filters, thresholds, horizons, extra nonlinearities, or sample deletion. The visible STAR50-negative / CSI1000-positive slice asymmetry is a failed robustness condition, not an invitation to select one direction after outcomes.

The decisive Validation run is `34677297901`; it used the exact original pre-Validation frozen model SHA `7eae7142323b38c5ae54618745e9ad9891c00afb09d02e8eb8def4490675f6b6`. Complete Action evidence was copied byte-for-byte into the research `evidence/` directory.

M3 remains a preserved predecessor result: it contains future-RMS information beyond own current-I/V, but its current refresh does not clear the frozen practical gate against equal-complexity lagged M3. Therefore M3 also remains outside D5/V19.

Backlog closeout rules still apply: V7/first-shock/RMR failures are historical outcomes; V8/V9/V10 ancestry is superseded by V17/V19; 2026-09-11 V11 is duplicate; `risk-gate-takeover` is coordination; old highvol-router is outside current scope; v0.6.17 is permanently blocked under its frozen protocol because qualifying prior identities do not exist.

Historical decisions remain authoritative: risk-coordinate full replication did not pass frozen support gates; V19 stays frozen; D3 negative practical decision stays; D4 remains endpoint-limited own current-I/V support; D5 remains bounded consumer engineering acceptance.

Parallel reception state remains `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`. Historical D5R still says no true local per-tick `received_at` exists; never infer one from available_at, batch ingested_at, file mtime, observation time or row order.

Open new science only for a genuinely distinct causal risk mechanism that can be frozen before outcomes and is not a rescue of M3, cross-index current degree, V19, old detector/reversal/router work. Do not query BlackBox or protected 2026 row detail, do not start V20/D6, and do not raise production authority.

`production_authority=false`.
