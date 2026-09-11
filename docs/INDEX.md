# STAR50 filter lab index

- **Current validated integrated episode authority:** `research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md` → `research/highvol_risk_episode_state_machine_v19_validation/DECISIVE_RECEIPT.json` → `research/highvol_risk_episode_state_machine_v19_validation/FROZEN_VALIDATION_CONTRACT.json` → Development evidence in `research/highvol_risk_episode_state_machine_v19/`. V19 freezes an E-15s close-confirmed risk-episode state machine: partial `UNSAFE/RECOVERING` is emitted immediately, while provisional partial `NORMAL` cannot close an already-active risk state before the 5m bar itself closes. Reusable 3s Validation is 2024-2025 only: 45,590 evaluable checkpoints; pooled precision `0.994594`, recall `0.989246`, FPR `0.000836`, exact three-state agreement `0.996315`; 542 reference episodes with capture `0.998155`, fragmentation `0.001845`, false machine-episode rate `0.049123`, same-checkpoint onset `0.880074`. `queried_2026_3s=false`; `production_authority=false`; BlackBox queries=0.

- **Current validated switch-on component:** `research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md` → `research/highvol_unsafe_switch_on_v18_validation/DECISIVE_RECEIPT.json` → `research/highvol_unsafe_switch_on_v18_validation/FROZEN_VALIDATION_CONTRACT.json` → Development evidence in `research/highvol_unsafe_switch_on_v18/`. V18 validates the frozen E-15s causal `NORMAL/RECOVERING -> UNSAFE` switch-on measurement using the unchanged V9 partial-state machine. Reusable 3s Validation is 2024-2025 only: 43,793 evaluable bars, 810 true switch-ons, precision `0.951123`, recall `0.888889`, FPR `0.000861`; both annual slices and both indices passed.

- **Current validated realtime recovery component:** `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md` → `research/highvol_realtime_horizon_adaptive_v17_validation/DECISIVE_RECEIPT.json` → `research/highvol_realtime_horizon_adaptive_v17/FROZEN_REALTIME_TRANSFER.json`. At exactly E-15s, 15m/30m use frozen V16 `state + recent-shock age`; 60m uses frozen V16 recent-shock-age-only. Reusable 3s Validation is limited to 2024-2025.

- **Current validated final-5m recovery component:** `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json` with reusable Validation in `research/highvol_horizon_adaptive_v16_validation/VALIDATION_RESULTS.md`. The 5m object is validated through 2026-08-21: 15m/30m use `current_state + recent-shock age`; 60m uses recent-shock age only. V16's 2026 5m authority does not create 2026 3s realtime authority.

- **Current validated causal architecture:** `V18 switch-on -> V19 close-confirmed UNSAFE / RECOVERING continuity -> V17/V16 recovery -> close-confirmed Normal`. The integrated V19 object is now reusable-Validation supported on the repository's available 2024-2025 3s coverage.

- **Current scope:** bottom-layer K-line risk-state annotation/gating only. Historical payoff/router material is archive evidence and is not current authority after scope repair. Historical payoff V17 branches are unrelated to current risk-state V17.

- Current cloud entry: [两指数底层K线风险研究交接](handoff/cloud_risk_gate_20260907/HANDOFF.md) → [数据口径](handoff/cloud_risk_gate_20260907/DATA.md) → [云端—本地记录](ops/cloud_local_communication.md)。

- Prior volatility research: [因果未来波动工具V1](research/causal_volatility_tool_v1/result.md) → [接口与复现](research/causal_volatility_tool_v1/workflow.md)。普通时段第一下突变预警未通过；V18 不重启该失败目标，而研究并验证 bar 内风险证据形成。

- Distribution research: [中证1000与科创50同期同频尾部研究](research/tail_distribution_v1/result.md) → [工作流](research/tail_distribution_v1/workflow.md)。

- Measurement archive: [秒级路径效率方差与中证1000半日低通迁移](research/resolution_transfer_v1/result.md) → [工作流](research/resolution_transfer_v1/workflow.md)。

- Historical payoff research: [平均单笔质量优先回测](research/half_day_slope_union_v2/result.md)；[半日低通1分钟、1—5根斜率并集白皮书](research/half_day_slope_union_v1/whitepaper.md)；[三个因果可得方案与组合验证](research/three_proposals_v1/report.md)；[波形偏斜与急起急落验证](research/wave_shape_v1/report.md)；[原满仓回撤逐笔记账](research/original_drawdown_trade_audit_v1.md)；[条件分桶首轮研究](research/conditional_bucket_v1/result_v1.md)。

- Current task and corrections: `CURRENT_RESEARCH.md`
- Continue here: `CONTINUE_HERE.md`
- available_at semantics: `docs/governance/available_at_owner_clarification_20260906.json`
- Data: `data/README.md`
- Roles: `docs/governance/data_usage_declaration.json`
- Scope: `docs/governance/package_scope.json`
- Receipts: `docs/research/` plus active `research/highvol_*` authority directories.
- Skill: `.codex/skills/strategy-slice-rebuild/SKILL.md`

## 第四轮：固定策略跨尺度根因（历史保留）

- [报告](research/cross_scale_root_cause/report.md)
- [白皮书](research/cross_scale_root_cause/whitepaper.md)与[工作流](research/cross_scale_root_cause/workflow.md)
- [不可变证据清单](../artifacts/cross_scale_root_cause/manifest.json)
- [校验状态与CI启动失败回执](research/cross_scale_root_cause_ci_closeout.md)
