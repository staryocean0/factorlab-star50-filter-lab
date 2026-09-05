# Current research entry

This entry follows the immutable `CONTINUE_HERE.md`, which is hash-bound by
the second-round research manifest. Preserve that file and both old bundles.

1. Third round: `docs/research/market_admission/report.md`.
   Official realtime STAR50 publication exists since2020-07-23; historical
   DataHub first/revised versions and actual reception clocks remain unproven.
   Official historical-data route identified; external market files received:0.
2. Cash ETF mapping is mechanically different:54.22% of frozen primary minute
    targets are short. After clipping shorts to cash, T+1 inventory still misses
    targets27.93% of minutes for baseline and29.36% for slow-conflict half.
    Both retain2 abstract locked units at the2025 terminal liquidation attempt.
    These are optimistic inventory diagnostics, not tradable PnL or MDD.
3. Read `docs/research/market_admission/data_request.json` for exact provenance,
    history, quote and account evidence needed. STAR50 ETF options did not exist
    before2023-06-05; no option strategy implemented. Do not backfill that period.
    Validate `python scripts/audit_market_admission.py --validate`.
    All five new annual sessions are sealed; do not overwrite them.
