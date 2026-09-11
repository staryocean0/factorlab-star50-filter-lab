# 当前任务：D3 已完成，未获实际增量用途晋升

更新：2026-09-12。用户要求因果K线风险属性服务行情跟踪与下游状态/策略分桶，数学与统计决策由执行者负责；本仓不开发具体交易策略。

## 权威链

数据治理以 `docs/governance/DATA_USAGE_POLICY_V2.md` / `data_usage_declaration.json` 为准，桶边界沿用 `BUCKET_SCOPE_REPAIR_20260909.md`。
方向以 `docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md` 为准。
**当前执行状态：`research/causal_state_utility_d3/PROGRAM_STATE.json` → `RESULTS.md` → `DECISIVE_RECEIPT.json` / `EXECUTION_RECEIPT.json` → `PROTOCOL.md` / `FIT_FREEZE_RECEIPT.json`。**
D1、D2和V16—V19的报告、原始程序状态与回执仍是封存历史，不把其中“D3未执行”当作当前断点。

## 三层结论

1. 科学基线：V19在冻结参考语义下具有reusable Validation支持；残差优化路径已关闭，不开accuracy微调V20。
2. 工程交付：D2因果E15/CLOSE回放已通过，113928原可用行零状态/概率漂移，232704事件与已声明范围的前缀测试通过。
3. 实际风险信息：**D3_INCREMENTAL_UTILITY_NOT_SUPPORTED**。D3已实际执行，但未达到本协议最小实际效应，不晋升为已证实有足够增量预测用途的风险门控。

当前工作状态：**D3_COMPLETED_NO_PRACTICAL_INCREMENTAL_PROMOTION**。这不是执行失败，也不是V19作废。

## D3结果和含义

协议先提交于43d46e211656e086a40c7a61c622674baa7b6011；30个固定信息探针仅在2021–2023拟合，78c12f27f43107b0b1f08902b75be4af09e9c638先封存模型哈希，再执行2024–2025评分。Validation可复用，非fresh OOS。V19/恢复表未重拟合。

在上一确认状态、已知冲击年龄、时点/指数及简单历史波动基准上加入当前状态/转移/冻结恢复属性：

| H | log未来RMS MSE相对减少 | 未来尾部Brier相对减少 |
|---|---:|---:|
| 15m | 0.46336% | 0.81010% |
| 30m | 0.74191% | 0.79116% |
| 60m | 0.91026% | 0.65491% |

6项都有正增量、12项调整后的5日块区间为正、年度/指数方向一致，但全部低于事前1%相对门槛。15/30m尾部还未达到0.0005绝对Brier门槛。不降低门槛，不用20日块结果或未注册比较改判。

基准再加入同一E15时点连续冲击强度/波动比率后，状态字段额外改善约0.003%–0.058%，全部调整区间跨0。这是固定探针下的结果，不是状态永远无用的定理。

描述性风险区分仍存在：15m尾部窗口占比NORMAL2.8136%、RECOVERING3.9807%、UNSAFE10.0386%。但独立未来事件捕获不是V19现有episode捕获；15m527个可评价唯一未来冲击中134个被前置风险窗口覆盖，不能冒称约99.8%的提前风险捕获。

## 因果与适用边界

未来标签只用当前bar结束后完整15/30/60分钟收益，不含当前正在形成的bar、不跨午休/隔夜。各H评分39770/33950/22310行，时间可行网格覆盖97.6190%/97.2222%/95.8333%。日初缺参考和未来缺窗口不补零；15:00因没有完整日内未来窗口不评分，其他陈旧观察按原样保留，不事后删样本。

Causal指当时可得、单边计算，不代表干预因果。NORMAL非安全保证、UNSAFE非看空、UNAVAILABLE非NORMAL。历史available_at仍是检索时钟；D2观察新鲜度限制与理想15秒提前量的假设性质不变。原冻结概率不重命名为D3的新墙钟概率。

## 真实执行位置与证据

D3统计、24项测试、治理/编译及独立复核在本会话；Actions只做12份已核验旧5m数据的格式转换，成功run34623937960/artifact10273059875，不是D3统计run。一次转运401和一次拟合前ISO8601解析失败均已记录，无统计择优重跑。

独立核验全部96030条评价标签，尾部零差异，log-RMS最大差2.083e-12，保存损失零差异；20个新增历史特征真实前缀扰动检查通过。模型Validation前后SHA256 f5a33a71969a18f2e7aa0aad45cd83903943d86962f2a92f5206e348667a2db0。完整结果包、系数/预测/块统计及哈希见回执和REPRODUCE.md；不声称本地FactorLab/DataHub、完整仓库、线上服务或策略经济验收通过。

## 下一方向，不混作已执行

保留V19/D2为因果描述与状态组织基线，不继续挤三状态识别率，不把D3失败解释成不需要实用评价。

下一合理工作：**独立预注册连续风险强度属性的实际用途评价**，保留状态作为描述轴，检验增量是否来自现有实时数值。B3对B1的描述性log-RMS改善约1.91%/2.75%/2.88%仅是动机，不是D3注册晋升路径，不据此宣布通过。D4尚未启动；不自动选阈值、映射交易动作或恢复旧router。

1%是本次事前研究门槛，不是所有下游应用的经济定律。后续必须有具体消费者问题、同信息基准和单独协议，不能改写D3。

## 数据与权限

Development2021–2023；Validation2024–2026-08-21按V2复用，不能直接拟合当前候选或称fresh OOS；本次实际评价到2025，不读取2026/new3s/保护期或BlackBox。V16的2026 final-5m证据不创建2026 realtime证据。
不接管Range/UpTrend/DownTrend父结构，不开发方向、开平仓、仓位、止损止盈、成本收益优化或payoff/router，不修改其他仓/live registry。

`v19_frozen=true`; `d2_supported=true`; `d3_executed=true`; `d3_practical_incremental_promotion=false`; `d4_started=false`; `v20_started=false`; `blackbox_queried=false`; `pnl_computed=false`; `production_authority=false`。
