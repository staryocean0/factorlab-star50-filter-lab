# Current research entry

## 当前：交接云端进行科创50/中证1000底层K线风险研究

先读[2026-09-07交接说明](docs/handoff/cloud_risk_gate_20260907/HANDOFF.md)与[数据说明](docs/handoff/cloud_risk_gate_20260907/DATA.md)。用户将任务扩展为两指数的跨尺度波动、聚集/孤立冲击与因果风险分桶；当前不做交易/期权，V2不改。15项文献全文已补齐并随包上传。DataHub新离线导出只开放截至2025年的两指数3秒，旧线上合同不变。以下均为既有研究成果或历史任务，不能覆盖当前范围。

## 最新：因果未来波动工具V1已完成历史检验

[结果与图形](docs/research/causal_volatility_tool_v1/result.md) → [接口与工作流](docs/research/causal_volatility_tool_v1/workflow.md)。未来波动水平预测有改善，但普通时段突变预警覆盖不足；不授交易路由，V2不变，无2026读取。

## 最新：两指数同时间同级别尾部与事前条件研究完成

[结论与图形](docs/research/tail_distribution_v1/result.md) → [工作流](docs/research/tail_distribution_v1/workflow.md)。1m/5m共同绝对与标准化尾部、时间聚集、事前波动条件及固定概率诊断已完成；高波动可识别很多绝对大幅变化，但科创50大且异常有显著非高波动部分。当前未形成交易路由，V2不变，无2026读取或生产权。

## 最新测量：秒级分辨率与中证1000固定迁移

[结果与图形](docs/research/resolution_transfer_v1/result.md) → [复现工作流](docs/research/resolution_transfer_v1/workflow.md)。两只科创50ETF2024/2025真实秒观测显示更细网格原始ER方差下降，但未识别交易最优分辨率；固定V2迁移中证1000的2021—2025研究已完成，无重选参数、无2026读取或生产权。V2仍是当前策略版本，因果路由尚未建立。

## 当前：V2单笔质量优先研究与回测完成

[结果与图形](docs/research/half_day_slope_union_v2/result.md) → [工作流](docs/research/half_day_slope_union_v2/workflow.md) → [冻结参数](docs/research/half_day_slope_union_v2/selected_policy.json)。2021—2023有界324身份开发后冻结，2024/2025逐年原样检验；V2相对V1提高平均单笔与整体Sharpe，2025总收益/Sharpe仍有代价。AI自加交易次数硬门的开发后修订已公开。指数方向费用代理模拟，非真实ETF/期权账户；2026未读，无生产权。下述V1为前序原型。

## 当前：半日低通1分钟斜率并集原型（用户最新改版）

[白皮书](docs/research/half_day_slope_union_v1/whitepaper.md) → [工作流](docs/research/half_day_slope_union_v1/workflow.md) → [机器合同](docs/research/half_day_slope_union_v1/contract.json)。接管原线程 `01a074d4-b841-7dc2-9cc0-2063f63de807` 最后任务：同一科创50半日低通策略改为原生1m、120交易分钟截止、入出场各1—5根相关性校正斜率并集、多空镜像。首版仅合成验证，经济参数未选优；2026未读取。旧5m限制和下述任务优先级由本次用户明确改版取代，历史工件保持可查。

## 最新：三个因果可得方案及组合已验证（2026-09-06）

读[三方案报告](docs/research/three_proposals_v1/report.md)。固定原满单位账户，A近期Q12集中度否决、B反向实体超过前序1σ否决、C原L3/P48→P96原生15m通道优先及组合，共9个身份、五年顺序审阅完成。原86.7566%年化/14.3238%MDD复现；88测试、158工件同源重放字节一致。

未支持Q12非重叠窗口的持续聚集；A有成本敏感型筛选进展，但零费年化86.76%→73.18%而MDD仅14.32%→13.97%，原零费tradeoff不强。每边万2代理下A年化41.34%→43.54%、MDD18.01%→15.18%、交易3482→2346；2024/2025仍落后，不能称稳定解决。B证据弱、AB并集并不优于A，C及组合扩大MDD。A/B交集82笔是后验弱桶线索，未追加交集策略或计算其MDD。真实ETF/期权经济验收未完成；无新策略晋级、2026读取或生产权限，顶层目标仍开放。以下为前序研究记录。

## 当前：用户波形偏斜/急起急落猜想已完成一轮验证（2026-09-06）

读[波形机制报告](docs/research/wave_shape_v1/report.md)。固定原因果LP12、sigma48与原满仓账户，450个合成例和五年3244个价格周期检验完成。357组相近周期/幅度/波动/趋势匹配中，位移集中组capture平均低7.25个百分点，五年同向；两个8项maxT修正参照均0.0005。支持急起急落的部分机制，但不支持简单左右偏斜符号规则；半高宽没有通过，偏度匹配证据弱。相同频谱功率、相同波动门槛，只改变相位也可由赚转亏；这是固定算法机制证据，不是整个真实回撤的因果解释。78测试、年度表和统计重放通过。无新否决规则、账户修改或2026读取，降回撤顶层目标未完成。当前产物`artifacts/wave_shape_v1p2`，v1/v1p1研究实现事故原样保留。

