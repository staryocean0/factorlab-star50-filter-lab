# DataHub reception adapter v1 — results

## Decision

**DATAHUB_RECEPTION_ADAPTER_V1_OFFLINE_CONTRACT_ACCEPTED_LOCAL_WIRING_PENDING**

The supplied real DataHub source exposes a clean dependency-injection seam around `HqApiPort.get_security_quotes()` and `QuotesListParserPort.parse_quotes()`. A non-invasive adapter has been implemented and tested against that contract. The correct v1 measurement boundary is the TDX Python SDK return / DataHub ingress, before the DataHub quote parser.

This does not mean a live recorder is installed, historical `received_at` has been recovered, or wire-level latency has been measured.

## What was actually executed

In the current chat container:

- 23 deterministic adapter tests: PASS
- Python compile check for adapter/tests: PASS
- real DataHub source files from handoff commit `bc84b65ba0510d164dbc90a01d3a98692982fc97` were inspected
- handoff manifest and normalized-source schema were inspected
- no live/new market data were read
- no V19/D2-D5 model/statistical research was rerun
- no Actions were dispatched

Adapter SHA256: `b57eaad252d7da72a347a426c06e7e77d5a1c7dd06fc27731ae5d930cea99c9e`
Test SHA256: `fe4b778470e94762285e44781c833e27da70d15a144a3f05edd5ad88541c19b8`
Test-output SHA256: `911213b93051f7c659132de12cc24cee92cd17f69224333df0ed93d710509665`

## Tested semantics

The tests establish that:

- canonical SDK-object hashing is stable to mapping key order;
- bytes/datetime/list-like SDK values have deterministic identity encoding;
- unsupported SDK objects fail closed;
- canonical symbol recovery is exact or uniquely inferred, never ambiguous-guessed;
- the wrapped HQ call returns the same payload object;
- one immutable receipt is stamped per returned SDK quote before parser invocation;
- local sequence and monotonic order are retained;
- payload mutation between capture and parse is rejected;
- delegate parser output is returned unchanged;
- parser-generated `timestamp=now(UTC)` is not promoted to market event time;
- source sequence is retained when actually present;
- parser exceptions still leave failure receipts;
- parser cardinality changes are rejected and logged;
- FIFO batch association is enforced.

## Historical sample use

The handoff manifest reports the accepted `2025-06-11` normalized historical sample as 4,746 rows for each index. It is used as a schema/provenance reference, not as evidence of historical local arrival time. The cloud connector did not expose the entire multi-megabyte JSONL as a local filesystem file during this step, so this result does **not** claim a new independent 9,492-row numerical replay. No such replay is required to accept the historical data itself.

## Correct interpretation of timing

The adapter measures the earliest point visible to the supplied DataHub Python source: after `api.get_security_quotes(...)` returns to DataHub and before `parse_quotes(...)` starts. It must be called `tdx_hq_sdk_return` / DataHub ingress timing, not raw network arrival.

The current TDX parser creates a UTC timestamp at parse time. That field is neither a vendor event timestamp nor a true local receive timestamp. Future source-specific event-time parsing may be added only when the upstream field contract is explicit.

## Next executable step

Install the already-tested wrappers around the real local DataHub injected `hq_api` and `quotes_parser`, first with synthetic or otherwise governance-allowed replay/input. Confirm persistence location, restart identity, duplicate/error handling, and overhead. Only after that may protected prospective capture begin.

Real post-cutoff row-level captures must remain locally protected under V2 governance. They are not automatically research-readable or uploadable.

`live_recorder_installed=false`; `true_reception_rows_collected=false`; `measured_feed_latency_supported=false`; `external_consumer_accepted=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
