# Prospective reception recorder V1 — frozen engineering contract

Date: 2026-09-12.
Source authority: `research/reception_clock_adjudication_d5r/RESULTS.md`.
This is an engineering instrumentation contract, **not D6, not V20, not a new model**.

## 1. Purpose

Historical `000688.SH` / `000852.SH` storage contains no true per-message local reception clock. Therefore measured feed/network/processing latency cannot be recovered retrospectively.

The only admissible path is prospective capture at the actual market-data callback boundary. The recorder exists to preserve enough evidence to later answer:
- when the source event says the observation occurred;
- when the local process first received it;
- the order in which the local process observed messages even if wall clock changes;
- the exact raw payload identity used to derive parsed fields.

It must not infer historical `received_at`, alter V19/D2-D5, create a trading gate, or grant production authority.

## 2. Capture must precede parsing

At the feed callback boundary the first recorder operation is:

1. increment a recorder-local sequence;
2. capture local UTC wall clock (`time.time_ns()` or equivalent);
3. capture local monotonic clock (`time.monotonic_ns()` or equivalent);
4. hash the raw payload and, where policy permits, retain the raw bytes;
5. only then parse/normalize event timestamp, symbol, price or source sequence.

`receive_wallclock_utc_ns` is human/cross-process time. `receive_monotonic_ns` is the within-process ordering/delta authority. Wall clock is explicitly allowed to jump backwards under NTP/manual clock changes; monotonic regression is an error.

Each recorder instance has a stable `recorder_instance_id` plus process-start wall/monotonic anchors. Monotonic values are never compared across recorder instances without an explicit bridge.

## 3. Required receipt evidence

Raw receipt record:
- schema / recorder version;
- recorder instance id;
- immutable receipt id;
- source and channel;
- local sequence;
- local receive wall-clock in UTC nanoseconds plus rendered UTC ISO time;
- local receive monotonic nanoseconds;
- process-start wall-clock and monotonic anchors;
- raw payload SHA256 and byte size;
- optional raw payload bytes/base64 according to local data policy.

Parsed record references the receipt id and may add:
- symbol (`000688.SH` / `000852.SH`);
- trading day;
- source market/event time exactly as received;
- normalized event time plus explicit timezone **only when source semantics support it**;
- PARSED / UNPARSED / INVALID status;
- price;
- source sequence / source row identity;
- parse error.

Invalid or unparseable source event time does not delete the receipt. It remains evidence of local arrival.

## 4. Forbidden substitutions

Never synthesize local reception from:
- `available_at`;
- batch `ingested_at`;
- file modification/download time;
- observation/event time;
- row index;
- another instrument's local timestamp;
- historical frequency assumptions.

Do not silently rewrite a literal `Z` source field into UTC semantics when source documentation does not establish that meaning.

## 5. Persistence and duplicates

Capture records are append-only. Exact duplicate source messages may appear more than once and must not be deduplicated at recorder level. Preserve source sequence if provided and always preserve recorder local sequence.

Raw and parsed streams may be separate. A receipt may legitimately have no parsed row after parser failure/crash; a parsed row may never exist without a receipt.

A synchronous JSONL reference sink is included for bounded tests. Live integration must benchmark recorder overhead and choose durability/buffering explicitly; this repository does not certify a production writer, queue, restart/reconnect protocol or disk policy.

## 6. Acceptance before real market use

Reference implementation acceptance:
- deterministic synthetic clocks;
- local sequence contiguous within recorder instance;
- monotonic clock cannot regress;
- wall clock regression is recorded rather than hidden;
- raw payload hash/size reproducible;
- parsing cannot mutate receipt clocks;
- invalid event times remain captured;
- cross-instance joins rejected;
- append-only serialization and independent validator pass.

Local DataHub integration acceptance (future, separate):
- place stamp call at the actual callback boundary before parsing/queueing;
- prove integration path with synthetic/replay input first;
- record source/channel/version identity;
- benchmark recorder overhead;
- define crash/restart and persistence semantics;
- only then begin protected prospective capture.

## 7. Data-governance quarantine

Current date is after the repository Validation cutoff `2026-08-21`. Under `DATA_USAGE_POLICY_V2`, eligible new observations may belong to pending BlackBox-V1.

Therefore installing the recorder does **not** authorize this research session to inspect new market rows. If live capture starts while BlackBox-V1 is pending:
- write records to the appropriate protected local data layer;
- do not copy row-level captured timestamps/prices into this research repository or chat;
- do not inspect or tune on them outside the permitted black-box/governance interface;
- later use requires an explicit data-role decision or pre-registered aggregate interface.

Synthetic integration tests and code-level recorder tests are not BlackBox market-data queries.

## 8. Current authority

Reference implementation may be published and tested now. Actual DataHub/live callback integration has not been executed by this cloud session.

Current intended state after reference acceptance:
`PROSPECTIVE_RECEPTION_RECORDER_V1_REFERENCE_ACCEPTED_LOCAL_INSTALL_PENDING`

This does not change:
- `D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED`;
- V19/D2/D3/D4/D5 scientific/engineering conclusions;
- `external_consumer_accepted=false`;
- `measured_feed_latency_supported=false`;
- `production_authority=false`.
