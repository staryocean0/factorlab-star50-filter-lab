# Causal K-line state delivery V1 — contract and implementation boundary

This is an engineering delivery version, not a new risk estimator or V20.
Current direction authority: `docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md`.

## Implemented slice

`adapter.py` accepts keyword-only, causal E-15 inputs: symbol, bar end, previous completed bar end/state/known time, frozen V9 partial state and observation/known times, upstream reference/checkpoint validity, V9 blob identity and timing basis, and publication time.

The frozen machine mapping is partial UNSAFE/RECOVERING immediately; otherwise retain prior confirmed risk while an exit is pending; otherwise NORMAL. Input authority is V9 blob `ae2a7e095df58692ef9df0dfee5856cac727ca44`; the mapped V19 rule is blob `ee2fce299d5ee21abf1ab2c2c5183bac101ae822`.

The function does not calculate V9 from raw prices. A caller-supplied blob ID is provenance metadata, not proof of upstream computational correctness. The nine-state-combination unit test checks the rule table; full-engine numeric parity remains pending.

The adapter is bounded to the two index symbols and 2021–2025 timestamps. Synthetic inputs are not market evidence or a data grant. It does not read any data files or contact services.

## Clock contract

- All times are timezone-aware. Bar end identifies the current bar, not the availability of its final state.
- decision_time = bar_end minus 15 seconds.
- A previous final state cannot be known before that previous bar closes; the bar must not overlap the current bar.
- Observation time and causal known time must be no later than decision_time. The observation must lie strictly after current bar start.
- published_at cannot precede decision_time. Consumers cannot use a snapshot before publication, even if its inputs were already available.
- `visible_at` exposes a snapshot only from its published_at until, but not including, current bar close. A delayed publication at/after close never becomes a timely E-15 snapshot.
- No extra staleness threshold or session/cohort repair is introduced here. `reference_chain_valid` and `checkpoint_available` must come from the unchanged frozen upstream guards; their end-to-end enforcement remains D2 work.
- Existing historical `available_at` is deliberately not accepted. `owner_realtime_assumption` describes historical causal replay under the owner's field clarification; `observed_reception_log` is permitted only when actual logs support it. The prototype does not manufacture or authenticate such logs.

## Output and consumer semantics

An immutable Annotation includes state, previous_confirmed_state, partial_state, transition, state_basis, exit_pending, availability_reason, clock/provenance fields and a derived bucket_key.

`transition` compares the previous completed 5m state with the current delivered state. It is not yet a deduplicated stream event or full-episode identifier.

`E15_PROVISIONAL` identifies a current provisional observation, including provisional NORMAL. `PRIOR_CONFIRMED_EXIT_PENDING` identifies retained prior risk while current partial NORMAL awaits close confirmation. Neither status is a trading instruction.

Missing references/checkpoints or inputs not known by the decision yield state=null, bucket_key=UNAVAILABLE and a reason; input state fields are also suppressed to prevent a downstream bypass. Malformed timestamps, unsupported vocabulary/identity/symbols and unexpected extra fields raise errors. UNAVAILABLE must never be converted into NORMAL.

At E-15, current final_state, reference state, retrospective episode end/duration, future return and historical available_at are not arguments. Evaluator labels belong in a separate table.

Recovery probabilities are explicitly null with reason NOT_ATTACHED_IN_CONTRACT_SLICE. This is not a zero-probability prediction and not an alteration of V17 gating. Every output carries production_authority=false.

Examples of attribute keys are UNSAFE|E15_PROVISIONAL and RECOVERING|PRIOR_CONFIRMED_EXIT_PENDING. They are descriptive risk axes for a consumer's own bucketing, not Range/UpTrend/DownTrend classification, trade_allowed, buy/sell, sizing or a strategy router.

## Tests and what they do not establish

Run in the repository root:

```bash
python -m unittest discover -s research/causal_state_delivery_v1 -p 'test_*.py' -v
```

Tests cover 9 state combinations, missing/future inputs, publication timing, refusal of retrospective inputs, immutable records, expiry at close, explicit transition/exit status, identity/symbol/scope and absence of trading/probability claims.

These are synthetic contract/unit tests. They do not establish real-market latency, full data-pipeline causality, source authenticity, market replay equivalence, useful future-risk separation, probability calibration or economic benefit.

## Pending delivery work — D2

Implement a separate close-event adapter, frozen V16/V17 probability attachment with its original gates, ordered/append-only event ledger and as-of consumer replay. Bind the exact source/config/data manifests, then test original available-row parity, missingness, censoring/session semantics, effective lead time and invariance of published prefixes under later data changes.

## Pending application-oriented research — D3

Before running outcome-based comparisons, preregister the bounded risk endpoints, non-overlapping input/label clocks, baselines, minimum practical effect and uncertainty method in a separate protocol. Existing Validation is reusable, never fresh OOS. No strategy, BlackBox or production authority is added by this contract.
