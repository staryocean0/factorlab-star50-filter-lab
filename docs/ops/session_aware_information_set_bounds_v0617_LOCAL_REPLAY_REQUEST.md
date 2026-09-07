# LOCAL REPLAY REQUEST — session-aware information-set bounds v0.6.17

日期：2026-09-07  
任务：CL-STAR-RISK-20260907  
云端实现验收：**PASS**  
云端 tested implementation commit：`b6930dcd16bb47664b1edcbc13e2bdabf779cf4a`  
CI：run `34111701647` / job `101709204616`，`159 passed, 1 skipped`；skip 仅因 GitHub-hosted runner 未挂载本地 canonical L3 三源码。  
真实 DataHub replay：**尚未执行**。

本请求是执行单，不授权本地重新定义研究问题。任何必要字段/identity receipt 缺失时必须 fail closed，提交 blocker receipt；不得临时改公式、删样本或用别的 1m surface 顶替。

## A. 代码身份

1. 先读取本请求与：
   - `docs/research/session_aware_information_set_bounds_v0617/FROZEN_PROTOCOL.md`
   - `docs/research/session_aware_information_set_bounds_v0617/implementation_acceptance_receipt.json`
2. 实际 scientific runner 必须来自 commit：
   `b6930dcd16bb47664b1edcbc13e2bdabf779cf4a`
3. 以下 Git blob 必须与 receipt 一致：
   - core `87e02e7f56737da39d9a2976abe51b677859881b`
   - CLI `07a050a53b4b5194c4b1efc08b909884b388a408`
   - v0.6.17 tests `bb0236d501c689c2f764601b94c8a92a437a5862`
   - protocol `8810e4d13474398a0fec0f092aa57863ce78be82`
4. 本地可以在自己的工作树调用 tested commit；不得修改上述四个对象后仍沿用 v0.6.17 名义。

## B. 两个必须是“事前已有”的 identity receipts

### B1. DataHub authoritative 1m source

必须找到**本请求之前已经存在**、属于此前 frozen intake/provenance 交付链的 DataHub source identity receipt，并从中取得：

- authoritative source 文件/对象身份；
- `rows = 349923`；
- **事前登记的 SHA-256**；
- DataHub commit / source receipt / lineage 信息。

禁止：

- 使用 FactorLab `1m_official` 的 350,561-row surface；
- 现场对某个候选文件计算 SHA-256，然后把同一个新算值同时当作 `actual` 和 `expected`；
- 因为路径名字相似而替代 authority。

若找不到**事前已有 SHA-256 receipt**，停止 scientific replay，输出：
`blocker = prior_authoritative_source_hash_receipt_missing`。

### B2. frozen v0.6.15 leg universe / overlays

必须找到此前 v0.6.15 失败实验实际使用且已冻结的 published-leg universe（包括当时 frozen strict-pair / qualification overlays）及其**事前已有 hash/manifest**。

不得从 v0.6.17 结果重新筛 leg，不得删除 session-edge / lunch / overnight / offset 边界 leg。

若找不到事前已有的 leg-universe hash/manifest，停止 scientific replay，输出：
`blocker = prior_v0615_leg_universe_identity_missing`。

## C. DataHub support topology 导出

本阶段 FactorLab **禁止自己复刻 DataHub bucket SQL**。support membership / expected-step topology 必须从已经云端复核过的 archived DataHub contract/implementation 路径导出。

已复核的关键语义继续有效：

- official request 与 offset wall-clock request 是两条明确路径；
- 5m offset0 的 official-v2 与 wall-clock-v1 source-minute→label 在当前语义下逐分钟等价，但该等价性不得外推到 15/30/60m；
- offset>0 的首桶按 native label 可能出现 **6 个 1m labels**，所以不得 fixed-five；
- 午休/隔夜/被 slicer 丢弃的分钟不得偷塞进相邻 native bar。

优先调用 DataHub 已存在的 deriver/assignment implementation；如必须写 read-only adapter，它只能：

