# Current research entry

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
