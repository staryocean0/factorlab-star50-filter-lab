# 当前任务：D4已完成，连续风险程度信息获得分目标支持

更新2026-09-12。使命不变：把当时可知的K线风险属性及变化交给下游，用于跟踪行情、环境分桶与策略适用性研究；本仓不开发具体交易策略。数学判断由执行者负责。

## 当前权威链

V2数据治理和BUCKET_SCOPE_REPAIR_20260909.md优先；方向见docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md。
当前状态：research/continuous_risk_utility_d4/PROGRAM_STATE.json → RESULTS.md → DECISIVE_RECEIPT.json / EXECUTION_RECEIPT.json → PROTOCOL.md / FIT_FREEZE_RECEIPT.json。消费者接续见同目录CONSUMER_CONTRACT.md。

**D4_COMPLETED_CONTINUOUS_ATTRIBUTES_PARTIALLY_SUPPORTED**。
D3的D3_INCREMENTAL_UTILITY_NOT_SUPPORTED保持原判，D2工程与V19识别证据保持原样。旧PROGRAM_STATE和旧报告中的“D4未开始”是历史状态，不是当前断点。

## D4实际回答

在固定E15，当前连续冲击强度/波动比率，是否比上一确认历史信息更有用？H是原D3简单历史基准；L是与当前数值C相同列数/非线性项/正则规则但仅使用已确认收益的对照。要求同一目标同时胜过H与L，不只选择弱基准。

| 目标 | H | 对H误差减少 | 对L误差减少 | 联合结论 |
|---|---|---:|---:|---|
| log未来RMS | 15m | 1.91064% | 1.60561% | 支持 |
| log未来RMS | 30m | 2.74830% | 2.45514% | 支持 |
| log未来RMS | 60m | 2.87781% | 2.80259% | 支持 |
| 未来尾部Brier | 15m | 1.10989% | 1.03193% | 绝对改善不足，不晋升 |
| 未来尾部Brier | 30m | 1.20514% | 1.10829% | 窄幅支持 |
| 未来尾部Brier | 60m | 0.96885% | 0.89253% | 相对改善不足，不晋升 |

这是预测损失改善，不是收益或风险本身下降。4/6目标组合、8/12单独比较通过。全部年度/指数方向正，12项调整5日块区间及20日敏感性区间正。30m尾部只是pooled点估计窄幅达到门槛，不能声称每切片或区间下界都达到实际幅度。

协议ef865110aee6c1c3b300d27c38a578c2b8882a67先于本轮新比较；模型冻结643671b7ca6bf0e7a0c3a975a383c8029a8ee92d先于Validation。H/C已有D3描述线索和系数被明确复用，新增复杂度对照及2023前向开发检查不刷新数据独立性。**这是自适应可复用Validation证据，不是fresh OOS。**

## 当前用途定位

交付三轴：V19状态上下文 + 连续I_t/V_t程度信息 + 确认/时钟/新鲜度/缺失约束。D4只支持固定信息集在指定风险目标上的有限增量，不给三状态改判，不把所有分桶都升级为预测门控。
delta_I/delta_V和Development固定3×3分位键仅是描述字段，未单独证明预测或交易效用。高分位窗口可能覆盖更多事件，也占用大量时段且多数没有后续尾部；不能据此直接禁交易、看空或降仓。

## 实际执行与边界

D4全部在本会话执行，无Actions。23项测试、20真实历史前缀检查、治理/编译通过；独立重算113928可用属性与96030未来记录，尾部/保存损失/块汇总零差异；原D3 H/C逐行预测零差异。模型SHA256 30edb34a68bd7b6010f57128177d5500558b7af1803cc8b279abeb9df80ddd18前后不变。

2020仅5m预热，Development2021–2023，Validation2024–2025。15/30/60m行数39770/33950/22310，同H同cohort。当前bar不进入未来标签，不跨午休/隔夜；缺窗口不补零；日初缺参考、日末新鲜度和其余陈旧观察保留。属性表116352网格，2424不可用。CSV时区Asia/Shanghai，理想15秒发布不是实测feed延迟。原V16概率目标不冒充D4未来墙钟目标。

## 直接下一步

按research/continuous_risk_utility_d4/CONSUMER_CONTRACT.md建立本仓无交易动作的样例消费者，对状态+裸值进行有界as-of接入验收。契约已记录，真实接入未执行；不要重新拟合或为了版本号开模型。D5未启动、V20未启动。

保留V16—V19、D1/D2/D3原代码/surface/报告/receipt。旧入口快照在4844ca27006bc187ee4d4ecb6262b903f4d798f0，不删除历史。
V2允许重复Validation与Development迭代，不拟合当前受测候选、不称fresh OOS。本轮无2026、newraw3s、保护期、BlackBox、PnL；不接管Range/UpTrend/DownTrend，不开发买卖/仓位/止盈止损/payoff/router，不改其他仓或生产registry。production_authority=false。
