# 当前任务：D5样例消费者已验收，转入有界外部研究接入

更新：2026-09-12。使命：把当时可知的K线状态、连续风险程度与适用性信息交给下游，支持行情跟踪、环境分桶和策略适用性研究。本仓不开发交易动作。

## 当前权威链

V2数据治理和BUCKET_SCOPE_REPAIR_20260909.md优先；方向见docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md。
当前执行状态：research/state_degree_consumer_d5/PROGRAM_STATE.json → RESULTS.md → EXECUTION_RECEIPT.json / INDEPENDENT_VERIFICATION.json → PROTOCOL.md / SOURCE_IDENTITY.json。
可运行例子与回迁：同目录REPRODUCE.md、example_consumer.py、LOCAL_HANDOFF.md。旧D4/D3/D2/D1的PROGRAM_STATE是各阶段封存状态，不覆盖本入口。

**D5_BOUNDED_RESEARCH_CONSUMER_ACCEPTED_EXTERNAL_INTEGRATION_PENDING。**
本仓样例接入已实际执行并通过；外部FactorLab/DataHub或策略研究进程尚未接入，生产未授权。不是D5待执行，也不是又开新统计模型。

## D5完成情况

232704条D2 E15/CLOSE事件完整接入；116352条D4 E15属性一对一匹配。每种时钟113928可用、2424原不可用均保留。源状态、转移、确认性质、时间、裸值、概率及缺失传递零差异；D4增强数值最大差0。
930816次固定边界查询与独立选择器逐项一致；20个消费者历史前缀检查、40项合成测试、治理/编译及两个CLI样例通过。全部在当前会话执行，使用标准库，无Actions、模型拟合、新行情或统计Validation。

E15只接同事件D4裸值和描述性lag/delta；CLOSE只用D2确认字段，不跨时钟复制E15增强或推广D4效用。numeric_bucket不交付，不把训练期分位配置当历史部署事实。V16概率保留原目标与可用性门控，不生产新概率。

published_at与received_at分开，收到前不能消费；晚到不能回填；过期/最新不可用不能回退旧状态；午休/日终明确无当前快照。上午确认可按原D2有效期作为午后首个E15前的上下文，但不是新的午后观察。

四种结果：AVAILABLE、STATE_ONLY、UNAVAILABLE、NO_CURRENT_SNAPSHOT。缺失不是NORMAL，空概率不是0/1。日初缺参考与日末旧观察保留，最大观察年龄165秒；新鲜度不等于实测网络延迟。默认即时收到与2秒延迟样例均为历史/合成假设。

## 不被D5改写的科学结论

V19：冻结参考语义下的风险状态识别支持，残差路线关闭，不启动accuracy微调V20。
D2：因果双时钟工程回放支持，不代表所有未来风险被提前识别。
D3：D3_INCREMENTAL_UTILITY_NOT_SUPPORTED原判保留，三状态小增量未达原实际门槛。
D4：连续I/V仅对15/30/60m log未来RMS、30m尾部在H/L双基准下获有限支持；15/60m尾部未晋升，delta与分位门控未独立验收。这是已知线索后的自适应可复用Validation，不是fresh OOS。
D5：消费者字节/时钟/来源接对，不提高D3/D4证据等级，不证明策略收益。

## 下一项实际工作与停止线

按research/state_degree_consumer_d5/LOCAL_HANDOFF.md进行外部研究消费者回迁和独立进程验收；任务CL-D5-RESEARCH-CONSUMER-20260912。回执必须说明实际本地环境、commit/输入SHA、命令/退出码及差异。没有可调用的本地执行通道，不声称自动派发或已回迁。

本仓此阶段完成，保持冻结维护；不为版本号启动D6或V20。若尚无实际外部消费需求，不需要继续造模型。真实feed、持久化/断线重连/修订策略、完整仓库suite和经济验收均未通过本次验收。

## 数据、权限与历史

Development2021–2023；V2 Validation至2026-08-21可复用，不能拟合当前受测候选或称fresh OOS。D5只消费原2021–2025封存派生产物；无raw3s/5m重读，无2026、保护期、BlackBox、PnL或生产扩权。V16的2026 final-5m覆盖不生成2026 realtime证据。

NORMAL非安全保证、UNSAFE非看空，状态/强度不是买卖许可。不接管父结构Range/UpTrend/DownTrend，不开发仓位/方向/payoff/router，不改其他仓或live registry。
原V16—V19与D1—D4代码、surface、报告、回执原样保留；原入口在11ade25e0ea7a25321955015e327854915cc211a。数学判定继续由执行者负责，权限不扩大。
d5_completed=true；external_consumer_accepted=false；d6_started=false；v20_started=false；production_authority=false。
