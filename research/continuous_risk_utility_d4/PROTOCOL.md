# D4 — 连续风险属性的及时更新用途：独立后续协议

日期：2026-09-12；source main：4844ca27006bc187ee4d4ecb6262b903f4d798f0。
用户授权执行下一步；数学与统计决策已委托。此协议先于本轮 D4 新比较/拟合/分桶评价提交，但 D3 的 B3 对 B1 描述性结果已经知道。这是基于已知线索的可复用 Validation 后续研究，不是全新盲验，也不改变 D3 未通过的决定。

## 1. 具体消费者问题

下游在 E-15 已知上一确认状态、冲击年龄和历史波动时，读取当前连续冲击强度与波动比率，是否有足够幅度的未来风险信息增量？改善是否只是历史信息增加非线性表达的结果，而非及时更新本身？
保留 NORMAL/UNSAFE/RECOVERING 为描述轴，不修改 V19，不创建 V20、交易动作、方向预测、仓位或 payoff router。研究统计探针不是新生产风险预测器。

## 2. 不可变输入和数据角色

D2 ZIP SHA256：cf1c89e1412fd70f27992d9077af10dd7887a6843072e03ef808902bf5a84096；input manifest：aa31cf36b09a4708be98c6867ee1db81063855d0fa87885ec52685c3e5fdd2c3。
旧 5m CSV 转运 ZIP：cc37a181782ea25e61329285641739a2284e77a0f1a4c3672783d8ee23b78b84。
D3完整证据 ZIP：ee634995477c6a6c043ccb452175b142e20161d932e26a0dc391ff48e186b533；其中冻结探针 SHA256：f5a33a71969a18f2e7aa0aad45cd83903943d86962f2a92f5206e348667a2db0。
复用只读 D3 数据装配/标签/设计函数，runner Git blob：ea9f77bedd0b952385917015ef080800bfa596ba。逐项核对输入 SHA、原始数据出口身份和 D2 输出 manifest；无须重跑 V19/D2、重新读取原始3s或搬新数据。
2020仅预热；Development=2021–2023；Validation=2024–2025。本轮不读取2026、保护期或BlackBox，不修改现行V2数据治理。

## 3. 相同决策时点、未来窗口和缺失规则

完全沿用 D3 E-15 cohort 和 15/30/60墙钟分钟窗口：未来 n=H/5 段完整 close-to-close 收益从当前bar结束后开始，当前bar收益不算入结果，不跨午休/隔夜。两个endpoint为 log(max(未来收益RMS,1e-12)) 的MSE和 max(abs(未来收益)) >= 3*决策时已知bg48 的Brier。
三种比较器对每个H严格同样本；不同H不冒充同一survival cohort。日初缺参考明确不可用；没有未来窗口不是负例。15:00端点无法提供日内完整未来窗口；其余陈旧观察全部保留，按<=15秒/>15秒描述但不事后删除。理想15秒发布与观察新鲜度都不是实测feed延迟。

## 4. 固定三种信息集，控制表达复杂度

H：原D3 B1，上一确认状态、确认冲击年龄桶、指数/日内slot以及简单历史波动。直接复用D3冻结系数，不改设计。
C：原D3 B3，H再加 a=log1p(E15 shock_intensity)、b=log(max(E15 vol_ratio,1e-12))，以及a²、b²、ab；五项及其与上一确认三状态的交互。直接复用D3冻结系数。这些是已见证据的明确复用，不是本轮独立发现。
L：复杂度匹配的旧信息对照，使用与C完全相同的列数、五项展开和交互，但替换为仅由已确认收益产生的两个数值：I_lag=abs(最近已确认有效5m收益)/bg48_t；V_lag=pstdev(最近12个已确认有效5m收益)/bg48_t。共同分母bg48_t在E15之前已知。滚动有效收益允许跨日，但不造跨夜收益。L不使用当前partial价格；不能把当前final close或当前return放入L。
L与C是相同函数复杂度、不同信息更新程度的对照，不是声称信息集合完全相等。任何状态/数值都是价格历史的确定变换，不会凭空创造超越其完整原始信息的新信息。
所有新探针采用D3固定ridge规则：Development列均值/总体标准差标准化，截距不惩罚，mean squared error + 0.01*sum(beta²)；二元输出截到[0,1]。不搜超参数、horizon、阈值或特征。

