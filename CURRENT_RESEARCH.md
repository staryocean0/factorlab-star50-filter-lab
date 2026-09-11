# 当前任务：面向下游分桶的因果 K 线风险属性交付

更新：2026-09-11。用户明确要求：风险识别要服务于跟踪行情演变与下游状态/策略分桶，优先因果可得和实际用途，不做脱离用途的学术优化；本仓仍不开发具体交易策略。数学、统计和研究判定由研究执行者负责。

## 当前权威链

1. 数据使用以 `docs/governance/DATA_USAGE_POLICY_V2.md` 与 `data_usage_declaration.json` 为准；研究桶边界沿用 `BUCKET_SCOPE_REPAIR_20260909.md`。
2. 下一阶段方向以 `docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md` 为准。
3. 执行状态以 `research/causal_state_delivery_v1/PROGRAM_STATE.json` 与 `EXECUTION_RECEIPT.json` 为准。
4. 基线结论回溯原始 V19/V18/V17/V16 报告与 receipt，不修改其封存字节。

## 使命与当前阶段

**把行情演变中已经发生、在当时可以知道的 K 线风险属性及其变化，转为下游可按时点消费的状态、转移和适用性信息。** 实用导向不是在本仓规定看多/看空、开仓/平仓、仓位或收益路由。

历史科学断点仍为 `V19_VALIDATED_RESIDUAL_PATH_CLOSED_NO_V20`。
当前执行阶段为 **`CAUSAL_KLINE_STATE_DELIVERY_V1_CONTRACT_TESTED_REPLAY_PENDING`**。

已完成：下一阶段契约；E-15 状态适配原型；20 项合成单元测试。
下一任务：冻结组件的 E-15/close 双时钟因果回放与消费者接入验收。
随后：先注册非 PnL 的风险分桶效用评价协议，再检验后续波动/冲击/持续与恢复是否被有效区分。

不是已完成事项：全量工程一致性、完整状态服务、实测延迟、分桶的增量市场效用、策略收益或生产上线。

## 保持冻结的基线

- V19 runner blob：`ee2fce299d5ee21abf1ab2c2c5183bac101ae822`。
- V19 Development：run `34611126345`，artifact `10267923594`。
- V19 reusable Validation：execution `b4527e2f431f5dfb2ef801f262d39f509253820f`，run `34612330970`，artifact `10268853374`。
- Validation artifact SHA256：`5989514df544ffc26c0559a185829f5c027df954a311dd9a43f3f0c9912238af`。
- V19 residual audit：run `34614008432`，artifact `10270156874`，SHA256 `b49c61d8b2345e0441c69fa7d94d25bf9425d572d13953e40e83aede72f4d0fb`；结论 `NO_V20_FROM_V19_RESIDUALS`。

原始证据：

- `research/highvol_risk_episode_state_machine_v19/PROTOCOL.md`
- `research/highvol_risk_episode_state_machine_v19/DEVELOPMENT_RESULTS.md`
- `research/highvol_risk_episode_state_machine_v19/DECISIVE_RECEIPT.json`
- `research/highvol_risk_episode_state_machine_v19_validation/FROZEN_VALIDATION_CONTRACT.json`
- `research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md`
- `research/highvol_risk_episode_state_machine_v19_validation/DECISIVE_RECEIPT.json`
- `research/v19_residual_failure_audit/RESULTS.md`
- `research/v19_residual_failure_audit/DECISIVE_RECEIPT.json`

冻结架构：V18 switch-on → V19 UNSAFE/RECOVERING 连续性 → V17/V16 恢复信息 → 收盘确认 NORMAL。

V18 的入口证据见 `research/highvol_unsafe_switch_on_v18_validation/`；V17 的实时恢复证据见 `research/highvol_realtime_horizon_adaptive_v17_validation/`；V16 surface 见 `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json`，其验证见 `research/highvol_horizon_adaptive_v16_validation/`。

## 当前结论必须怎样解释

V19 的 Validation 数字是与冻结参考语义的一致性，不是“所有市场风险”真值。整体风险 recall 不等于新进入提前 recall；episode 有重叠不等于整段无漏报。固定 E-15 checkpoint 的轨迹证据不等于全秒级生产回放。

“零提前退出”部分由 close-confirmed 定义保证，不能证明所有提前退出都不好；残差穿越阈值的描述不是不可改进性定理。当前停止的是针对 V19 已审计残差的事后优化，不是禁止任何具有实用目的的新问题。

此前入口中“一经消费 Validation 就无法继续有效研究”的强表述不再作为当前治理依据。Validation 可复用、可诊断并启发下一 Development；不得直接拟合当前受测候选，不得冒称 fresh OOS。历史封存报告保持原样。

## 下一阶段硬约束

实时输入与后验评价分离；不使用当前未收盘 final_state、未来路径或事后 episode 终点构造消费属性。发布快照不可回填改写，数据缺失不能补 NORMAL，概率不可用不能补 0/1。

`available_at` 保留历史检索语义；盘中因果时钟另列并标注用户已确认的实时假设或实际接收日志。不要制造实测延迟。

所有新工作须说明具体消费者用途、当时可得的信息、失败条件及结果前验收标准。不为版本号立项；有新需求时可独立开发候选，但保留 V19 基准，不覆盖冻结对象。

不接管 Range/UpTrend/DownTrend 父结构；不恢复 payoff/router、方向、持仓、成本收益优化；不修改其他仓或本地 live registry。

## 数据与权限

Development：2021–2023；reusable Validation：2024–2026-08-21，受实际来源覆盖约束。V17/V18/V19 实时验证覆盖止于 2025-12-31，V16 final-5m 止于 2026-08-21；后者不能创建 2026 3s 实时证据。

本次仅有契约/合成测试，无新行情查询、无新的统计 Validation、无 2026 3s、无截止日后数据或 BlackBox、无 PnL。

`v19_frozen=true`; `v19_residual_path_closed=true`; `v20_started=false`; `production_authority=false`。
