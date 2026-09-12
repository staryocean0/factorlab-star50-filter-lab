# DataHub reception cloud acceptance v1 — results

## Decision

**DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED**

GitHub Actions successfully reproduced the recorder/adapter engineering checks against the owner's already-uploaded handoff package. This closes the cloud-executable engineering acceptance gap. It does not create or recover a historical local reception clock and does not measure live feed/network latency.

## Authoritative execution

- workflow: `datahub-reception-cloud-acceptance`
- PR run id: `34666927078`
- job id: `103480600260`
- PR merge checkout SHA used by the run: `f6c3b462a01769dca83bfc5b6f549cd409e5b609`
- handoff branch commit/source: `bc84b65ba0510d164dbc90a01d3a98692982fc97`
- handoff ZIP bytes: `328518`
- handoff ZIP SHA256: `866824b8966b237ed8463afd6280186301db95c450876112da77787d5d50fa0d`
- evidence artifact id: `10288693269`
- artifact bytes: `4345`
- artifact ZIP SHA256: `627f7fb8e20f96133baa2691a3fcaaaf7d0fbc0dba6481645b516550f17b0ded`
- artifact retention expiry: `2026-12-11T02:10:35Z`

All workflow steps completed successfully, including V2 governance validation.

## Full historical handoff audit

The Action recovered the existing handoff ZIP directly from the repository handoff branch and verified the expected ZIP size and SHA before extraction.

It then checked every one of the 20 manifest entries against declared bytes and SHA256. All matched.

The full normalized sample was read and audited, not merely referenced:

- `000688.SH`: 4,746 rows
- `000852.SH`: 4,746 rows
- total rows independently verified: **9,492**
- trading day: `2025-06-11`
- first observation label: `09:25:00`
- last observation label: `15:00:03`
- both indices have the same 4,746-point observation grid: **exact match**
- each symbol has 1 open-call-auction row, 4,740 continuous-auction rows, and 5 close-auction rows
- gap-count profile is identical for both indices: 4,740 × 3s, 2 × 6s, 1 × 174s, 1 × 300s, 1 × 5,397s
- row index, symbol, trading day, source kind, source file, archive identity and dataset version consistency checks passed
- prices were finite and positive throughout
- no true local reception fields were present or fabricated

Observed price ranges in this one-day engineering sample:

- `000688.SH`: 980.29–990.14
- `000852.SH`: 6162.16–6221.20

These are descriptive sample facts, not new predictive findings.

## Real DataHub seam audit

The supplied DataHub source file SHA256 was reverified as:

`b9e8dad9ba2b50f38716bfa5f311dd5c918301f97b45c7ef85f83c67c6a42117`

AST/source-contract checks confirmed:

- `hq_api` is injectable;
- `quotes_parser` is injectable;
- `get_security_quotes` occurs at source line 105;
- `parse_quotes` occurs at source line 112;
- the HQ call precedes the parser call;
- local `datetime.now(UTC)` metadata exists in the DataHub path and is not promoted to vendor event time;
- accepted capture boundary remains `tdx_python_sdk_return_before_datahub_parser`;
- no wire-level arrival claim is made.

## Recorder/adapter tests

The Action ran the reference recorder and DataHub adapter suites together:

- 18 recorder tests: PASS
- 23 adapter tests: PASS
- total: **41 tests PASS**
- compile check: PASS

## Synthetic wrapper overhead

A descriptive GitHub-hosted-runner probe used 3,000 iterations with two quotes per iteration and produced 6,000 receipt plus 6,000 parsed records, with zero pending capture batches at completion.

Baseline two-quote call+parse timing:

- median: 1,313 ns
- p95: 1,402 ns
- p99: 1,810 ns

Wrapped timing:

- median: 60,609 ns
- p95: 97,012 ns
- p99: 110,922 ns

Descriptive incremental timing:

- median: 59,296 ns (~59.3 µs per two-quote synthetic iteration)
- p95: 95,610 ns
- p99: 109,112 ns

This is **only synthetic Python-wrapper overhead on a GitHub runner**. It is not live DataHub performance, feed latency, network latency or a production performance gate.

## Evidence hashes produced by the run

- `cloud_acceptance.json`: `4c6e89a29405b8ca992eda0a73be270050e8888c1fa0aecfd726211825001b7f`
- `cloud_acceptance.stdout.txt`: same content/hash
- `unit_tests.txt`: `39a7fdb519704c70270d37cd9962c59f664c3cbcca548cd9294f136c244e36f5`
- `synthetic_overhead.json`: `08716ffb99a6bdbea94ec6be7209a69612f398ed6a66926a016b07c5fbd4fafc`
- `synthetic_overhead.stdout.txt`: same content/hash

The first workflow version also included `SHA256SUMS.txt` in its own wildcard hash set, yielding the empty-file SHA for that entry. This bookkeeping issue does not affect any evidence file and is corrected in the workflow before merge.

## Interpretation and remaining boundary

Cloud-executable acceptance is complete. No additional historical raw-data proof or local-model engineering execution is required for this adapter decision.

The remaining unavailable evidence is a different object: genuine future local reception observations generated when the recorder is actually attached to a live local feed. GitHub Actions cannot manufacture those observations. Until governance-eligible true reception evidence exists:

- `live_recorder_installed=false`
- `true_reception_rows_collected=false`
- `measured_feed_latency_supported=false`
- `external_consumer_accepted=false`
- `blackbox_queried=false`
- `d6_started=false`
- `v20_started=false`
- `production_authority=false`