## 5. 执行顺序与Development前向检查

先在2021–2022拟合H/L/C共18个探针，仅对2023做前向Development检查；这是开发期诊断，不是fresh OOS，不据其结果改规格。
随后仅拟合6个L探针于2021–2023，并复用原D3的12个H/C探针。所有系数、列名、标准化参数、代码/协议身份和分位边界先落盘，发布 FIT_FREEZE_RECEIPT 后才执行本轮Validation新比较。即使Development符号不支持也允许完成注册诊断，但相应endpoint不得晋升。
原D3模型字节在本轮前后必须不变。新模型身份在Validation前后必须不变。

## 6. 12项固定比较和晋升规则

固定族：C对H、C对L × 2 endpoints × 3 horizons=12项；主要用途结论必须对同一endpoint/H同时通过两种基准，不可只选较弱基准通过。C对H已有描述性线索须明确披露。
不确定性沿用同日两指数共同的5交易日非重叠配对块，按年分层、5000次bootstrap，seed=20260913；12项Bonferroni双侧区间分位0.05/(2*12)。固定20交易日块作为敏感性，不能代替主区间。不确定性是有限块样本的近似，也不消除跨轮自适应使用Validation的选择影响。
每项门槛：Validation>=10000、Development>=20000、每年度/指数>=1000；尾部Validation正例>=100；相对损失减少>=1%；尾部还需绝对Brier减少>=0.0005；调整后5日块区间下界>0；2024/2025和两指数分别非负；时间可行网格覆盖>=95%；2023前向Development比较符号非负。所有门槛按本协议不变。
同一endpoint/H两种比较全部通过，才可标注 D4_CONTINUOUS_REFRESH_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS；均无联合通过则 D4_CONTINUOUS_REFRESH_UTILITY_NOT_SUPPORTED。部分通过逐项列明，不把某个horizon通过推广到全部目标。只对H通过意味着不足以排除表达复杂度解释。
1%和0.0005是本项目此次预设的实际幅度要求，不是经济收益门槛。无论结果为何，不改判D3、不获得生产或策略权限。

## 7. 面向下游的数值属性与描述性分桶

保留I_t、V_t、I_lag、V_lag以及delta_I、delta_V、D2原始状态/确认性质和时钟。训练期按指数分别对所有可用E15的I_t、V_t固定20%/80%分位（线性分位定义），组成3×3描述键 I_QLOW/QMID/QHIGH 与 V_QLOW/QMID/QHIGH，边界相等归入较低桶。不按未来结果选边界，不声称高分位等于应禁交易。
分位网格、裸值变化不作为额外模型输入，不触发晋升。输出全部9格的样本/占用、未来RMS、尾部比例、年度/指数/固定新鲜度切片；另报告唯一未来冲击事件去重覆盖及无尾部窗口比例。该描述无论漂亮与否都不能挽救主门槛。
实时属性交付表与未来评价表分开，缺字段保留UNAVAILABLE，分位表达是D4研究描述元数据，不是V19第四状态。验证期使用Development冻结边界；Development期分位表仅为训练描述，不冒充那些历史时点已部署该边界。

## 8. 验证、证据和执行位置

当前会话已具备D2/D3完整输入和numpy/pandas，所有计算、测试与复核在当前会话，不触发Actions、不声称本地FactorLab/DataHub执行。
必查：输入/旧模型身份、H/C逐行预测与D3已存预测一致、独立顺序历史缓冲验证L的两个属性、未来标签重算、全部保存损失重算、冻结模型不漂移、未来扰动不改变历史属性、当前/未来评价字段不能进入设计、同H同cohort、同日两指数共同block、全部失败与不适用记录保留。旧V19/D1/D2/D3源码和报告不改；记录实际命令、退出码、软件版本、源与产物SHA256。
参考方法说明：训练期预处理隔离见 https://scikit-learn.org/1.8/common_pitfalls.html ；时间序列块bootstrap背景见 https://bashtage.github.io/arch/bootstrap/timeseries-bootstraps.html 。本协议具体非重叠块方案与门槛是上述明确的项目选择，不称由文档推荐或保证。
最终按结果更新权威入口。V19保持冻结；v20_started=false；blackbox_queried=false；pnl_computed=false；production_authority=false。
