---
doc_id: MODULE-HISTORY-MARKET-INDEX-TRANSACTIONS-V1
truth_role: design-truth
module_primary: history
module_related: [tdx-tech]
governed_surface: market-index 3s observations, 1m canonical parent and shifted bars
---

# 市场指数 3 秒观测与多频 K 线白皮书

## 1. 能力结论

市场指数分钟能力不再是 gap。生产链固定为：

```text
Baidu Netdisk exact 3s deep history
  + TDX history_transaction daily incrementals
  -> market_index_transactions (3s)
  -> transaction-derived 1m source
  -> bars_cn_index_1m_raw_canonical
  -> BarsQuery on-demand 5m/15m/30m/60m/1d
  -> session_offset_minutes / close_anchor additive views
```

百度负责深历史，TDX 负责日常增量；TDX 日线 `get_index_bars(category=4)` 同时作为日线交叉验证和独立 daily product source。

## 2. 百度源实证

远程目录：

```text
/A股数据_分笔成交_指数/指数分笔成交_沪深京_按月归档/
```

2026-08-23 从百度客户端 `filecache.db` 和真实下载确认：

- 月目录：`2000-07..2026-08`；
- 日 ZIP：6,331 个，`20000714.zip..20260821.zip`；
- 总大小：61,781,292,874 bytes；
- `20260821.zip`：22,673,481 bytes，531 个指数 CSV；
- CSV：UTF-8 BOM，字段严格为 `时间,价位,成交额`。

核心 8 指数真实样本共 37,967 行，全部合法且无重复。`成交额`是每个片段的非累计金额：相邻行约一半会下降；沪深300 全日求和为 505,500,865,900 CNY。它不是证券成交量，`volume` 必须保持 null。

## 3. TDX 协议语义

### 3.1 index-bars 死锁修复

`AsyncTdxHq_API.get_index_bars` 在 native handler 路径曾保留 `self.lock`。parser 获取该锁后调用 `self.send_pkg`，native adapter 再次获取同一非重入锁，导致 8 秒超时。修复为与 `get_security_bars`、transaction 方法一致：`reader/writer` 缺失时 `lock=None`。

真实 DIRECT probe 后：

- `get_index_bars(category=4)`：约 58ms，返回日线；
- `get_index_bars(category=8)`：约 115ms，返回 1m；
- `get_history_transaction_data`：约 114ms/2,000 行。

### 3.2 transaction 字段不能按证券解释

TDX `0x0FB5` 历史 transaction 的时间协议只有 `HH:MM`。同一分钟可有最多 20 行，源顺序稳定，秒标签按 rank `0,3,...,57` 确定性恢复。该秒不是协议原生秒，逐行必须带：

```text
timestamp_mode=minute_protocol_plus_stable_sequence_rank_3s
```

对指数，TDX `vol` 实际是成交额百元单位：真实样本最后一行 `31,754,120 × 100 = 3,175,412,000`，与百度精确相等。`buyorsell` 是占位值，不是买卖方向。禁止复用证券 transaction 的 `volume/side` 语义。

同日沪深300三页为 `2000+2000+745=4745` 行。2026-08-23 对 `39.108.28.83:7709` 做 DIRECT live replay 后，重建结果与百度 4,745 行在 timestamp、price、`vol×100` amount 上逐行 `mismatch_count=0`。分页边界可能切开同一分钟，重建排序固定为 `(HH:MM, page_start ASC, page_row_index ASC)`，再计算分钟内 rank。

## 4. 3s 到 1m 合同

分钟线只聚合实际观测，不 carry forward：

| 原始时间 | 1m 标签 | 规则 |
|---|---|---|
| 09:25--09:29 | 09:31 | 集合竞价价/额并入首分钟；真实 TDX 09:31 open 与 09:25 价一致 |
| 09:30--11:28 | 下一分钟 | end label |
| 11:29--11:30:59 | 11:30 | 午间修正 cap 到上午尾桶 |
| 13:00--14:57:59 | 下一分钟 | end label，14:57 行形成 14:58 |
| 14:58--14:59:59 | 下一分钟，最大 15:00 | 仅源真实存在时生成 |
| 15:00--15:00:59 | 15:00 | 收盘最终修正 cap 到尾桶 |

若源无 14:58/14:59 观测，不生成对应 bar。真实沪深300得到 239 个 1m bar：无 14:59，15:00 bar close=4618.90、amount=6,073,726,900。TDX category=8 的 14:59 尾行出现 `5.877e-39` sentinel，因此不能取代 transaction-derived 尾桶。

## 5. 多频与差分供应

1m 发布为标准 `dataset_kind=bars`：

```text
market=cn_index
instrument_type=market_index
dataset_id=bars_cn_index_1m_raw_canonical
```

