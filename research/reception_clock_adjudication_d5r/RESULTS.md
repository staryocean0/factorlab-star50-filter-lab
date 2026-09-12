# D5R 结果：历史真实接收时钟不可用，实测延迟验收无法完成

## 正式判定

**D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED**。

本轮不是模型研究，也不是重新执行 D5。它只复核本地上传的真实接收时间检索包，并判断已有历史数据是否足以把 D5 的 `received_at` 从理想/合成时钟升级为真实本机接收时钟。

结论：**不能。** 本地没有保存 `000688.SH` / `000852.SH` 的逐条真实 reception timestamp，因此无法从现有历史数据计算真实接收延迟分布、真实 E-15 到达覆盖率或实际端到端提前量。不得使用 `available_at`、batch `ingested_at`、文件 mtime、下载时间或 market observation time 代替 `received_at`。

## 已复核的来源

本地交付 commit：`09cb66a86be6a9bef3a91b52af34b747f812b407`。

Release：`star50-true-reception-raw-20260912`；asset `STAR50_TRUE_RECEPTION_RAW_20260912.zip`。

Release asset：

- size: `5446` bytes
- SHA256: `63badecf70405452674831f41a6aef0de174ca8d10b113fc32c91a8e1ca24cf0`
- quote rows: `0`
- verdict: `NO_TRUE_RECEPTION_TIMESTAMP_AVAILABLE`

仓库来源文件：

- `docs/ops/receipts/star50_true_reception_raw_20260912/README.md`
- `SCHEMA.json`
- `SOURCE_INFO.json`
- `MANIFEST.json`
- 原 ZIP

本地只读检索覆盖 DataHub live lake/metadata、market-stream recording 代码和 SQLite 表、FactorLab 两指数 3s 研究副本及 reception-clock 字段搜索。`recording_datasets`、`recording_runtime`、`subscriptions`、`replay_sessions`、`source_receipts` 均为空；`lake/recording` 与 `ticks.parquet` 未物化。

## 哪些字段存在，哪些不能冒充

现有 `market_index_transactions` 具有 `observation_datetime`、`observation_time`、`trading_day`、`price`、`row_index` 等，它们描述市场/重建观察时钟和源文件顺序，不是本机到达时钟。

以下均不能升级为真实 reception clock：

- `available_at`：历史/派生可得性口径；
- `ingested_at`：batch import 时钟；
- 文件 mtime / 下载时间；
- `source_receipts.observed_at`（且当前表为空）；
- `row_index`：源顺序；
- 其他品种或元数据表中的 `local_timestamp` / `received_at`。

特别地，现有 `observation_datetime` 虽带字面 `Z`，其时钟标签与上海交易时段一致，不能据此解释成 UTC 本地接收时间。

## 对既有结论的影响

### 保留

- V19 冻结风险状态识别结论不变；
- D2 双时钟历史工程回放不变；
- D3 未获实际增量晋升的结论不变；
- D4 指定目标下连续风险程度有限支持不变；
- D5 本仓样例消费者的字节、as-of、过期、缺失和时钟分离工程验收不变。

### 不能再向上声称

- 不能声称历史 `received_at` 已由真实本机日志验证；
- 不能给出真实 feed / network / processing latency 分布；
- 不能把 D5 零延迟或 2 秒延迟样例称为实测；
- 不能把 owner_realtime_assumption 升级成 measured_reception_log；
- 不能据现有历史数据完成真实外部接收时钟验收或生产准入。

因此 D5 的 `external_consumer_accepted=false` 仍保持；不是代码失败，而是所需历史接收观测不存在。

## 下一步的唯一合理数据路径

若未来确实需要 measured reception 证据，只能**前瞻采集**真实接收时钟，而不是从历史数据反推。

未来采集的最小字段应在接收瞬间原样持久化：

- symbol；
- source/vendor/channel；
- market/event timestamp；
- local wall-clock receive timestamp（timezone-aware）；
- local monotonic receive timestamp / sequence（用于识别系统时钟调整与同秒顺序）；
- price；
- source sequence / row identity（若源提供）；
- trading day；
- recorder/version identity。

该采集契约只是未来观测要求，不代表本轮已修改 DataHub、启动在线 recorder 或获得生产权限。没有这类新观测前，本仓应继续把盘中到达语义标记为 `owner_realtime_assumption` / `unmeasured_reception`。

## 当前断点

**D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED**。

这不是 D6，也不是 V20。没有必要为了缺失日志继续重跑旧模型。只有真实前瞻 reception 记录出现后，才有资格重新打开“实测接收时钟验收”问题。

`true_reception_timestamp_available=false`；`measured_feed_latency_supported=false`；`external_consumer_accepted=false`；`d6_started=false`；`v20_started=false`；`blackbox_queried=false`；`pnl_computed=false`；`production_authority=false`。
