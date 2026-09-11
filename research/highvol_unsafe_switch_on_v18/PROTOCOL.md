# V18 — causal UNSAFE switch-on evidence accumulation (Development)

## Purpose

V16/V17 validate the recovery side of the causal risk-state machine. V18 studies the missing entry side: **when does causal information already available inside a still-forming 5m bar justify switching into `UNSAFE`?**

This is not a return forecast and not a renewed attempt to predict the first shock before any evidence exists. Prior causal-volatility work already showed that ordinary-session first-shock prediction has poor recall. V18 instead measures evidence accumulation during the target 5m bar.

## Frozen state authority

- exact frozen V9 realtime state runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`;
- state constants unchanged: `RV_WINDOW=12`, `BG_WINDOW=48`, `HIGHVOL_RATIO=1.50`, `RECOVERY_NORMAL_RATIO=1.10`, `SHOCK_SIGMA=3.00`;
- symbols: `000688.SH`, `000852.SH`;
- Development: 2021-01-01 through 2023-12-31; 2020 reference/warm-up only;
- 3s Development inputs: 2021-2023 only.

Validation, 2024+, 2026, and BlackBox are physically excluded.

## Frozen evaluable cohort and target

The V18 causal-evaluable cohort is every final 5m bar in Development whose:

1. final previous state is `NORMAL` or `RECOVERING`;
2. frozen V9 has the required prior return window, previous close and background volatility needed to form the partial-bar state.

The first 5m bar of a trading day is therefore outside the V18 evaluable cohort because frozen V9 deliberately resets the same-day previous-close chain. V18 will report these boundary exclusions separately and will **not** import an overnight previous close or invent a new opening-bar rule.

Within the frozen evaluable cohort:

- positive switch-on target: final 5m `risk_state == UNSAFE`;
- negative control: final 5m `risk_state != UNSAFE`.

Bars already coming from `UNSAFE` are excluded because they are persistence, not switch-on.

The positive target has two descriptive pathways under the unchanged state machine:

1. shock entry: final `shock == true`;
2. recovery re-escalation: previous state `RECOVERING`, no final shock, and final volatility ratio is high enough to return to `UNSAFE`.

No pathway-specific rule is fitted.

## Frozen realtime signal

At fixed checkpoints `E-60s`, `E-30s`, `E-15s`, `E-6s`, `E-3s`, use the exact V9 partial-bar construction:

1. select the latest same-bar 3s observation at or before the checkpoint;
2. compute partial 5m return from the frozen previous close;
3. recompute rolling volatility and shock intensity using the frozen V9 windows;
4. run the unchanged V9 state transition from the **final previous state**;
5. emit `switch_on_signal = (partial_state == UNSAFE)`.

No probability model, classifier, threshold, smoothing rule, or checkpoint is fitted.

`E-15s` is the preregistered **primary checkpoint** because V10/V17 already establish E-15s as the current realtime risk checkpoint. The other four checkpoints are a fixed descriptive evidence-accumulation curve and cannot rescue an E-15s failure.

## Fixed outputs

For every checkpoint, pooled and by source state / year / symbol where applicable:

- candidate rows and checkpoint coverage;
- final UNSAFE-entry prevalence;
- signal count;
- precision, recall, false-positive rate, specificity;
- TP / FP / FN / TN;
- partial shock rate among true positives and false positives;
- partial volatility-ratio distribution summaries;
- final switch-on pathway counts.

Across the fixed checkpoint curve, also report:

- cumulative fraction of true switch-ons detected by each checkpoint;
- earliest checkpoint at which each true event first becomes `UNSAFE`;
- whether a signalled event remains `UNSAFE` at all later checkpoints;
- late-forming events that are first detected after E-15s;
- opening / missing-reference boundary exclusions.

These are diagnostics only; no checkpoint selection is allowed.

## Development acceptance

V18 is **Development-supported** only if every condition below holds at the frozen `E-15s` primary checkpoint:

1. pooled candidate rows >= 30,000;
2. pooled true switch-on events >= 300;
3. each Development year contains >= 50 true switch-on events;
4. pooled checkpoint coverage >= 0.98;
5. each Development year coverage >= 0.95;
6. pooled precision >= 0.90;
7. pooled recall >= 0.80;
8. pooled false-positive rate <= 0.01;
9. each Development year precision >= 0.85;
10. each Development year recall >= 0.70;
11. each Development year false-positive rate <= 0.02;
12. both symbols have nonzero true switch-on events and nonzero E-15s true positives;
13. V9 runner blob and all state thresholds remain unchanged;
14. no threshold search, feature search, probability fit, lead-time selection, post-hoc subgroup selection, PnL, payoff, routing, sizing, leverage, or trading rule is created;
15. Validation and BlackBox are not queried.

Failure cannot be rescued by selecting E-3s/E-6s, changing the target, dropping a year/symbol/source state, or relaxing thresholds after inspection.

A Development PASS makes this exact switch-on measurement **eligible for a separately authorized reusable Validation**. It does not itself authorize Validation, BlackBox, or production use.

`production_authority=false`.
