# 权威叙事：状态上下文 + 连续风险程度 + 因果适用性

2026-09-11建立；2026-09-12更新D5实际验收。用户要求贴近行情变化与下游环境分桶，而非只追求后验标签准确率。本仓拥有K线风险属性，不开发具体交易动作；数学判断由执行者负责。

## 使命与证据边界

在当时可知的信息中识别和表达状态、程度、变化及可用性，使下游研究能正确跟踪行情条件。父结构Range/UpTrend/DownTrend、策略动作与经济验收仍属于相应其他仓，不改其他仓或live registry。

V19/V16—V18识别及恢复基线冻结，残差优化路线关闭；不为accuracy开V20。D1契约与D2因果双时钟回放支持只是工程证据，不等于全部未来风险已能提前发现。
D3未获实际增量晋升的结论原样保留。D4只对15/30/60m log未来RMS与30m尾部在H/L对照下获有限支持，15/60m尾部不晋升；30m尾部窄幅通过不能夸大为强预警。D4是已知D3线索后的自适应可复用Validation，不是fresh OOS。delta与分位门控没有独立效用验收。

## D5已经打通本仓样例消费链

本次实际实现D2 E15/CLOSE状态到无交易动作消费者的接入。232704事件、116352个E15增强完整保留；状态/转移/确认性质/裸值/概率/时钟零差异，增强值最大差0。930816次边界查询与独立参考选择器匹配，40项单元测试与20个历史前缀检查通过。工程通过不提高D3/D4预测效用等级。

E15接D4当期I/V和描述性lag/delta；CLOSE只接D2确认数值，不复用E15增强或跨时钟推广D4结论。已有V16概率保持原目标和不可用规则；不新增预测器或概率服务。不输出训练期拟合的numeric_bucket，避免把研究编码变成未经验证的门控或历史部署事实。

消费者将published_at与received_at分开，按已发布且已收到的信息查询。临时快照与确认记录分开保存，不回写。完全重复幂等、冲突重复拒绝；最新记录不可用/过期不回退，迟到增强不倒填。
AVAILABLE、STATE_ONLY、UNAVAILABLE、NO_CURRENT_SNAPSHOT各有明确语义；NORMAL非安全保证，UNSAFE非看空，缺失非NORMAL，空概率非0/1。高强度不意味着禁止交易。

## 因果与适用性不妥协

Causal指单边计算、信息不晚于决策，不是干预因果。未来标签、当前未确认final_state/close和完整episode终点不入消费字段。D4源码/包身份被核对，不靠调用者自报版本证明算法正确。

CSV按Asia/Shanghai解释，历史available_at仍是检索时间。原日初每时钟2424条不可用和日末旧观察保留，最大观察年龄165秒；无新鲜度删样本。午休关闭，午后首个E15前可依原D2有效期读取上午确认上下文，不能当作午后新观察；日终不跨夜沿用。

样例零/2秒接收延迟已实际检查，但延迟是合成参数；owner_realtime_assumption不是实测feed。软件现在实现不等于2021年已部署。当前只支持既有2021–2025封存消息的有界研究消费，不是泛化实时数据总线。

## 下一阶段：交接真实外部研究消费者，而非继续造版本

D5本仓验收已经完成。下一项是CL-D5-RESEARCH-CONSUMER-20260912，在真实本地研究进程中按LOCAL_HANDOFF.md进行回迁、独立复核与接入，并记录环境、commit/输入SHA、命令/退出码和全部差异。本会话没有自动派发或执行FactorLab/DataHub，不冒称生产通过。

没有实际外部消费需求时，冻结维护即可；不为了版本号启动D6/V20。生产消息认证、接收日志、长期持久化、断线重连、修订处理、完整仓库suite、动作映射及经济收益必须另行验收。

## 数据、执行与权威链

D5全在当前会话执行，标准库实现，无Actions、新行情、raw3s/5m重读或统计拟合。首次导出受工具执行时限中断，仅调gzip压缩级别及进度输出后完成，接口/输入/门槛未改；实际过程见回执。
V2治理及研究桶边界不变：Development2021–2023；Validation至2026-08-21可复用，不拟合当前受测候选、不称fresh OOS。本次只使用已有2021–2025派生产物。V16 final-5m的2026支持不创建实时3s支持，无2026/保护期/BlackBox/PnL或生产扩权。

CURRENT_RESEARCH.md → 本文 → research/state_degree_consumer_d5/PROGRAM_STATE.json → RESULTS.md / EXECUTION_RECEIPT.json / INDEPENDENT_VERIFICATION.json → PROTOCOL.md / SOURCE_IDENTITY.json → REPRODUCE.md / LOCAL_HANDOFF.md → 原D4/D3/D2/D1及V19—V16证据。

当前D5_BOUNDED_RESEARCH_CONSUMER_ACCEPTED_EXTERNAL_INTEGRATION_PENDING。原封存证据字节不改；旧入口在11ade25e0ea7a25321955015e327854915cc211a。d6_started=false；v20_started=false；production_authority=false。
