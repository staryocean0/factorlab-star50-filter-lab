# V18 causal UNSAFE switch-on — frozen reusable Validation protocol

## Authorized question

Validate exactly the Development-supported V18 causal switch-on measurement on the repository's existing 2024–2025 3s reusable-Validation coverage.

The frozen primary signal remains:

`E-15s switch_on_signal = (frozen V9 partial_state == UNSAFE)`

This is an intrabar risk-state measurement, not a forecast of a shock before evidence exists and not a trading signal.

## Frozen identity

- V18 Development execution commit: `542b11857baeaebd43d93dc5ac866c6c3316e477`.
- exact V18 runner blob: `62c207badff1c3e37cbb1a8e17ef89feeea611d8`.
- V18 Development run: `34606023820`; artifact: `10266486662`.
- frozen V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`.
- source states: `NORMAL`, `RECOVERING` only.
- fixed checkpoints: `E-60s`, `E-30s`, `E-15s`, `E-6s`, `E-3s`; only `E-15s` is decisive.
- V9 thresholds/windows and V18 target/candidate/boundary logic are unchanged.

No threshold, feature, classifier, probability, smoothing, subgroup, or lead-time search is permitted.

## Validation boundary

- reference/warm-up files: 2020–2025 5m, only as required by the frozen causal state process;
- scored reusable Validation years: 2024 and 2025 only;
- 3s inputs: 2024 and 2025 only;
- no 2026 3s data may be read, synthesized, inferred, or claimed;
- BlackBox is not queried.

The frozen V9 causal boundary is retained: rows lacking the same-session previous close/background/prior window are excluded from the evaluable cohort; no overnight previous-close repair is introduced.

## Frozen target and signal

For each evaluable final 5m bar whose final previous state is `NORMAL` or `RECOVERING`:

- target = final 5m `risk_state == UNSAFE`;
- bars already coming from `UNSAFE` remain excluded as persistence rather than switch-on;
- at each fixed checkpoint, use the exact V18/V9 partial-bar construction;
- primary signal at E-15s is true iff the partial state is `UNSAFE`.

The full five-checkpoint curve is reported only as frozen evidence-accumulation diagnostics and cannot rescue E-15s.

## Fixed outputs

Report pooled E-15s precision, recall, false-positive rate, specificity, coverage, TP/FP/FN/TN, candidate count and true switch-on count; the same metrics by year, symbol and source state; pathway counts; boundary exclusions; and the frozen five-checkpoint evidence-accumulation curve.

## Acceptance

Reusable Validation is supported only if every condition holds without modification:

1. pooled candidate rows >= 30,000;
2. pooled true switch-on events >= 300;
3. each Validation year has >= 50 true switch-ons;
4. pooled E-15s checkpoint coverage >= 0.98;
5. each Validation year coverage >= 0.95;
6. pooled precision >= 0.90;
7. pooled recall >= 0.80;
8. pooled false-positive rate <= 0.01;
9. each Validation year precision >= 0.85;
10. each Validation year recall >= 0.70;
11. each Validation year false-positive rate <= 0.02;
12. both symbols have nonzero true switch-ons and nonzero E-15s true positives;
13. exact V18 and V9 runner blobs and all state thresholds remain unchanged;
14. no threshold/feature/probability/lead-time/subgroup search, PnL, payoff, routing, sizing, leverage, or trading rule is created;
15. only 2024–2025 3s Validation data are queried; no 2026 3s and no BlackBox.

Failure is final for this frozen V18 object and cannot be rescued by selecting E-3s/E-6s, changing thresholds, dropping a year/symbol/state, or redefining the target.

`production_authority=false`.
