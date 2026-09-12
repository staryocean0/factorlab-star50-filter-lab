# STAR50 / CSI1000 true reception raw export

Verdict: `NO_TRUE_RECEPTION_TIMESTAMP_AVAILABLE`

This package contains **no quote rows**. Cloud already has the multi-year 3s / 1m / 5m history. The local search found **no** per-tick local reception clock for `000688.SH` or `000852.SH`. No `received_at` was invented from file mtime, database update time, download time, `available_at`, `ingested_at`, or frequency inference.

## 1. Local systems searched

- DataHub live lake and metadata: `/home/starryocean/桌面/量化/unified_datahub/.runtime/live`
- DataHub market-stream / recording code and SQLite tables
- FactorLab STAR50 research 3s copies: `/home/starryocean/桌面/量化/factorlab-star50-filter-lab/data/cross_index_risk_gate_3s_v1`
- FactorLab / DataHub / Terminal source greps for reception-clock field names
- DataHub `lake/recording` (does not exist)
- `datahub.db` tables `recording_datasets`, `recording_runtime`, `subscriptions`, `replay_sessions`, `source_receipts`

No GitHub, FactorLab, or DataHub files were modified. No V19/D2–D5, consumer, model, or backtest was run.

## 2. Actual source directories / tables

Closest **market-index** raw product (market observation only):

- Lake: `unified_datahub/.runtime/live/lake/market_index_transactions`
- Versions inspected by schema only:
  - `dataset_version=market_index_baidu_3s_20000714_20260821_v1`
  - `dataset_version=market_index_baidu_3s_20000714_20260821_cffex_underlyings_alias_repaired_v4_20260823`
- Research copies (same schema): `factorlab-star50-filter-lab/data/cross_index_risk_gate_3s_v1/000688.SH_*.parquet` and `000852.SH_*.parquet`
- Vendor archive fields (Baidu CSV): `时间,价位,成交额` only
- TDX `history_transaction` incremental lake files exist for 2026-08-24/2025 dates; **2026 rows were not exported**

Live recording tables in `datahub.db`:

- `recording_datasets` row_count = 0
- `recording_runtime` row_count = 0
- `subscriptions` row_count = 0
- `replay_sessions` row_count = 0
- `source_receipts` row_count = 0
- no `ticks.parquet` under live runtime

Recording writer *would* persist `lake/recording/dataset_version=*/ticks.parquet` with feed `timestamp` / `available_at` / `sequence_no`. That path has never been materialized on this host.

## 3. Exported date range

None. No true-reception sample exists, so no trading-day window was exported.

2026 / BlackBox / protected quote rows were not read for export. A 2025 schema peek of the already-known 3s research file was used only to list columns.

## 4. Row counts

- `000688.SH`: 0 exported
- `000852.SH`: 0 exported

## 5. Native frequency of closest raw product

Baidu archive: vendor-labelled exact 3s (`timestamp_mode=source_exact_3s`).
TDX incrementals: minute protocol plus reconstructed 3s rank (`timestamp_mode=minute_protocol_plus_stable_sequence_rank_3s`). Neither product stores local arrival time.

## 6. Market timestamp field (closest raw)

- `observation_datetime`
- `observation_time`
- `trading_day`

These are **market / reconstructed observation** clocks, not local reception.

## 7. True received timestamp field

**Absent.** `NO_TRUE_RECEPTION_TIMESTAMP_AVAILABLE`

## 8. Timezones (as stored, not rewritten)

- `observation_time`: naive `HH:MM:SS`. DataHub session semantics treat this as China index wall clock `Asia/Shanghai`.
- `observation_datetime`: ISO string with a literal `Z` suffix, but the clock-of-day matches Shanghai session labels (example from 2025 research file, not exported here: `2025-01-02T09:25:00Z` with `observation_time=09:25:00` open-call). This is **not** a proven UTC instant of local receipt. Do not reinterpret it as `received_at`.
- No timezone-aware local reception field exists.

## 9. Same market timestamp, multiple rows

The 3s lake keeps `row_index` and does not require uniqueness of `observation_datetime`. That property was **not** re-exported; it is a property of the historical observation product, not of a reception log.

## 10. Original order

Not applicable: no reception rows exported. Historical 3s files contain `row_index`.

## 11. Transformations

None on quote data. This directory is documentation-only.

## 12. Missing reception timestamp

Yes. Entirely missing for both indices.

### Closest real fields (do not treat as received_at)

| Field | Where | Why it is not true reception |
|---|---|---|
| `observation_datetime` / `observation_time` | `market_index_transactions` | Market/reconstructed event time |
| `row_index` | same | Source-file order, not host arrival |
| `available_at` | derived 1m builder sets `{day}T15:30:00+08:00` | Schedule-bound knowledge time |
| `ingested_at` | derived 1m builder sets `datetime.now(UTC)` at **batch import** | One import clock for many bars |
| `ingested_at` on `star50_etf_spot_l2` | STAR50 **ETF** L2, not `000688.SH` / `000852.SH` index | Wrong instrument; batch ingest |
| `local_timestamp` | CN futures depth snapshots | Futures vendor/local clock, not these cash indices |
| `received_at` | `nonstock_listing_instance_v5` listing metadata | Not index quotes |
| recording tick `timestamp` / `available_at` | market-stream code only | No persisted recordings on this host |
| file mtime / download time / `source_receipts.observed_at` | various | Forbidden substitutes; receipts table empty |

### Symbol mapping (not rewritten)

- `000688.SH` = STAR50 / 科创50; lake also stores `index_code=000688`, `exchange=SSE`
- `000852.SH` = CSI 1000 / 中证1000
- Do not confuse with stock `000688.SZ`

No `000688.XSHG` rows were found in the inspected 3s schema sample.
