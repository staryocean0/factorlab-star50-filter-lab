# 本地接续：当前没有本地研究执行待办

当前权威见 `CURRENT_RESEARCH.md`、`CONTINUE_HERE.md` 与 `research/activity_degree_incremental_utility_v1/`。

最新科学决定：**`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。该研究已在GitHub Actions完成Development fit/freeze与2024–2025 reusable Validation，不需要本地重跑。current M3相对current-I/V baseline有额外future-RMS信息，但没有证明相对等复杂度lagged-M3有≥1%的实际refresh增量，因此不进入D5 consumer或V19 state machine，也不允许调阈值救结果。

历史DataHub/reception线也没有新的本地工程待办。云端已经完成recorder、adapter、真实源码seam、9,492行handoff样本与41项测试的工程验收。D5R仍确认历史没有逐条真实本机`received_at`，不得从`available_at`、batch `ingested_at`、mtime、observation time或row order反推。

只有一种未来情况可能再次需要本地：**真实本机feed实际运行并产生future true-reception observations**。这些未来新行情/接收时间可能属于pending BlackBox-V1，必须先留在受保护本地层，不能直接上传公开GitHub/聊天或用于逐行调参，直到治理明确允许其用途。

因此当前不要让本地模型：

- 重跑M3/D4/V19研究；
- 再找历史received_at；
- 重新wiring已完成云端验收的adapter；
- 查询或上传受保护2026逐行subject数据；
- 做PnL/router/生产研究。

云端下一步是历史research backlog证据收口。只有后续某个合法科学步骤明确需要**GitHub没有、但本机独有**的数据时，才重新生成具体的数据查找/打包/上传任务给本地。

`local_research_execution_required=false`; `live_true_reception_rows_available=false`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
