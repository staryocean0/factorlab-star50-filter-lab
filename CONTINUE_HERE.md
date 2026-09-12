# 接续入口：D5样例消费者已通过；历史真实接收时钟不可用

当前状态：**D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED**。

不要重做 D5，不重拟合 V19/D3/D4，也不要再把“外部 reception 验收待执行”理解为历史数据仍可完成。先读：

1. `CURRENT_RESEARCH.md`
2. `research/reception_clock_adjudication_d5r/PROGRAM_STATE.json`
3. `research/reception_clock_adjudication_d5r/RESULTS.md`
4. `research/reception_clock_adjudication_d5r/DECISIVE_RECEIPT.json`
5. `docs/ops/receipts/star50_true_reception_raw_20260912/README.md`
6. `docs/ops/receipts/star50_true_reception_raw_20260912/SOURCE_INFO.json`
7. 原 `research/state_degree_consumer_d5/`、D4/D3/D2/V19 证据。

## 已确定事实

本地对 DataHub / FactorLab / recording 存储做了只读检索，没有找到 `000688.SH`、`000852.SH` 的逐条真实本机 `received_at`。Release `star50-true-reception-raw-20260912` 的 ZIP 为 5446 bytes，SHA256 `63badecf70405452674831f41a6aef0de174ca8d10b113fc32c91a8e1ca24cf0`，quote rows=0。

不能用 `available_at`、batch `ingested_at`、mtime、下载时间、市场观察时钟或 row_index 代替 reception clock。D5 的零/2秒接收延迟样例仍是合成/理想时钟检查，不是实测 feed 延迟。

## 现在还能做什么

V19/D2/D3/D4/D5 原结论全部保留。历史 measured-latency 验收因数据不存在而关闭，不是代码失败。

只有未来前瞻 recorder 真正持久化 market timestamp + local receive wall clock + local monotonic sequence 等字段后，才可重新做实际接收延迟和 E15 到达覆盖验收。没有新 reception 数据时保持冻结维护，不开 D6/V20。

`true_reception_timestamp_available=false`; `measured_feed_latency_supported=false`; `external_consumer_accepted=false`; `production_authority=false`。