## 当前纠偏：回到原满仓策略逐笔回撤归因（2026-09-06）

用户指出前轮固定单位账户不能替代原满仓策略目标，且总体关联不能代替逐笔归因。当前读[原始回撤逐笔报告](docs/research/original_drawdown_trade_audit_v1.md)：5m+0的14.3238%事件50个持仓片段已全部对账，并人工解释首段反手链、同阶段盈利和隔夜跳变反例；5m+2的19.7519%事件292个片段已单独列账。完整逐笔根因尚未全部解决，不能把机械MFE/回吐标签称为已完成因果归因。信号、仓位、原始账户不改，无新回测、2026读取或生产权限。下述固定数量实验不具有原满仓降回撤成果的权威。

## 当前：条件分桶首轮账户研究已完成，未晋级策略（2026-09-06）

读[本轮报告](docs/research/conditional_bucket_v1/result_v1.md)与[控制器验收](artifacts/conditional_bucket_accounts_v1p3/controller_acceptance.json)。五个冻结否决条件、三个载体路线、18个2025完整账户已运行；92个工件隔离重放字节一致，70项测试通过。ETF无条件同时改善MDD与平均单笔净收益；期权三个条件相对改善，但全部账户仍亏损，不构成可采用策略或加杠杆依据。ETF推进不足条件仅保留为单笔质量进展。先条件分桶、后微调、仓位最后不变，无2026行情研究或生产权限。

现货v1.1继续有效。新发现588080期权历史条款在2025-10-17生效前已被调整后状态回填，该期权复制车道隔离；不影响本轮588000主样本和计入分红的588080 ETF。见[DataHub修复提示词](docs/research/conditional_bucket_v1/datahub_terms_repair_prompt.md)，`bd://fl-vcyb3`。主目标`fl-qg35a`仍未完成。以下均为历史阶段记录，不是当前调度入口。

## 历史：历史盘口返修已验收，恢复条件分桶研究准备（2026-09-06）

[返修独立复验](</home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab/docs/user/star50_datahub_reacceptance_v1_20260906.md>)通过F1/F2/E1。现货使用v1.1，期权版本不变；当前精确绑定为[数据绑定](docs/research/conditional_bucket_v1/datahub_binding_v1.json)。959条盘后区间已修、价量未变，11个读取门用例和五日21字段重放通过。原缺源日期保留，无2026或生产授权。后续仍按最大回撤/单笔净质量双目标，先条件桶和否决，后调参，仓位最后；本次未运行策略回测。以下待返修条目降为历史。

## 最新：历史盘口交付已到，独立验收待返修（2026-09-06）

期权627日、现货483日数据已到，1110文件全量哈希/行数/日期范围与当前精确grant通过。验收发现读取工具未实际执行授权检查，以及959条现货盘后反向有效区间；期权两个样本的全字段重放证明也待补。详见[验收报告及返修提示词](</home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab/docs/user/star50_datahub_acceptance_v1_20260906.md>)。整体changes_required，正式双载体回测未准入；下文“等待历史交付”是前序记录。

## 当前任务：条件分桶/交易否决，等待历史盘口交付（2026-09-06）

顶层目标见[用户合同](docs/research/conditional_bucket_v1/owner_contract.json)：降低最大回撤、提高平均单笔净质量，先条件筛选，再微量调参，仓位最后。8个因果候选测量已准备，但未形成有效桶或新策略。用户要求先定位更长盘口：已确认原始归档存在、DataHub深历史物化/注册/供应链未闭合，详见[诊断](docs/research/conditional_bucket_v1/datahub_diagnosis.md)与其中的转发提示词。正式双载体回测未开始，不用旧零成本指数账户替代。

## 当前：第五轮连败与频段机制已完成（2026-09-06）

读[第五轮报告](docs/research/streak_mechanism_v1/report.md)。平均胜率38.40%、最长12连败没有超出声明的随机参照；频段属性对每笔收益的关系比对胜率更稳定。第五轮重新绑定原包实际源码并从原行情重建，来源/年度链/数值复验通过，58项测试通过。第四轮历史哈希缺口仍保留，不能因本轮通过而改写旧清单。无新策略、无2026读取、无生产权限，第六轮未开。

## 本地接管核验补充（2026-09-06）

先读[LOCAL_TAKEOVER.md](LOCAL_TAKEOVER.md)。云端增量已完整回迁，54项测试和前三轮封存校验通过；第四轮原策略路径及统计表复现一致，但严格验证器因`filters.py`/`backtest.py`冻结哈希不匹配而失败。下文旧“本地本轮校验通过”保留为云端交接记录，不代表本地来源验收通过。两份缺失哈希字节尚未找回，旧协议/manifest不改，详见本地报告与`bd://fl-mmbk4`。第一阶段未启动新研究。

