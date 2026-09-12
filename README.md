# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓用于研究行情环境与策略适用条件，不开发交易动作、方向、仓位或收益 router。

## 当前：reception云端工程验收完成；历史冻结研究继续收口

当前主断点：**DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING**。

历史 D5R 仍确认没有逐条真实本机 `received_at`；这只限制历史实测延迟声明，不影响历史行情数据使用。前瞻 recorder、DataHub adapter 与完整 handoff 云端验收已全部完成。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [reception程序状态](research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [云端验收结果](research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_RESULTS.md)。

## 最新研究收口：risk-coordinate Validation v1

历史分支中一项已冻结、已执行但未进入权威树的2024/2025 Validation已经恢复并原样复现：

**RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE**。

[正式结果](docs/research/risk_coordinate_validation_v1/RESULT.md) → [执行回执](docs/research/risk_coordinate_validation_v1/EXECUTION_RECEIPT.json)。

原run `34303912251` 与复现run `34667783528` 在110,911个Validation rows及所有科学结果上逐项一致：state-persistence轴在STAR50/CSI1000 × 2024/2025全部复制；M3极端band未来15m RMS effect-size关系全部通过；但三个Unsafe极端格未达到预注册最小样本量，所以M3完整amplitude-axis不晋升。禁止事后降门槛、合并年份或移动M3 bands救结果。

## Reception云端验收

Action run `34666927078` 已完成：既有handoff ZIP/20个manifest文件校验；两指数各4,746行、共9,492行完整审计；4,746点observation grid完全一致；18项recorder + 23项adapter = 41项测试通过；真实DataHub源码seam与V2治理validator通过。

最早可控测量边界是 **TDX Python SDK返回之后、DataHub parser之前**，不是raw TCP/frame arrival。GitHub runner synthetic wrapper开销只作描述，不是live feed latency或production gate。

## 历史backlog审计

Action run `34668006394` 已扫描112个 `research/*` 分支：81已有结果，8个Action成功但结果未持久化，1个冻结但未成功执行，2个只有冻结设计。后续优先接管真正冻结而未完成的项目，而不是继续凭记忆造新版本。

## 保留的研究结论与停止线

[V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)、[D2](research/causal_state_delivery_d2/RESULTS.md)、[D3](research/causal_state_utility_d3/RESULTS.md)、[D4](research/continuous_risk_utility_d4/RESULTS.md)、[D5](research/state_degree_consumer_d5/RESULTS.md)、[D5R](research/reception_clock_adjudication_d5r/RESULTS.md)均保持原判。

不为V19 accuracy开V20；不因缺日志强开D6；不查询BlackBox逐行细节；不计算PnL；不恢复交易router；不提高production authority。

`cloud_acceptance_supported=true`; `risk_coordinate_full_replication=false`; `risk_coordinate_threshold_retune_allowed=false`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
