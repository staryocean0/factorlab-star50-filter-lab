# STAR50 DataHub raw-before-parser sample

`CALLBACK_RAW_NOT_PERSISTED`

This package is an interface-format sample for a prospective reception recorder adapter.
It is **not** research data, not a latency study, and it contains **no** `received_at`.

## 1. Local project root

`/home/starryocean/桌面/量化/unified_datahub`

Related research copy (same lake schema, not used as the export source):
`/home/starryocean/桌面/量化/factorlab-star50-filter-lab/data/cross_index_risk_gate_3s_v1`

## 2. Actual vendor / source

Historical 3s index observations:

- Vendor: user-maintained Baidu Netdisk daily ZIP
- Remote path used at ingest (2026-08-23): `/A股数据_分笔成交_指数/指数分笔成交_沪深京_按月归档/`
- Daily archive name: `YYYYMMDD.zip`
- ZIP member for these two indices: `000688.csv`, `000852.csv`
- Vendor CSV encoding: UTF-8 with BOM
- Vendor CSV header: `时间,价位,成交额`
- Source contract id: `baidu_netdisk_market_index_transaction_3s`
- Lake dataset: `market_index_baidu_3s_20000714_20260821_cffex_underlyings_alias_repaired_v4_20260823`

Live market-stream path (no historical persistence on this host):

- `TdxRemoteRealtimeAdapter.poll_quotes()` → `TdxQuotesListParserAdapter.parse_quotes()` / `_normalize_raw()` → `RealtimeService.normalize_tick()` → `StreamCoordinator._on_tick`
- `RecordingCoordinator.on_tick` only sees the already-normalized envelope
- `recording_runtime` / `recording_datasets` row counts are 0
- `lake/recording` does not exist

Current BaiduPCS-Go login (`uid=4030689877`) no longer has `/A股数据_分笔成交_指数/`. 2025 daily ZIPs were deleted after monthly backfill.

## 3. Data level of this package

`NORMALIZED_SOURCE_ROWS`

Not `CALLBACK_RAW`.
Not `PARSER_INPUT_RAW` (the 2025 vendor ZIP/CSV bytes are gone).

This is `market_index_transactions` lake rows: the closest persisted records after `MarketIndexTransactionArchiveReader.read_zip()` parsed vendor CSV.

## 4. Was callback raw historically persisted?

No.

`CALLBACK_RAW_NOT_PERSISTED`

No live callback bytes, no vendor protocol frames, and no local reception clock were found for `000688.SH` / `000852.SH`.

## 5. Parser source paths (copied under `parser_source/`)

Historical ZIP/CSV parser (the actual 3s ingest path):

- `/home/starryocean/桌面/量化/unified_datahub/src/datahub/core/services/market_indices/transactions_service.py`
  - class `MarketIndexTransactionArchiveReader`
  - `inspect_zip()` / `read_zip()`
  - function `_normalize_observation(...)`
- `/home/starryocean/桌面/量化/unified_datahub/src/datahub/core/services/market_indices/catalog.py`
- `/home/starryocean/桌面/量化/unified_datahub/config/market_indices/core_market_indices.v1.json`
- `/home/starryocean/桌面/量化/unified_datahub/config/reliability/source_contracts/market_index_transactions.v1.json`
- `/home/starryocean/桌面/量化/unified_datahub/scripts/market_index_transactions.py`

Live quote path (already normalized before any recorder hook):

- `/home/starryocean/桌面/量化/unified_datahub/src/datahub/adapters/tdx_remote/realtime.py`
  - `TdxRemoteRealtimeAdapter.poll_quotes`
  - `TdxQuotesListParserAdapter.parse_quotes`
  - `TdxRemoteRealtimeAdapter._normalize_raw`
- `/home/starryocean/桌面/量化/unified_datahub/src/datahub/core/services/market_stream/realtime_service.py`
  - `RealtimeService.normalize_tick`
- `/home/starryocean/桌面/量化/unified_datahub/src/datahub/orchestration/stream_coordinator.py`
- `/home/starryocean/桌面/量化/unified_datahub/src/datahub/orchestration/recording_coordinator.py`
- `/home/starryocean/桌面/量化/unified_datahub/src/datahub/core/services/market_stream/recording_service.py`
- `/home/starryocean/桌面/量化/unified_datahub/src/datahub/core/models/stream.py`

