# STAR50 / CSI1000 AI entry — prospective reception recorder reference accepted

Read `AGENTS.md`, `CURRENT_RESEARCH.md` and `CONTINUE_HERE.md` first.
Current authority: `research/prospective_reception_recorder_v1/PROGRAM_STATE.json`, `PROTOCOL.md`, `SCHEMA.json`, `EXECUTION_RECEIPT.json`.

Current state: `PROSPECTIVE_RECEPTION_RECORDER_V1_REFERENCE_ACCEPTED_LOCAL_INSTALL_PENDING`.

Historical D5R remains `D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED`: no per-tick true local received_at exists for `000688.SH` / `000852.SH`; do not infer one from available_at, batch ingested_at, mtime, observation time or row order.

The reference recorder now defines the only acceptable forward path: stamp UTC wall-clock, monotonic_ns, local sequence and raw payload identity at the actual feed callback before parsing/queueing, then parse market event time/symbol/price. 18 synthetic tests, compile and independent validator sample passed in chat. No live DataHub installation or real reception rows yet.

New post-2026-08-21 market rows may belong to pending BlackBox-V1. Local installation may proceed with synthetic/allowed replay tests; any real capture must stay protected locally until governance permits use. Do not upload row-level new market data to public GitHub/chat.

Keep V19/D2-D5 conclusions unchanged. No D6/V20, payoff/router, new 2026 research, BlackBox query, PnL or production authority. `production_authority=false`.
