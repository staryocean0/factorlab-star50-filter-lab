# STAR50 / CSI1000 AI entry — D2 accepted, D3 preregistration next

Read AGENTS.md, CURRENT_RESEARCH.md and CONTINUE_HERE.md. Direction: docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md. Current status: research/causal_state_delivery_d2/PROGRAM_STATE.json, RESULTS.md and EXECUTION_RECEIPT.json.

D2_CAUSAL_REPLAY_SUPPORTED_D3_NOT_EXECUTED. Independent chronological raw-price replay preserved all 113928 original E15 rows with zero state/probability mismatch; 232704 E15/CLOSE events and 20 market prefix checks passed. D1's 20 and D2's 38 tests passed. Original D1 files/receipt remain sealed, not the current breakpoint.

Purpose: causal K-line risk-attribute changes for downstream state/strategy bucketing. No strategy actions, payoff routing, parent Range/UpTrend/DownTrend classifier or production serving. V19 remains frozen; no residual-optimization V20.

Next task is D3 protocol-first non-PnL incremental risk-bucket utility evaluation. Account for first-bar unavailability, lunch/day-end/forward-window boundaries, and observation freshness: all 2424 E15 observations older than120s occur at the15:00 bar. Do not erase them or change the baseline after inspection. Ideal15s publication timing is an assumption, not measured live latency.

V2 permits Development fitting and reusable Validation diagnostics but no fitting the candidate under test on Validation and no fresh-OOS claim. No2026 3s, protected data, BlackBox or production authority. Historical available_at is not intraday latency.

Older entry text remains at commit766dd6f5293a1fa8588edabe368088f63981fa1a. Historical Current/Latest instructions do not override this entry. production_authority=false.
