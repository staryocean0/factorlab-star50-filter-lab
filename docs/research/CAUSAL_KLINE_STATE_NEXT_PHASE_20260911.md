# 权威叙事：状态上下文 + 连续风险程度 + 因果适用性

2026-09-11建立，2026-09-12更新D4实际结果。用户要求研究贴近行情演变与下游状态/策略分桶；数学统计决策由执行者负责。本仓不开发具体策略。

## 使命与所有权

将当时可知的K线风险属性及变化交给下游，使其能跟踪市场环境、研究策略适用条件，不只追求后验标签准确率。拥有波动/冲击/再冲击、三风险状态与恢复信息；父结构Range/UpTrend/DownTrend、具体策略、经济验收属于其他仓，不修改其他仓或生产registry。

## 四类结论分开

V19及V16—V18冻结识别证据、残差审计保持原样；不磨accuracy开V20。D1契约、D2 E15/CLOSE回放及既定范围消费者工程验收保持原样；完整网格97.9167%与日初缺参考、日末旧观察限制不变，不是实测feed或生产验收。

D3正式D3_INCREMENTAL_UTILITY_NOT_SUPPORTED：三状态表达相对历史基准的小增量没有达到原实际门槛；这个决定不被D4改写。

D4正式D4_COMPLETED_CONTINUOUS_ATTRIBUTES_PARTIALLY_SUPPORTED：当前连续I/V在15/30/60m log未来RMS、30m尾部上同时胜过简单历史H和同复杂度旧数值L；15/60m尾部未晋升。真实策略收益、回撤/成本和生产就绪仍未证明。

## D4为什么不是换一个名字挽救D3

D3的C对H改善线索已知，所以D4明确是可复用Validation的自适应后续评价，不是新盲验。协议先于本轮新比较发布；增加同列数/非线性项/正则、但不使用当前partial信息的L对照，先做2021–2022到2023前向开发检查，再冻结6个L与复用12个H/C探针，之后评分2024–2025。没有调V19、没有改D3门槛、没有重新选择更晚checkpoint。

C对L的15/30/60m波动预测误差减少1.60561%/2.45514%/2.80259%；30m尾部Brier相对1.10829%、绝对0.000549137，窄幅通过。15m尾部绝对幅度不够，60m尾部相对幅度不够。全部区间/年度/指数方向正也不能豁免失败门槛。区间下界>0不等于实际效应下界超过预设幅度；30m尾部不能称强预警。

通过的是固定信息集的预测损失比较，不是每个裸值/差分字段各自的独立因果贡献，不是超越全部原始价格历史创造新信息。delta_I/delta_V和3×3分位键仅为描述性消费者元数据，不单独晋升为预测/交易门控。

## 现在交付什么

优先组合三个相互独立标注的轴：V19三状态与转移（上下文）；当前I_t/V_t及确认历史对照（程度）；observation/decision/published/expiry、确认性质、新鲜度、缺失原因（适用性）。这些属性帮助下游研究环境变化，不直接规定看多看空、买卖、持仓或路由。

NORMAL非安全保证，UNSAFE非看空，RECOVERING非开仓许可，UNAVAILABLE非NORMAL。高分位不是“不能交易”。描述性事件高覆盖必须同时报告覆盖时段占用与无事件窗口比例，不把它与V19已有episode捕获率互换。

## 因果和时钟硬约束

Causal指单边可得、无未来泄漏，不是干预因果或首跳证据出现前的预测保证。当前未收盘final_state/close、未来路径、完整episode终点/长度只在评价侧；实时属性和未来评价表分开。E15与CLOSE分别留痕，不能回填、提前消费或无限跨过期沿用；缺失不补正常/概率0或1。

历史available_at保留检索语义；CSV为Asia/Shanghai墙钟，owner_realtime_assumption不等于实测接收延迟。日末观察旧于决策点的事实保留。原V16恢复时钟/目标不被改成D4新的墙钟概率。Development全期拟合分位边界不能冒称训练期当时已知的生产配置。

## 当前实际执行与直接下一步

D4全部会话执行，无Actions；23测试、20市场历史前缀、113928属性/96030未来标签及损失独立复核通过。完整证据见research/continuous_risk_utility_d4/，原D3 H/C预测逐行零差异。无原始3s重放或本地FactorLab/DataHub执行声称，完整仓库suite、真实feed与生产未验收。

下一步以CONSUMER_CONTRACT.md作为冻结起点，在本仓建立无交易动作样例消费者，检验D2双时钟状态与D4裸值的as-of接入、列白名单、缺失/过期、时区和版本。契约已记录，实际接入未执行，D5未启动。不急于开新预测器；先把已有有限支持转成能正确消费的研究接口。

## 数据与权威链

V2治理优先：Development2021–2023；Validation至2026-08-21可重复诊断、启发下轮Development，不直接拟合当前受测候选，也不是fresh OOS。本轮实际评价只到2025，重用旧5m CSV和D2账本；无2026、新raw3s、保护期、BlackBox、PnL或生产扩权。V16的2026 final-5m支持不创建实时3s证据。

CURRENT_RESEARCH.md → 本文 → research/continuous_risk_utility_d4/PROGRAM_STATE.json → RESULTS.md / DECISIVE_RECEIPT.json / EXECUTION_RECEIPT.json → PROTOCOL.md / FIT_FREEZE_RECEIPT.json → CONSUMER_CONTRACT.md → 原D3/D2/D1及V19—V16。

当前D4_COMPLETED_CONTINUOUS_ATTRIBUTES_PARTIALLY_SUPPORTED；D3原判不变；d5_started=false；v20_started=false；production_authority=false。历史入口快照4844ca27006bc187ee4d4ecb6262b903f4d798f0，原研究封存字节不改。
