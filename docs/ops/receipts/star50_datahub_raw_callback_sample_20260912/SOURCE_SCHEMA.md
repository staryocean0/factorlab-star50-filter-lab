# SOURCE_SCHEMA

Do not treat this file as a new schema design. It only describes the real local inputs.

## CALLBACK_RAW

**Absent. Not historically persisted.**

Live path object after adapter (never saved for these indices):

```text
Raw object type: dict  (already renamed by TdxQuotesListParserAdapter / _normalize_raw)

Original vendor HQ fields seen by parse_quotes():
code / symbol -> later "symbol"
price         -> later "last_price"
vol / cur_vol -> later "volume"
amount        -> later "amount"
bid1          -> later "bid_price_1"
ask1          -> later "ask_price_1"
bid_vol1      -> later "bid_volume_1"
ask_vol1      -> later "ask_volume_1"

Parser:
/home/starryocean/桌面/量化/unified_datahub/src/datahub/adapters/tdx_remote/realtime.py
function: TdxQuotesListParserAdapter.parse_quotes(...)
function: TdxRemoteRealtimeAdapter._normalize_raw(...)

Then:
/home/starryocean/桌面/量化/unified_datahub/src/datahub/core/services/market_stream/realtime_service.py
function: RealtimeService.normalize_tick(...)
```

`on_tick` receives the normalized envelope, not the HQ callback payload.
No historical file of that payload exists.

## PARSER_INPUT_RAW  (vendor ZIP/CSV)

This is what `MarketIndexTransactionArchiveReader.read_zip()` actually reads.

```text
Raw object type: ZIP member bytes -> csv.DictReader dict

Transport:
  daily ZIP named YYYYMMDD.zip
  member 000688.csv / 000852.csv
  encoding utf-8-sig (UTF-8 BOM)

Original fields (Chinese names kept):
时间   -> vendor market/event timestamp, "YYYY-MM-DD HH:MM:SS"
价位   -> index level
成交额 -> interval constituent turnover, CNY, non-cumulative

No symbol column inside the CSV.
No source sequence column.
Symbol comes from ZIP member name + catalog.

Parser:
/home/starryocean/桌面/量化/unified_datahub/src/datahub/core/services/market_indices/transactions_service.py
class: MarketIndexTransactionArchiveReader
function: read_zip(...)
function: _normalize_observation(...)

Catalog / symbol mapping:
/home/starryocean/桌面/量化/unified_datahub/src/datahub/core/services/market_indices/catalog.py
/home/starryocean/桌面/量化/unified_datahub/config/market_indices/core_market_indices.v1.json
  000688.SH / index_code 000688 / source member 000688.csv
  000852.SH / index_code 000852 / source member 000852.csv
```

Header bytes still present locally (leftover 2007 ZIP, header only, no quote rows):

```text
EF BB BF E6 97 B6 E9 97 B4 2C E4 BB B7 E4 BD 8D 2C E6 88 90 E4 BA A4 E9 A2 9D 0A
= UTF-8 BOM + 时间,价位,成交额\n
```

2025-06-11 original ZIP/CSV bytes are **not** on this host.

`_normalize_observation` mapping:

```text
时间  -> datetime.strptime(..., "%Y-%m-%d %H:%M:%S")
       observation_datetime = value.strftime("%Y-%m-%dT%H:%M:%SZ")
       observation_time     = value.strftime("%H:%M:%S")
       trading_day          = value.date().isoformat()
价位  -> float -> price
成交额 -> float -> amount
volume = None
row_index = enumerate order in that CSV
source_file = ZIP member name, e.g. 000688.csv
source_archive_sha256 = SHA-256 of the daily ZIP
timestamp_mode = source_exact_3s
source_kind = baidu_netdisk_market_index_transaction_3s
```

The literal `Z` on `observation_datetime` is added by the parser. It is not a proven UTC reception instant.

## NORMALIZED_SOURCE_ROWS  (what this package ships)

```text
Raw object type: parquet / JSON object (lake row)

Original fields (lake names, not renamed):
symbol
index_code
market
instrument_type
exchange
observation_datetime   # "YYYY-MM-DDTHH:MM:SSZ"
trading_day            # "YYYY-MM-DD"
observation_time       # "HH:MM:SS"
price                  # float64 index level
amount                 # float64 CNY interval turnover
volume                 # null
session_phase          # parser-derived
timestamp_mode
source_kind
source_file            # 000688.csv / 000852.csv
source_archive_sha256
row_index              # 0-based CSV order
trading_month
.dataset_version
```

No `received_at`.
No `ingested_at`.
No local monotonic clock.
`row_index` is source-file order, not host arrival.
