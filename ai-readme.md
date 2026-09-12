# STAR50 / CSI1000 AI entry

Read `AGENTS.md`, `CURRENT_RESEARCH.md` and `CONTINUE_HERE.md` first.

Latest scientific state: **`ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**.

Preserved predecessor states:

- `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`;
- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`;
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`.

Historical research backlog is closed; remaining executable legacy backlog = 0. Parallel reception remains `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`.

Primary current authority:

- `research/degree_trajectory_utility_v1/PROGRAM_STATE.json`
- `research/degree_trajectory_utility_v1/RESULTS.md`
- `research/degree_trajectory_utility_v1/DECISIVE_RECEIPT.json`
- `research/degree_trajectory_utility_v1/EXECUTION_RECEIPT.json`
- `research/degree_trajectory_utility_v1/evidence/VALIDATION_RESULTS.json`
- `research/degree_trajectory_utility_v1/evidence/FROZEN_MODELS.json`

Interpret the latest result strictly. C is the 84-column own-index D4-style current-I/V baseline. T adds the immediately preceding confirmed degree; O adds the two-valid-return-bars-back degree with the exact same 20-column transform/state-interaction block. T/O are both104 columns with identical schema/scaling/ridge. Since current I/V is already in C, lag1 degree and current-minus-lag1 delta are bijective at the raw-information level.

Decisive run `34680352701`; frozen model SHA `04b49e8613cad5b24822f8e827f8d6513f6fef74da5c2df0851e03473b4db188`. Validation n is39,770 /33,950 /22,310 at15/30/60m with100% trajectory coverage.

All twelve formal relative loss reductions are below the frozen1% practical gate. RMS gains T-vs-C/O are about +0.114%/+0.113% at15m, **+0.150%/+0.152% at30m**, and +0.024%/-0.041% at60m. Tail effects are tiny;15/30m T-vs-O tail is negative; absolute Brier gains are far below0.0005.

Do not misstate this as “delta contains zero information”:30m T-vs-C has a small positive adjusted interval. The correct conclusion is that the one-step trajectory does **not** show enough magnitude or stable advantage over the equal-complexity lag2 control for independent predictive promotion.

D4/D5 `lag_intensity`, `lag_ratio`, `delta_intensity`, `delta_ratio` remain allowed as descriptive/diagnostic/consumer fields under their existing contract, but they are not validated predictive gates. Do not change D5 decision logic or V19 from this result.

Never use this reusable Validation result to retune lag3/lag4, smoothing/decay, normalizers, nonlinear transforms, selected symbol/state/time subsets, ridge/horizons/bootstrap family, or to drop O.

The prior shock-memory, cross-index and M3 negative promotion decisions remain authoritative; D4 own current-I/V support, D3 negative practical decision, V19 freeze and D5 bounded consumer remain unchanged.

Historical D5R still says no true local per-tick `received_at` exists; never infer one from available_at, batch ingested_at, file mtime, observation time or row order.

Open new science only for a genuinely distinct causal risk mechanism frozen before outcomes. It must not be a rescue of trajectory lags/smoothing, shock-memory, cross-index current degree, M3, V19 or retired trading/router work. Do not query BlackBox or protected2026 row detail, do not start V20/D6, and do not raise production authority.

`production_authority=false`.
