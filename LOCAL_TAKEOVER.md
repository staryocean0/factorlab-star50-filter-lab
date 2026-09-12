# 本地接续：当前没有本地研究执行待办

当前权威见 `CURRENT_RESEARCH.md`、`CONTINUE_HERE.md`、`research/signed_risk_asymmetry_utility_v1/` 与历史backlog closeout。

最新科学决定：**`SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

本轮 signed-history V1 已在云端完整执行、冻结并收口：前12个有效已完成5m收益的正负结构，在 pooled 60m future-RMS 上相对 C / M 分别出现 +1.35593% / +1.02822% 点估计，但 adjusted CI 跨0，而且 STAR50 为负、CSI1000 为正，所以不构成跨指数稳健 promotion。协议禁止事后只保留CSI1000，也禁止窗口/decay/skew/downside-count等救援。

这项研究**不需要本地模型重跑或补数据**。完整 decisive evidence 已在 GitHub research 目录持久化；D5 不新增 signed-asymmetry field/gate，V19、D4、D5 authority 均不变。

前置 trajectory/shock-memory/cross-index/M3 路径也已经云端收口；历史research backlog仍是 **remaining executable legacy backlog=0**。不要让本地模型去重跑 V7/V8/V9/V10、first-shock、RMR、V11、v0.6.17、old router，或对已关闭的 M3 / shock-memory / trajectory / signed-asymmetry 做参数救援。

历史DataHub/reception线同样没有新的本地工程待办。D5R仍确认历史没有逐条真实本机`received_at`，不得从`available_at`、batch `ingested_at`、mtime、observation time或row order反推。

只有一种未来情况可能再次需要本地：**真实本机feed实际运行并产生future true-reception observations**。这些未来新行情/接收时间可能属于pending BlackBox-V1，必须先留在受保护本地层，不能直接上传公开GitHub/聊天或用于逐行调参，直到治理明确允许其用途。

因此当前不要让本地模型：

- 重跑 signed-asymmetry / trajectory / shock-memory / cross-index / M3 / D4 / V19；
- 再找历史received_at；
- 重新wiring已完成云端验收的adapter；
- 查询或上传受保护2026逐行subject数据；
- 做PnL/router/生产研究。

只有后续某个**新的、合法、独立的因果风险机制**明确需要 GitHub没有、但本机独有的数据时，才重新生成具体的数据查找/打包/上传任务给本地。若没有这种机制，维持当前authority即可。

`local_research_execution_required=false`; `signed_asymmetry_local_rerun_required=false`; `historical_research_backlog_closed=true`; `remaining_executable_legacy_backlog=0`; `live_true_reception_rows_available=false`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
