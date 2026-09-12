# STAR50 / CSI1000 AI entry

Read `AGENTS.md`, `CURRENT_RESEARCH.md` and `CONTINUE_HERE.md` first.

Latest scientific state: **`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**.

Historical research backlog state: **closed; remaining executable legacy backlog = 0**. Do not infer pending work from old branch names. Read `docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json` before proposing to rerun a historical branch.

Primary current authority:

- `research/activity_degree_incremental_utility_v1/PROGRAM_STATE.json`
- `research/activity_degree_incremental_utility_v1/RESULTS.md`
- `research/activity_degree_incremental_utility_v1/EXECUTION_RECEIPT.json`
- `research/activity_degree_incremental_utility_v1/evidence/VALIDATION_RESULTS.json`
- `docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json`

Interpret current M3 carefully: it adds short-horizon future-RMS information relative to a D4-style current-I/V baseline (15m A-vs-C +2.175%, individually supported), but it does **not** clear the frozen practical gate against an equal-complexity lagged-M3 control. A-vs-N log-RMS gains are only about +0.433% / +0.579% / +0.183% at 15/30/60m; tail endpoints are not supported. Therefore current M3 must not be promoted into the D5 consumer or V19 state machine and its thresholds must not be retuned to rescue the result.

Backlog closeout rules:

- V7/first-shock/RMR failures are historical outcomes, not tuning invitations.
- V8/V9/V10 ancestry is superseded by later validated V17/V19 authority.
- 2026-09-11 V11 is a duplicate design; completed V11/V12 already answered that path.
- `risk-gate-takeover` is a coordination branch, not a missing standalone experiment.
- old highvol-router is retired because PnL/route/hold/cost/Sharpe/MDD are outside current scope.
- v0.6.17 is permanently blocked under its frozen protocol because strict pre-v0.6.17 Git audit found no qualifying 349,923-row source identity and no v0.6.15 leg-universe identity. Never backfill a new hash and call it the old preregistered identity.

Historical decisions remain authoritative: risk-coordinate full replication did not pass frozen support gates; V19 stays frozen; D3 negative practical decision stays; D4 remains endpoint-limited current-I/V support; D5 remains bounded consumer engineering acceptance.

Parallel reception state remains `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`. Historical D5R still says no true local per-tick `received_at` exists; do not infer one from `available_at`, batch `ingested_at`, file mtime, observation time or row order. Recorder/adapter/cloud engineering acceptance is complete; only future physical feed can create future true-reception observations.

There is currently no legacy experiment to “continue”. Open new science only for a distinct causal risk mechanism that can be frozen before outcomes and is not a rescue of M3/V19/old detector/reversal/router work. Do not query BlackBox or protected 2026 row detail, do not start V20/D6, and do not raise production authority.

`production_authority=false`.
