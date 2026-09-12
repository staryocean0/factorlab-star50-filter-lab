# DataHub reception adapter v1 — integration contract

## Purpose

This adapter connects the already-frozen prospective reception recorder to the real DataHub TDX realtime seam supplied in the 2026-09-12 handoff. It does **not** question or replace the historical market data. Historical `market_index_transactions` rows remain accepted historical observations. The adapter only answers where a future local reception stamp can be taken without confusing parser time with vendor event time.

## Audited DataHub seam

The supplied DataHub source defines an injectable `HqApiPort` and `QuotesListParserPort` in `src/datahub/adapters/tdx_remote/realtime.py`.

The concrete HQ adapter calls the TDX Python SDK and returns `list(payload or [])`. The realtime adapter then passes that list to `quotes_parser.parse_quotes(raw_quotes)`. Therefore the earliest DataHub-controlled seam visible in the supplied source is:

`TDX Python SDK get_security_quotes() return -> DataHub quote parser`

This is the frozen v1 instrumentation boundary. It is **not** raw TCP/frame arrival. Any future latency measured at this boundary includes whatever transport/SDK decoding occurs before the Python SDK returns.

The supplied DataHub parser currently creates its normalized `timestamp` with `datetime.now(UTC)`. That value is parser-time metadata. It must not be promoted to vendor market/event time and must not be called `received_at`.

The existing stream coordinator and recording coordinator operate on already-normalized quotes and are therefore too late to establish the earliest DataHub-controlled reception clock.

## Non-invasive wiring

No change to polling, failover, stream coordination, or existing normalized quote behavior is required. Wrap the existing injected dependencies:

```python
buffer = CaptureBuffer()
recorder = ReceptionRecorder(
    source="tdx_hq_sdk_return",
    channel="TdxHqApiAdapter.get_security_quotes",
    retain_raw_payload=True,
)

hq = TdxReceptionHqTap(
    existing_hq_api,
    recorder=recorder,
    capture_buffer=buffer,
    receipt_sink=receipt_sink,
)
parser = ReceptionAwareQuotesParser(
    existing_quotes_parser,
    recorder=recorder,
    capture_buffer=buffer,
    parsed_sink=parsed_sink,
)

adapter = TdxRemoteRealtimeAdapter(
    ...,
    hq_api=hq,
    quotes_parser=parser,
)
```

`TdxReceptionHqTap` returns the exact SDK payload object after stamping it. `ReceptionAwareQuotesParser` returns the exact delegate parser output after linking parsed fields to the immutable receipt stamps.

## Payload identity

The source handoff did not preserve historical realtime callback objects or wire bytes. For future SDK-return instrumentation, the adapter canonicalizes the Python SDK quote mapping into deterministic JSON bytes solely to provide a stable identity/hash at this seam. This hash means **canonical TDX Python SDK object identity**, not original network-frame identity.

Historical normalized rows are not reverse-converted into SDK payloads.

## Event-time rule

The supplied TDX source does not establish a vendor event-time field in the SDK quote contract. Therefore v1 deliberately keeps `market_event_time_normalized=null` and `event_time_parse_status=UNPARSED` unless a future source-specific contract explicitly provides a vendor event-time key.

A parser-created `timestamp=now(UTC)` is never used as event time. A self-describing raw key such as `event_time` may be retained as raw text, but remains UNPARSED until a source contract defines its timezone/meaning.

## Symbol and source sequence

The adapter maps an SDK `code`/`symbol` such as `000688` back to the uniquely requested canonical symbol `000688.SH`. Ambiguous base-code mappings are left unresolved rather than guessed.

If the SDK payload actually contains `sequence_no`, `sequence`, `seq`, or `source_sequence`, it is preserved. Otherwise source sequence remains null.

## Failure behavior

- Parser failure does not erase the receipt stamp; a failure `ParsedReceipt` is emitted.
- Payload mutation between HQ return and parser is rejected.
- Cardinality changes are rejected and logged as parse failures.
- Missing capture batches are rejected rather than silently treating parser-time metadata as reception data.
- Unsupported SDK value types fail closed instead of producing unstable payload hashes.

## Historical normalized sample

The owner-provided handoff branch contains accepted historical normalized rows for `2025-06-11`:

- `000688.SH`: 4,746 rows
- `000852.SH`: 4,746 rows
- level: `NORMALIZED_SOURCE_ROWS`
- source: `baidu_netdisk_market_index_transaction_3s`

These rows are valid historical market observations and are useful for schema/semantic compatibility. They do not contain and are not expected to contain true historical local `received_at`. No deeper vendor-byte provenance proof is required for their historical use.

## Governance / deployment boundary

This adapter is an offline-tested research instrumentation adapter only. It does not install itself in DataHub, subscribe to a feed, write production registries, or grant trading authority.

Because the current date is after the repository's 2026-08-21 Validation cutoff, future real subject rows may fall into pending BlackBox-V1. Real prospective capture must remain in protected local storage until its data role and allowed interface are determined under `DATA_USAGE_POLICY_V2.md`. Do not upload row-level prospective market/reception data to the public repository or chat merely because the recorder exists.

`production_authority=false`.