## 已执行：第四轮固定策略跨尺度根因（2026-09-06）

最新报告：`docs/research/cross_scale_root_cause/report.md`；数学定义和完整
40项统计参照见同目录whitepaper与artifacts/cross_scale_root_cause。
本轮完成用户“同意请执行”指令，不再只是下一会话任务书。

- 原始5m+0满仓账户逐点复现，未降仓，未增加交易规则。年化86.7566%、MDD14.3238%。
- 五年/五偏移重复支持：低日内路径效率、同日快变化强、门槛相对工作波幅大
  与更差同日捕获率有关。慢/工作速度更高总体有利，不支持“低频越强越坏”。
- 1192日、20属性×2结果经循环错位与20日分块maxT参照；完整失败项保留。
  相同属性的前一日因果版本40项均未通过。没有发布因果降回撤策略。
- 固定算法84个无噪声合成例显示短往返与响应滞后会产生规律亏损；7种频段
  数学扰动与此相容，但非真实市场反事实、非可实现收益、非独立因果贡献。
- 最大持续回撤15日下降、46日恢复；恢复的正负收益对消87.65%。第7事件
  50日恢复对消91.76%，尚无统一低频恢复开关。快速跳变第2事件是另一类失败。
- 日效率低的两格贡献前十峰谷净log损失78.5%（剔除快速跳变事件88.6%）；
  这是事后选定窗口的互斥记账占比，不是因果解释比例。强趋势回撤仍有反例。
- `available_at`仍按用户澄清的历史获取语义；2026未参与属性/参数发现。
  2021—2025持续为已消费，五个年度已依次审查封存。生产权限false。
- 本地本轮校验通过；GitHub CI在任何步骤启动前失败，重试一次仍同样。
  原因未确认，不能宣称远端CI通过；见`docs/research/cross_scale_root_cause_ci_closeout.md`。
- 校验：`python scripts/validate_cross_scale_root_cause.py`；完整数据重放另加
  `--data-dir artifacts/drawdown_material`。不重写本轮或前三轮manifest。
- 后续若继续，先冻结“盘中可得的推进/响应滞后/回吐”有限测量与验证预算；
  不把本轮后验门槛直接当交易开关，不以降仓代替解释，不重新开放2026。

## 用户最新澄清与下一会话任务（2026-09-06）

首先阅读 `docs/governance/available_at_owner_clarification_20260906.json`
和 `docs/user/next_session_drawdown_root_cause.md`。它们修正此前对字段的
解释，并取代下述历史轮次对“下一步优先任务”的安排。

- `available_at` 是历史数据可获取时间。用户已明确：盘中实时数据实时获取。
  不得将15:30历史字段当成盘中延迟或据此判定盘中不可用；撤回由这一
  字段单独推出的可得性缺口。旧回执中的相应标记是已被取代的历史解释。
- 下一会话追查固定原策略持续回撤的根因，映射至不同回看期、不同频段
  的K线属性及其关系。允许后验、非因果的解释性分析；先判断是否存在
  可重复机制，再另行标记哪些属性当时可得。
- 不以降仓位、仓位择时或更好MDD作为本轮目标。固定原基线、持仓规模
  与账户口径，解释同一批亏损；不把ETF库存/执行映射审计替代为K线根因。
- “低频有关”与“可能只是巧合”均须检验，不能预设结论。分析峰至谷及
  谷至恢复，比较盈利/普通区间，并控制时间依赖、重叠样本与多重尝试。
- 2021—2025为已消费开发材料，2026不用于选参或本轮属性发现。保留5分钟
  工作图与本仓库主题。此条是下次会话交接，本次未运行新实验。

## 历史研究索引（保留，不作为当前任务优先级）

This entry follows the immutable `CONTINUE_HERE.md`, which is hash-bound by
the second-round research manifest. Preserve that file and both old bundles.

1. Third round: `docs/research/market_admission/report.md`.
   Official realtime STAR50 publication exists since2020-07-23; historical
   DataHub first/revised versions and actual reception clocks remain unproven.
   Official historical-data route identified; external market files received:0.
2. Cash ETF mapping is mechanically different:54.22% of frozen primary minute
    targets are short. After clipping shorts to cash, T+1 inventory still misses
    targets27.93% of minutes for baseline and29.36% for slow-conflict half.
    Both retain2 abstract locked units at the2025 terminal liquidation attempt.
    These are optimistic inventory diagnostics, not tradable PnL or MDD.
3. Read `docs/research/market_admission/data_request.json` for exact provenance,
    history, quote and account evidence needed. STAR50 ETF options did not exist
    before2023-06-05; no option strategy implemented. Do not backfill that period.
    Validate `python scripts/audit_market_admission.py --validate`.
    All five new annual sessions are sealed; do not overwrite them.
