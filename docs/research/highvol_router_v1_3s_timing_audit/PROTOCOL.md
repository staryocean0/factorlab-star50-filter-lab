# HighVol Router V1 — 3s index timing audit protocol

Role: diagnostic-only timestamp/observation audit of the already frozen HighVol Router V1. This is **not** a tradable fill study.

The audit asks whether the frozen 1-minute `open` entry/exit return is materially sensitive to replacing each target minute open with the first causally visible CSI1000 3-second **index observation** after a fixed delay.

## Frozen strategy object

No Router V1 selector, route, threshold, entry minute, exit minute, hold, cost, overlap rule, or acceptance decision may change.

- signal source: `000852.SH` 1-minute index data;
- route: CSI1000 active long 3-minute module only;
- STAR50 and unsupported HighVol contexts remain `NO_TRADE`;
- baseline entry = frozen next-minute 1m open;
- baseline exit = frozen open exactly 3 minutes later.

## Data roles

- 1m signal/frozen trade reconstruction: 2020 warm-up plus 2021–2025 `000852.SH` bounded index files.
- 3s timestamp audit: `data/cross_index_risk_gate_3s_v1/000852.SH_YEAR.parquet`, years 2021–2025 only.
- Development diagnosis: 2021–2023.
- reusable Validation diagnosis: 2024–2025 only.
- 2026 is **not** part of this audit because the authorized 3s cloud package ends 2025-12-31.
- BlackBox-V1 is not queried.

## Fixed causal observation mappings

For each frozen trade and for each delay `d` in exactly `{0, 3, 6, 15}` seconds:

1. compute the target entry minute start and target exit minute start from the frozen session/minute identity;
2. entry proxy = first 3s source observation with observation time `>= entry_target + d` and `< entry_target + 60 seconds`;
3. exit proxy = first 3s source observation with observation time `>= exit_target + d` and `< exit_target + 60 seconds`;
4. if either side has no valid positive price in that window, mark the trade unmatched for that delay;
5. preserve source order for equal timestamps using `row_index` if that field exists;
6. no interpolation, no nearest-earlier observation, no best-price selection, no resampling.

The 3s source is an index snapshot/observation stream, not a tradeable quote. `delay=0` is therefore only a timestamp-alignment proxy, not an executable fill.

## Fixed outputs

For Development and Validation-2024/25 separately, and by calendar year:

- frozen 1m trade count;
- matched count and match rate at each delay;
- median and p95 realized source latency relative to `target+d` for entry and exit;
- mean/median 1m-open gross return;
- mean/median 3s-observation gross return;
- mean/median `(3s gross - 1m gross)` timing drift;
- mean net at the unchanged abstract 1 bp/leg cost, for comparability only;
- one-way break-even of the 3s-observation gross return;
- sign agreement between 1m and 3s gross returns.

Also report the distribution of per-trade timing drift and exact source column identity detected from the parquet schema.

## Interpretation

A negative timing drift can weaken confidence that minute-open marks faithfully represent the index path immediately after the signal. A positive drift cannot be treated as achievable alpha or price improvement because the 3s source is not an executable carrier.

This audit cannot rescue or reject Router V1 by changing parameters. It only qualifies timestamp semantics. Real execution still requires a tradable carrier with bid/ask/fees/slippage evidence under `CL-HIGHVOL-ROUTER-EXEC-20260909`.

`production_authority=false`. BlackBox query count remains zero.
