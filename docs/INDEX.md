# STAR50 filter lab index

- **Current authority evidence:** [HighVol Router V1 reusable Validation result](research/highvol_router_v1/VALIDATION_RESULTS.md) → [frozen router identity](research/highvol_router_v1/FROZEN_ROUTER_V1.json) → [decisive receipt](research/highvol_router_v1/DECISIVE_RECEIPT.json). CSI1000 is the only active HighVol payoff module; STAR50 and unsupported contexts are `NO_TRADE`. Validation: 129 trades, pooled net +0.5463 bp/trade @1bp/leg, BE 1.2731 bp, 2/3 positive annual slices. Research-only; `production_authority=false`; BlackBox queries=0.

- Current cloud entry: [两指数底层K线风险研究交接](handoff/cloud_risk_gate_20260907/HANDOFF.md) → [数据口径](handoff/cloud_risk_gate_20260907/DATA.md) → [云端—本地记录](ops/cloud_local_communication.md)。15项文献全文和有界指数3s/1m/5m；本地为存储核心，不开启交易/期权或2026研究。

- Latest: [因果未来波动工具V1](research/causal_volatility_tool_v1/result.md) → [接口与复现](research/causal_volatility_tool_v1/workflow.md)。环境预测有进展，普通时段突变预警未通过；不授交易路由。

- Latest: [中证1000与科创50同期同频尾部研究](research/tail_distribution_v1/result.md) → [工作流](research/tail_distribution_v1/workflow.md)。绝对尾部与超背景异常分开；未将结果直接注册为交易桶。

- Latest measurement: [秒级路径效率方差与中证1000半日低通迁移](research/resolution_transfer_v1/result.md) → [工作流](research/resolution_transfer_v1/workflow.md)。两项完成但未产生最优分辨率或因果路由，V2参数不变。

- Current V2: [平均单笔质量优先回测](research/half_day_slope_union_v2/result.md) → [执行与图形工作流](research/half_day_slope_union_v2/workflow.md) → [冻结参数](research/half_day_slope_union_v2/selected_policy.json)。保留V1与完整324身份研究，指数模拟不授真实载体/生产权限。

- Current version: [半日低通1分钟、1—5根斜率并集白皮书](research/half_day_slope_union_v1/whitepaper.md) → [工作流](research/half_day_slope_union_v1/workflow.md) → [线程接管](research/half_day_slope_union_v1/handoff.md)。Layer 3策略原型；未进行历史收益选参。

- Latest: [三个因果可得方案与组合验证](research/three_proposals_v1/report.md) — 原满单位账户；A有成本敏感型进展、聚集未获支持，C全局优先失败，无新策略晋级。

- Latest hypothesis result: [波形偏斜与急起急落验证](research/wave_shape_v1/report.md) — 位移集中度有条件性支持，单纯左右偏斜不成立为通用规则；原账户不变。

- Current owner correction: [原满仓14.32%/19.75%回撤逐笔记账与案例解释](research/original_drawdown_trade_audit_v1.md) — 完整记账不等于完整根因，逐笔归因仍须继续。

- Current result: [条件分桶首轮真实盘口账户研究](research/conditional_bucket_v1/result_v1.md) — 18账户、92工件重放、70测试；无新策略晋级。
- Open data issue: [588080期权历史条款修复提示词](research/conditional_bucket_v1/datahub_terms_repair_prompt.md)

- Accepted data: [fixed STAR50 spot v1.1 and option binding](research/conditional_bucket_v1/datahub_binding_v1.json)

- Active task: [条件分桶双目标合同](research/conditional_bucket_v1/owner_contract.json) → [历史盘口阻断诊断](research/conditional_bucket_v1/datahub_diagnosis.md)

- Prior local result: [第五轮连败与频段机制](research/streak_mechanism_v1/report.md)

- Current task and corrections: `CURRENT_RESEARCH.md`
- Next session: `docs/user/next_session_drawdown_root_cause.md`
- available_at semantics: `docs/governance/available_at_owner_clarification_20260906.json`

- Data: `data/README.md`
- Roles: `docs/governance/data_usage_declaration.json`
- Scope: `docs/governance/package_scope.json`
- Cloud prompt: `docs/user/cloud_execution_prompt.md`
- Receipts: `docs/research/`
- Skill: `.codex/skills/strategy-slice-rebuild/SKILL.md`

## 第四轮：固定策略跨尺度根因

- [报告](research/cross_scale_root_cause/report.md)
- [白皮书](research/cross_scale_root_cause/whitepaper.md)与[工作流](research/cross_scale_root_cause/workflow.md)
- [不可变证据清单](../artifacts/cross_scale_root_cause/manifest.json)
- [校验状态与CI启动失败回执](research/cross_scale_root_cause_ci_closeout.md)
