# STAR50 / CSI1000 risk research data requirements

Date: 2026-09-07.

Purpose: provide a compact contract that a shared data tool can satisfy for this repository without re-reading the full research history.

## Priority A — core required data

These are sufficient to maintain the validated `first shock -> Unsafe -> Recovering score` research line.

### A1. Native 1-minute index bars — REQUIRED

Symbols:
- `000688.SH` STAR50
- `000852.SH` CSI1000

Coverage:
- preserve existing sealed history;
- append new complete trading days after the current same-semantics snapshot (`2026-08-21`) in separately versioned incremental packs;
- do not rewrite old manifests/hashes.

Required fields/semantics:
- `symbol`
- `timestamp`
- `trading_day`
- `open/high/low/close`
- `amount` if source supplies it
- `volume` if source supplies it; do not fabricate
- `causal_flat_fill`
- `source_minute_count`
- `high_frequency_analysis_eligible`
- `source_kind`
- `dataset_version`
- export/source identity and historical availability metadata already used by DataHub

Consumer rules:
- Shanghai wall-clock/session semantics must be explicit;
- no interpolation across missing source support;
- repair/flat-fill rows remain identifiable;
- only complete trading days enter validation snapshots.

Research uses:
- frozen first-shock event detection;
- pre-shock `sigma_pre`;
- current trailing-5m RMS / `sigma_pre` recovery score;
- Unsafe/Recovering duration and censoring evaluation.

**Important: the currently supported recovery state can be computed from this 1-minute layer alone.**

### A2. Manifest / receipt — REQUIRED

For every incremental snapshot or file, provide:
- SHA256
- rows
- first/last trading day
- number of complete trading days
- symbol/frequency
- timezone/timestamp semantics
- parent dataset/export version
- source file/version identity
- quality/repair counts when available
- snapshot cutoff date
- explicit statement that no rows after the cutoff are present

Incremental packs must be append-only/versioned. Never mutate sealed 2021-2025 or existing 2026 validation manifests to make a new snapshot look continuous.

## Priority B — important research support

### B1. 3-second index source observations — IMPORTANT, not required for the core Recovering score

Symbols:
- `000688.SH`
- `000852.SH`

Coverage:
- continue after the current same-semantics cutoff `2026-08-21` whenever authoritative source support becomes available;
- preserve prior history and same-second source rows.

Required fields:
- `symbol`
- `observation_datetime`
- `trading_day`
- `price`
- `row_index`
- `amount` if supplied
- `volume` if supplied; null is acceptable
- source/dataset version fields
- source archive/file identity

Rules:
- source `Z` suffix semantics must remain documented as Shanghai wall-clock labels if that source convention continues;
- keep `(symbol, observation_datetime, row_index)` ordering;
- no silent same-second deduplication;
- no interpolation across source gaps;
- provide gap/coverage statistics by year/snapshot.

Research uses:
- path and endpoint-semantic audits;
- distinguishing concentrated moves, directional continuation and round trips;
- future pre-registered alternative release features;
- measurement quality checks between minute and high-frequency exports.

This layer should not be treated as transaction/event-count intensity, order flow, cancellations or order-book depth.

## Priority C — materially different information that could justify reopening online Clean research

These are OPTIONAL. Do not block the current repository on them. They are useful only if the shared data project can support them with reliable point-in-time semantics.

### C1. Point-in-time index constituent cross-section — highest-value optional extension

For STAR50 and CSI1000:
- historical point-in-time constituent membership and index weights;
- constituent 1-minute bars on matching trading days;
- preferably amount/turnover and suspension/quality flags.

Desired derived research capability:
- cross-sectional breadth of large moves;
- weighted dispersion;
- share of constituents remaining high-volatility after the index shock;
- synchronized vs concentrated constituent stress.

Reason: this is materially different from the index's own price history and may help distinguish persistent systemic stress from an index move that is already dissipating.

### C2. True tradable-market microstructure for a frozen representative carrier — optional

If available, select and freeze representative liquid instruments for each index exposure rather than mixing arbitrary products after seeing results.

Useful fields:
- best bid/ask and spread;
- multiple-depth levels if available;
- quote sizes/depth;
- true trade prints and aggressor side if available;
- queue/order imbalance measures derivable from raw quotes;
- cancellations only if source truly identifies them.

Reason: current index 3s snapshots cannot supply OFI, depth, queue imbalance or cancellation intensity. True market microstructure would be materially different information for future Clean-release research.

### C3. Scheduled event/context calendar — optional

Point-in-time timestamps for major scheduled macro/index-relevant events, with no future leakage. Use only as an explicit external-context feature in a new preregistered protocol.

## Snapshot cadence requested from the shared data tool

For Priority A/B, prefer a stable incremental process:
- source of truth remains DataHub;
- export only completed trading days;
- produce a new immutable snapshot/manifest when the same-semantics source advances materially;
- monthly snapshots are sufficient for research operations, but any cadence is acceptable if each cutoff is explicit;
- never silently revise past bytes; revisions require a new version plus a repair/change receipt.

## Current known cutoff and next useful independent data

Current same-semantics validation support ends at `2026-08-21`.

The next genuinely independent time extension begins **after 2026-08-21**. New days should be kept untouched by model tuning until a new validation protocol is frozen.

## What this repository does NOT need now

- ETF/options/futures data for the core Unsafe/Recovering state;
- order book data pretending to exist for the index itself;
- 2021-2025 re-export;
- new resampled OHLC frequencies created ad hoc;
- trading/account/order data;
- production serving grants.
