# Current research entry

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