These copies are byte-identical to the local DataHub files. They were not rewritten.

## 6. Original symbol field

Vendor ZIP member filename: `000688.csv` / `000852.csv`

Catalog fields:

- `symbol` = `000688.SH` / `000852.SH`
- `index_code` = `000688` / `000852`

CSV rows themselves have **no** symbol column. Identity comes from the member name plus `core_market_indices.v1.json`.

## 7. Original market / event time field

Vendor CSV: `时间`

Format seen on leftover vendor bytes: `YYYY-MM-DD HH:MM:SS`

After parser: stored as

- `observation_datetime` = `YYYY-MM-DDTHH:MM:SSZ` (naive Shanghai session clock with a literal `Z` suffix added by `_normalize_observation`)
- `observation_time` = `HH:MM:SS`
- `trading_day` = `YYYY-MM-DD`

These are market observation clocks, not local reception clocks. Do not treat them as `received_at`.

## 8. Original price field

Vendor CSV: `价位` (index level)

After parser: `price` (Python `float` / parquet double)

Vendor CSV also has `成交额` (interval turnover, CNY, non-cumulative). After parser: `amount`. `volume` is always null for these index observations.

## 9. Source sequence

Vendor CSV has **no** sequence column.

Persisted order is `row_index` = enumerate order inside that ZIP member after `csv.DictReader`.

Live TDX `sequence_no` is assigned by DataHub (`count(1)` / `_normalize_raw`), not a vendor sequence. No live ticks were exported.

## 10. Actual raw payload type

Vendor parser input (not available for 2025-06-11 on this host):

- Daily ZIP (`bytes`)
- Member CSV (`bytes`, UTF-8 BOM)
- Then `csv.DictReader` rows: `dict` with keys `时间`, `价位`, `成交额`

What this package actually ships:

- Lake `dict`/parquet rows after `_normalize_observation`
- Plus a 27-byte leftover vendor CSV **header only** (`EF BB BF` + `时间,价位,成交额\n`) taken from a 2007 ZIP that still exists locally. That file contains no quote rows and is not `000688`/`000852` data.

## 11. Exported trading day

`2025-06-11`

Ordinary mid-year session. Chosen from the ingest receipt calendar (`20250611.zip` present, `missing_members=[]`, `invalid_row_count=0`). Not chosen by price, return, or research outcome.

Both indices use this same day.

No row after `2026-08-21` was read into the quote files.

## 12. Row counts

- `000688.SH`: 4746
- `000852.SH`: 4746

Time span in lake rows: `09:25:00` … `15:00:03`.
`row_index` 0 … 4745 for each file.
`source_archive_sha256` = `f4045be45b8bc886de39ff595533e59416a042e09d7c1ee8f3682b574bf1afe5`

## 13. Transformations

Ideal original-byte copy of `20250611.zip` / `000688.csv` / `000852.csv` is **not possible**: monthly backfill deletes the download directory after parquet+receipt persist, and the current Baidu account no longer lists that remote tree.

What was done:

1. Filtered the v4 lake parquet to `trading_day=2025-06-11` and only `000688.SH` / `000852.SH`.
2. Wrote those rows in original `row_index` order to parquet, keeping lake field names. No columns were renamed.
3. Wrote the same rows to JSONL. JSON numbers are IEEE doubles from parquet (`982.6` not the original CSV text `982.60`). `volume` is JSON `null`.
4. Did **not** invent `received_at`, `ingested_at`, file mtime, download time, or current export time as a reception clock.
5. Copied one-day ingest receipt excerpt `20250611.zip.source_receipt_excerpt.json` from `trading_month=2025-06.json`. That receipt lists the nine catalog symbols requested when the ZIP was ingested; it is archive metadata, not other-index quote rows.
6. Copied leftover vendor CSV header bytes only, for the real `时间,价位,成交额` spelling.

## Missing

- Historical callback raw payload
- 2025 vendor ZIP / CSV original bytes for these two indices
- Local reception clock
- Live TDX quote objects

Do not upload this ZIP to public GitHub. Vendor archive and local source copies are for the current ChatGPT session only.