1. 调用/暴露既有 DataHub assignment；
2. 导出明确 `leg_id -> step_ordinal -> source row` membership；
3. 对 expected 但被明确丢弃/不可观测的 step 保留 `observed=false` placeholder；
4. 不计算任何 return/P&L/未来标签；
5. 随结果提交 adapter 源码 hash、DataHub HEAD、调用的 canonical function/contract ID 和 targeted tests receipt。

support 表至少满足 v0.6.17 protocol：
`leg_id, step_ordinal, observed, <stable source key>, open, high, low, close`。

若 authoritative source 的 `timestamp` 不唯一，必须用 DataHub 原稳定 row key；禁止为通过 gate 而去重。

## D. 本地执行前 gates

执行顺序固定：

1. 验 tested implementation commit / blob；
2. 读取 prior source expected SHA-256；
3. 读取 prior v0.6.15 legs expected SHA-256；
4. 载入 exact 349,923-row source，计算 actual SHA-256，与 prior expected SHA-256 比较；
5. 载入 frozen legs，计算 actual SHA-256，与 prior expected SHA-256 比较；
6. 导出 DataHub support topology；
7. 验每个 `observed=true` support row 都能回连 authoritative source，OHLC 相等；
8. 才能执行 v0.6.17 runner。

任一步失败，停止；不得进入第8步后再解释前面的身份失败。

## E. 固定 runner

在 tested implementation commit 上执行：

```bash
python scripts/run_session_aware_information_bounds_v0617.py \
  --authoritative-source <exact-datahub-authoritative-1m> \
  --expected-source-sha256 <PRIOR_FROZEN_DATAHUB_SHA256> \
  --legs <EXACT_FROZEN_V0615_LEG_UNIVERSE> \
  --expected-legs-sha256 <PRIOR_FROZEN_V0615_LEGS_SHA256> \
  --support <DATAHUB_ACTUAL_SUPPORT_TOPOLOGY> \
  --source-key <timestamp-or-stable-datahub-row-key> \
  --out artifacts/session_aware_information_set_bounds_v0617
```

**不得使用 `--diagnostic-nonauthoritative` 产生 scientific conclusion。** 该 flag 只用于查 blocker。

## F. 必须保留的真实 replay 输出

runner 固定输出：

- `leg_information_bounds_v0617.csv`
- `summary_v0617.json`
- `replay_receipt_v0617.json`

另请本地生成一个不含交易结果的：
`support_topology_receipt_v0617.json`，至少含：

- DataHub repo HEAD；
- archived contract / canonical implementation identity；
- authoritative source prior expected hash + actual hash + row count；
- frozen legs prior expected hash + actual hash + row count；
- support file SHA-256 + rows；
- source-key uniqueness诊断；
- expected-step-count frequency（尤其 5/6 等）；
- offset × boundary_class 的 support complete/gap 计数；
- observed support→source OHLC max error；
- `results_blind=true`；
- `read_2026=false`；
- `trading_or_oos_evaluated=false`。

如 support topology 文件过大，不要求上传原始 349,923-row source，也不要求把整个 support 文件推云端；但必须保存本地、记录 SHA-256，并上传 deterministic boundary samples：offset0–4 的晨首、午前、午后首、下午末、overnight/session-gap 代表样本，包含 source key / ordinal / observed / native bar identity，供云端逐项复核。

## G. 回传位置

不要覆盖本云端 tested branch。建议新建：

`local/session-aware-information-set-bounds-v0617-replay-20260907`

只提交：

- 三个 runner 输出；
- `support_topology_receipt_v0617.json`；
- deterministic boundary samples；
- 如新写 read-only DataHub adapter，则提交其归档副本/测试/源码 hash（不含凭据和父数据）；
- `LOCAL_REPLAY_RESULT.md`，只陈述 identity/support/tightness 结果，不看收益。

随后回传 branch + commit SHA。云端下一步是对该 commit 做逐文件复核并裁决 real replay，不是直接进入 returns/OOS。

## H. 仍然冻结

无论 real replay 结果如何，以下都没有因本请求解锁：

- `morphology_replication_not_yet_accepted`；
- direction；
- third-wave；
- returns / P&L / MDD；
- fresh OOS；
- trading / position sizing / production。

本地不得因为 v0.6.17 bounds 看起来紧或松而改 support policy、删边界 leg、扫描新阈值或提前看经济结果。