外部使用通用接口：

```text
GET /api/v1/history/bars
  ?market=cn_index
  &instrument_type=market_index
  &frequency=1m|5m|15m|30m|60m|1d
```

不传 pinned version 时，现有 `BarsQuery` 从 latest 1m canonical 按需派生。`session_offset_minutes` 和 `close_anchor=11:30` 完全复用 `cn_a_session_wall_clock_offset_v1`，不是另一套指数专用算法。

真实样本已验证：

- 1d@11:30：open=4585.44、close=4616.83；
- 60m+5：标签 `10:35/11:30/14:05/15:00`，construction metadata 完整；
- `first_tradable_slot` 与现有合同一致。

## 6. 不变量

- Baidu overlap 优先于 TDX reconstructed 秒标签；
- TDX 只有在真 DIRECT 7709 路由下才进入增量 lane；
- 不把 `vol` 写成 volume，不从 price×vol 发明 amount；
- 不填造缺失分钟；
- 3s、1m、canonical 每层均不可变并保留 receipt/hash；
- 不修改证券 lifecycle/authority 大表。

## 7. 生产化回填与 lifecycle

全历史不再按 6,331 个日包发布零散产品。`market_index_bulk_backfill.py` 以月为边界执行：

1. 通过用户已登录的 BaiduPCS-Go 下载一个月目录；
2. 每个日 ZIP 只读官方目录中的指数 CSV，校验日期、header、SHA-256 和 launch-date 后成员完整性；
3. 生成月分区 3s 与 1m Parquet，持久化 checkpoint 后立即删除当月下载目录；
4. 全部月份完成后才合并不可变 `market_index_transactions` 版本、注册 1m source 并发布 canonical；
5. 任一个预期“指数×交易日”缺失、重复或价额非法都使 source 为 `PARTIAL`，禁止 canonical 发布。

若日 ZIP 在多个指数同一秒同时出现 `price=0/amount=0` 的源端哨兵行，批量入口会保留 archive SHA、member、row index 和 raw 值后隔离该行；不 carry-forward、不填 0、不影响同分钟其余真实观测。单日严格入口默认仍拒绝非法行。

深历史 expected day 以 checkpoint 中实际取得的日 ZIP 枚举为准：当日有 ZIP 才证明该源的交易日。有 ZIP 但某目录指数成员缺失时，记为显式 `source_member_missing_on_archive_day` 非阻塞 gap；这表示已完整交付源端实际覆盖，不声称或补造缺失点位。

路由合同位于 `config/market_indices/market_index_product_lifecycles.v1.json`：Baidu 是历史 primary，TDX 是每日增量 primary 与 overlap reconciler；默认路由拒绝，不允许 implicit latest/fallback。该独立 registry 复用通用 lifecycle 引擎，但不写入外部 AI 正在修改的核心元数据清单。

## 8. 2026-08-23 全量生产实证

- 314 个月目录、6,331 个日 ZIP 全部进入 checkpoint；
- `market_index_baidu_3s_20000714_20260821_v1`：`READY`，135,077,414 条，manifest hash `fdacc3f7ded7193944ec22efee597ad6e7ad477026bd5030227156ff7d7c2820`；
- derived 1m source 与 `bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_v1`：均 `READY`，9,135,707 条；
- 38,527 个 expected “指数×archive day”中实际 38,217，310 个源成员缺失显式非阻塞；2,051 条零值哨兵已隔离；duplicate/invalid residual/blocking 均为 0。
- 后续审计发现中证500旧档使用 `399905.csv`，不是官方 identity `000905.csv`。v4 固定 source alias 后以 78 个原始 ZIP/CSV receipt 补入 exact 3s，生成 `market_index_baidu_3s_20000714_20260821_cffex_underlyings_alias_repaired_v4_20260823`：`READY`、135,222,990 条；derived 1m/canonical 为 9,154,417 条。
- v4 的 CFFEX required scope=`000016.SH/000300.SH/000905.SH/000852.SH`，required missing=0。全九指数仍保留 232 个非目标 `source_member_missing_on_archive_day`，不得改写为全目录零缺口。
- 老历史 TDX transaction 与百度 exact 3s 的 overlap 在行数和 amount 上漂移，禁止用分钟标签重建回填 2006—2007 源成员缺口；TDX 仍只在已逐行验证的时期承担日常增量。
- 沪深300 2026-08-21 验收：3s=4,745 条，1m=239 条，5m=48 条，60m+5 为 `10:35/11:30/14:05/15:00`，11:30 日线 open/close=`4585.44/4616.83`。

来源合同：`config/reliability/source_contracts/market_index_transactions.v1.json`。操作步骤见 [`market-index-transactions-workflow.md`](market-index-transactions-workflow.md)。
