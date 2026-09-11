# STAR50 filter lab index

- **Current mathematical breakpoint — residual path closed:** `research/v19_residual_failure_audit/RESULTS.md` → `research/v19_residual_failure_audit/DECISIVE_RECEIPT.json` → `research/v19_residual_failure_audit/PROTOCOL.md`. Decision: **`NO_V20_FROM_V19_RESIDUALS`**. On consumed 2024-2025 Validation data, all 66 binary-risk FNs are late `NORMAL -> UNSAFE` final shocks still below the frozen 3σ threshold at E-15, while all 33 FPs are transient E-15 partial shocks that resolve below 3σ before close. The one uncaptured episode, one fragmented episode, and all 28 false machine episodes trace to these timing effects; all false episodes are one checkpoint long. Development 2021-2023 reproduces the same mechanism. Do not start V20 to optimize these boundary residuals.

- **Current validated integrated episode authority:** `research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md` → `research/highvol_risk_episode_state_machine_v19_validation/DECISIVE_RECEIPT.json` → `research/highvol_risk_episode_state_machine_v19_validation/FROZEN_VALIDATION_CONTRACT.json` → Development evidence in `research/highvol_risk_episode_state_machine_v19/`. V19 freezes the E-15s close-confirmed state machine: partial `UNSAFE/RECOVERING` is emitted immediately, while provisional partial `NORMAL` cannot close an already-active risk state before the 5m bar closes. Reusable 3s Validation 2024-2025: 45,590 checkpoints; precision `0.994594`, recall `0.989246`, FPR `0.000836`, exact three-state agreement `0.996315`; 542 reference episodes with capture `0.998155` and fragmentation `0.001845`.

- **Current validated switch-on component:** `research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md` → `research/highvol_unsafe_switch_on_v18_validation/DECISIVE_RECEIPT.json`. V18 validates the frozen E-15s causal `NORMAL/RECOVERING -> UNSAFE` switch-on measurement on 2024-2025 3s: precision `0.951123`, recall `0.888889`, FPR `0.000861`.

- **Current validated realtime recovery component:** `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md` → `research/highvol_realtime_horizon_adaptive_v17_validation/DECISIVE_RECEIPT.json` → `research/highvol_realtime_horizon_adaptive_v17/FROZEN_REALTIME_TRANSFER.json`. At E-15s, 15m/30m use frozen V16 `state + recent-shock age`; 60m uses frozen V16 recent-shock-age-only. Realtime Validation is limited to 2024-2025.

- **Current validated final-5m recovery component:** `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json` with reusable Validation in `research/highvol_horizon_adaptive_v16_validation/VALIDATION_RESULTS.md`. Final-5m authority extends through 2026-08-21; this does not create 2026 3s authority.

- **Current validated causal architecture:** `V18 switch-on -> V19 close-confirmed UNSAFE / RECOVERING continuity -> V17/V16 recovery -> close-confirmed Normal`.

- **Forward rule:** V11-V19 and the V19 residual audit should not be reopened merely to improve residual metrics. A new version requires a qualitatively new causal question or genuinely new independent realtime data. Existing 2024-2025 realtime Validation is consumed and cannot serve as a fresh V20 holdout.

- **Current scope:** bottom-layer K-line risk-state annotation/gating only. Historical payoff/router material is archive evidence and is not current authority. Historical payoff V17 branches are unrelated to current risk-state V17.

- Current cloud entry: [两指数底层K线风险研究交接](handoff/cloud_risk_gate_20260907/HANDOFF.md) → [数据口径](handoff/cloud_risk_gate_20260907/DATA.md) → [云端—本地记录](ops/cloud_local_communication.md)。

- Prior volatility research: [因果未来波动工具V1](research/causal_volatility_tool_v1/result.md) → [接口与复现](research/causal_volatility_tool_v1/workflow.md)。普通时段第一下突变预警未通过；V18 did not reopen that failed target.

- Distribution research: [中证1000与科创50同期同频尾部研究](research/tail_distribution_v1/result.md) → [工作流](research/tail_distribution_v1/workflow.md)。

- Measurement archive: [秒级路径效率方差与中证1000半日低通迁移](research/resolution_transfer_v1/result.md) → [工作流](research/resolution_transfer_v1/workflow.md)。

- Current task and corrections: `CURRENT_RESEARCH.md`
- Continue here: `CONTINUE_HERE.md`
- Data: `data/README.md`
- Roles: `docs/governance/data_usage_declaration.json`
- Scope: `docs/governance/package_scope.json`
- Receipts: `docs/research/` plus active `research/highvol_*` and `research/v19_residual_failure_audit/` authority directories.

`v20_started=false`; `queried_2026_3s=false`; `blackbox_queried=false`; `production_authority=false`.
