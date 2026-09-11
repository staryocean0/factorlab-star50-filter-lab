# 当前任务：面向下游分桶的因果 K 线风险属性交付

更新：2026-09-11，D2 已执行并验收。用户要求风险属性服务于跟踪行情演变、下游状态识别和策略适用条件分桶；本仓不开发具体交易策略。数学、统计和研究判定由执行者负责。

## 当前权威链

1. 数据治理：`docs/governance/DATA_USAGE_POLICY_V2.md`、`data_usage_declaration.json`；研究桶边界：`BUCKET_SCOPE_REPAIR_20260909.md`。
2. 方向：`docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md`。
3. 当前执行状态：`research/causal_state_delivery_d2/PROGRAM_STATE.json`、`EXECUTION_RECEIPT.json`、`RESULTS.md`。
4. D1 原始契约与执行回执保留在 `research/causal_state_delivery_v1/`，不是当前待执行状态。
5. 科学基线回溯原 V19/V18/V17/V16 报告、代码、surface 和 receipt，不改封存字节。

## 使命与当前阶段

**把行情演变中已经发生、在当时可以知道的 K 线风险属性及其变化，转为下游可按时点消费的状态、转移和适用性信息。**

历史科学断点：`V19_VALIDATED_RESIDUAL_PATH_CLOSED_NO_V20`。
当前交付断点：**`D2_CAUSAL_REPLAY_SUPPORTED_D3_NOT_EXECUTED`**。

D1 契约与 E-15 原型的 20 项测试保留通过。D2 已增加独立顺序价格计算内核、E-15/CLOSE 事件、冻结恢复概率、不可变事件账本与 as-of 研究消费者；38 项新测试通过。

## D2 已完成的真实证据

- raw replay run `34620317766`，job `103332375643`，执行 commit `2102642cc18fe17b577f818e4f31e2a6e8f4ad7e`。
- artifact `10271634055`，SHA256 `cf1c89e1412fd70f27992d9077af10dd7887a6843072e03ef808902bf5a84096`。
- 2021–2025 两指数完整网格 `116,352` 个 bar；原可用 E-15 行 `113,928` 全部保留。
- 原可用行的状态、冲击、观察时点、冲击年龄、概率 gating 与冻结概率：**零不一致**。
- E-15/CLOSE 事件 `232,704`；市场未来扰动锚点 `20/20` 通过。
- 当前会话独立核验全部事件、哈希链及18个输出文件，不冒充会话内又重算原始 Parquet。

执行地点：标准库单元测试和产物复核在本会话；全量原始价格回放在有界 Actions。会话数据传输/Parquet依赖不可用、没有可调用本地执行器，已在协议和回执记录 fallback 理由。本地 FactorLab/DataHub 未自动执行；完整仓库测试与生产服务未验收。

## 交付限制必须随结果传递

原可用 cohort 的覆盖是100%；完整网格覆盖是 **97.9167%**。每天第一根09:35 bar缺少同日上一收盘参考，两指数共 `2,424` 个bar在两种时钟上都明确不可用，不补NORMAL，不跨夜造收益。

E-15 输出中，恢复曲线 `12,660` 条，对机器风险行覆盖 `80.8171%`；不可评分保留原 gate，不补概率0/1。CLOSE 可评分 `12,662` 条。所有曲线保持冻结单调性和60m anchor。

观察新鲜度不等于可用性：最大观察年龄165秒；超过120秒的2,424条全部集中在15:00 bar的E-15；其他时点另有30条超过15秒。D2不据此删样本或更换checkpoint。下游应保留 observation_time/observation_age_seconds；D3要在结果前明确时段、窗口和新鲜度解释。

15秒是 owner_realtime_assumption 下的理想发布提前量，不是实测端到端延迟。冲击年龄按日内交易bar步数，跨午休不跨日；冻结概率标签与参考起点不改造成任意墙钟的新目标。

## 下一项直接任务：D3

**先预注册非PnL风险分桶效用协议，再评价。** 检查因果状态/转移是否区分后续实现波动、再次冲击、风险持续和恢复，并且是否提供超越上一已确认状态、简单历史波动等匹配基准的信息。

在看结果前明确 endpoint、未来窗口与输入不重叠、bar-time与墙钟/午休/收盘边界、覆盖口径、最小实际效应、依赖块不确定性；报告桶占用、NORMAL风险泄漏、误报、转换时点与年度/指数稳定性。不要把自身标签的一致性或D2零漂移当作效用证明。

D3尚未执行。D2不能证明下游增量效用或盈利，不自动授予实盘、交易路由、仓位或生产权限。

## 保持冻结的基线

V19 runner：`ee2fce299d5ee21abf1ab2c2c5183bac101ae822`。Development run `34611126345` / artifact `10267923594`；Validation run `34612330970` / artifact `10268853374`。

V19 residual audit run `34614008432` / artifact `10270156874`；`NO_V20_FROM_V19_RESIDUALS`保留。这是研究优先级，不是不可改进性定理，也不是Validation永不能再用的数据禁令。

原始证据在 `research/highvol_risk_episode_state_machine_v19/`、`research/highvol_risk_episode_state_machine_v19_validation/`、`research/v19_residual_failure_audit/`。

架构：V18 switch-on → V19 UNSAFE/RECOVERING连续性 → V17/V16恢复信息 → 收盘确认NORMAL。对应原始组件见 `research/highvol_unsafe_switch_on_v18_validation/`、`research/highvol_realtime_horizon_adaptive_v17_validation/`、`research/highvol_horizon_adaptive_v16/`。

## 解释、范围与治理

Causal指当时可得、单边计算，不代表干预因果证明。整体风险recall不等于新风险提前recall；episode重叠不等于全程无遗漏；零提前退出部分由定义保证。NORMAL不保证交易安全，UNSAFE不等于看空，UNAVAILABLE不是NORMAL。

历史available_at仍是历史检索可得时间，不是盘中延迟。E-15不得输入未收盘final_state/未来路径，CLOSE不得回写早先快照。输出不含后验episode结束时间或交易动作。

不接管Range/UpTrend/DownTrend父结构；不恢复payoff/router、方向、持仓、止损止盈、成本收益优化；不修改其他仓或live registry。

Development 2021–2023可开发拟合；Validation 2024–2026-08-21可按冻结协议复用/诊断并启发下一Development，不直接拟合当前受测候选，也不是fresh OOS。实际3s证据仍止于2025；V16 final-5m到2026-08-21不创建2026 realtime证据。

`v19_frozen=true`; `d2_supported=true`; `d3_executed=false`; `v20_started=false`; `queried_2026_3s=false`; `blackbox_queried=false`; `pnl_computed=false`; `production_authority=false`。
