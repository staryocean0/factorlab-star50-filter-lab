# STAR50 filter lab index

- **Current switch-on research authority (Development only):** `research/highvol_unsafe_switch_on_v18/DEVELOPMENT_RESULTS.md` → `research/highvol_unsafe_switch_on_v18/DECISIVE_RECEIPT.json` → `research/highvol_unsafe_switch_on_v18/PROTOCOL.md`. V18 measures causal within-bar evidence accumulation for new `NORMAL/RECOVERING -> UNSAFE` entries using the unchanged frozen V9 partial-state machine. Development: 65,431 evaluable bars, 1,361 true switch-ons. Frozen E-15s primary checkpoint: precision `0.970656`, recall `0.923586`, FPR `0.000593`; all 2021-2023 annual gates passed. Fixed diagnostic recall curve: E-60 `0.5805`, E-30 `0.8486`, E-15 `0.9236`, E-6 `0.9603`, E-3 `0.9956`. **V18 Validation has not been queried or authorized.** `production_authority=false`; BlackBox queries=0.

- **Current validated realtime recovery authority:** `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md` → `research/highvol_realtime_horizon_adaptive_v17_validation/DECISIVE_RECEIPT.json` → `research/highvol_realtime_horizon_adaptive_v17/FROZEN_REALTIME_TRANSFER.json`. At exactly `E-15s`, 15m/30m use the frozen V16 `state + recent-shock age` surface with the frozen V9 provisional state; 60m uses the frozen V16 recent-shock-age-only anchor. Reusable 3s Validation is limited to 2024-2025: 4,540 cohort rows, 4,516 realtime-scored, coverage 0.994714; 15m/30m probability MAE 0.000825/0.000638; 60m is exactly unchanged. `queried_2026_3s=false`; `production_authority=false`; BlackBox queries=0.

- **Current final-5m recovery authority:** V16 frozen horizon-adaptive recovery surface in `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json` with reusable Validation in `research/highvol_horizon_adaptive_v16_validation/VALIDATION_RESULTS.md`. The 5m object is validated through 2026-08-21: 15m/30m use `current_state + recent-shock age`; 60m uses recent-shock age only. V16's 2026 5m authority does not create 2026 3s realtime authority.

- **Current scope:** bottom-layer K-line risk-state annotation/gating only. Historical payoff/router material below is retained as archive evidence and is not current authority after the scope repair. The historical payoff V17 branches are unrelated to the current risk-state V17.

- Current cloud entry: [两指数底层K线风险研究交接](handoff/cloud_risk_gate_20260907/HANDOFF.md) → [数据口径](handoff/cloud_risk_gate_20260907/DATA.md) → [云端—本地记录](ops/cloud_local_communication.md)。15项文献全文和有界指数3s/1m/5m；本地为存储核心，不开启交易/期权研究。

- Latest prior volatility research: [因果未来波动工具V1](research/causal_volatility_tool_v1/result.md) → [接口与复现](research/causal_volatility_tool_v1/workflow.md)。环境预测有进展，但普通时段第一下突变预警未通过；V18 不重启该失败目标，而研究 bar 内风险证据形成。

- Latest distribution research: [中证1000与科创50同期同频尾部研究](research/tail_distribution_v1/result.md) → [工作流](research/tail_distribution_v1/workflow.md)。绝对尾部与超背景异常分开；未将结果直接注册为交易桶。

- Latest measurement archive: [秒级路径效率方差与中证1000半日低通迁移](research/resolution_transfer_v1/result.md) → [工作流](research/resolution_transfer_v1/workflow.md)。两项完成但未产生最优分辨率或因果路由。

- Historical V2 payoff research: [平均单笔质量优先回测](research/half_day_slope_union_v2/result.md) → [执行与图形工作流](research/half_day_slope_union_v2/workflow.md) → [冻结参数](research/half_day_slope_union_v2/selected_policy.json)。

- Historical payoff version: [半日低通1分钟、1—5根斜率并集白皮书](research/half_day_slope_union_v1/whitepaper.md) → [工作流](research/half_day_slope_union_v1/workflow.md) → [线程接管](research/half_day_slope_union_v1/handoff.md)。

- Historical: [三个因果可得方案与组合验证](research/three_proposals_v1/report.md)；[波形偏斜与急起急落验证](research/wave_shape_v1/report.md)；[原满仓回撤逐笔记账](research/original_drawdown_trade_audit_v1.md)；[条件分桶首轮研究](research/conditional_bucket_v1/result_v1.md)。

- Current task and corrections: `CURRENT_RESEARCH.md`
- Continue here: `CONTINUE_HERE.md`
- available_at semantics: `docs/governance/available_at_owner_clarification_20260906.json`

- Data: `data/README.md`
- Roles: `docs/governance/data_usage_declaration.json`
- Scope: `docs/governance/package_scope.json`
- Receipts: `docs/research/` plus the active `research/highvol_*` authority directories.
- Skill: `.codex/skills/strategy-slice-rebuild/SKILL.md`

## 第四轮：固定策略跨尺度根因（历史保留）

- [报告](research/cross_scale_root_cause/report.md)
- [白皮书](research/cross_scale_root_cause/whitepaper.md)与[工作流](research/cross_scale_root_cause/workflow.md)
- [不可变证据清单](../artifacts/cross_scale_root_cause/manifest.json)
- [校验状态与CI启动失败回执](research/cross_scale_root_cause_ci_closeout.md)
