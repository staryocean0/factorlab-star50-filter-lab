# V19 causal realtime risk-episode state machine — Development protocol

## Question

Does the already frozen entry/recovery stack form a stable causal realtime **episode-level** risk state machine at the existing `E-15s` checkpoint, without changing V9/V16/V17/V18 thresholds, probabilities, checkpoint, target, or data roles?

V19 is not a new directional/payoff model. It does not predict returns, optimize trades, or reopen first-shock forecasting.

## Frozen upstream authority

V19 must preserve these exact authorities:

- V9 causal partial-state runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`;
- V18 Development runner blob: `62c207badff1c3e37cbb1a8e17ef89feeea611d8`;
- V17 Development runner blob: `397d80037806ba11cadf7f77717d36d55fbafc91`;
- V16 frozen surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`;
- checkpoint: exactly `E-15s`;
- V9 constants: `RV_WINDOW=12`, `BG_WINDOW=48`, `HIGHVOL_RATIO=1.5`, `RECOVERY_NORMAL_RATIO=1.1`, `SHOCK_SIGMA=3.0`.

## Data boundary

Development only:

- 2020 5m may be read only as warm-up/reference history;
- scored Development years: 2021, 2022, 2023;
- 3s inputs: 2021, 2022, 2023 only;
- no 2024+ Validation data;
- no 2026 3s;
- no protected BlackBox.

Rows without the frozen V9 same-session previous close, background volatility, prior return window, or E-15s 3s checkpoint are unavailable. No overnight previous-close repair is allowed.

## Primary causal state machine

For every evaluable 5m bar, the previous completed 5m state is already known at E-15s. Let `partial_state` be the exact frozen V9 state computed from data available at E-15s.

The V19 primary machine state is deterministic:

1. if `partial_state` is `UNSAFE` or `RECOVERING`, emit that partial state immediately;
2. if `partial_state == NORMAL` and the previous completed 5m state is `UNSAFE` or `RECOVERING`, retain that previous risk state until bar close (`close-confirmed exit`);
3. otherwise emit `NORMAL`.

There is no tunable persistence length. The only exit hysteresis is the already implied V17 rule that a provisional E-15s `NORMAL` is not sufficient to emit a realtime recovery probability / declare the risk episode closed before the bar itself closes.

The raw frozen V9 `partial_state` sequence is retained as a diagnostic comparator only. It cannot replace the primary machine after results are observed.

## Retrospective E-15s reference state

The reference answers what state should still be considered active at E-15s under the same close-confirmed-exit semantics:

1. if the current final 5m state is `UNSAFE` or `RECOVERING`, use the current final state;
2. otherwise, if the previous completed 5m state is `UNSAFE` or `RECOVERING`, retain that previous state until the current bar closes;
3. otherwise use `NORMAL`.

This reference is used only for evaluation. It is not available to the realtime machine.

## Episode definition

Within each symbol and trading day, a risk episode is a maximal contiguous run of E-15s reference states in `{UNSAFE, RECOVERING}`. A machine episode is the analogous maximal contiguous run of primary machine states in `{UNSAFE, RECOVERING}`.

Opening/session-boundary episodes whose beginning lies outside the causal-evaluable cohort are marked left-censored and excluded from onset-timing gates. End-of-day active episodes are marked right-censored where applicable.

A reference episode is captured if any machine risk checkpoint overlaps it. It is fragmented if more than one machine episode overlaps it. A machine episode is false if it overlaps no reference episode.

## Transition classes

The following final-5m transitions are fixed diagnostics:

- `NORMAL -> UNSAFE`: switch-on;
- `RECOVERING -> UNSAFE`: re-escalation;
- `UNSAFE -> RECOVERING`: recovery transition;
- risk-state holds;
- `UNSAFE/RECOVERING -> NORMAL`: close-confirmed exit rows.

No pathway-specific threshold may be fitted.

## Frozen V16/V17 recovery attachment

Where the E-15s frozen V9 partial state is `UNSAFE` or `RECOVERING`, no fresh partial shock is present, and a causal prior finalized shock exists, attach the exact frozen V16/V17 recovery surface:

- 15m: frozen `state + recent-shock-age` probability using the E-15s partial state;
- 30m: frozen `state + recent-shock-age` probability using the E-15s partial state;
- 60m: frozen recent-shock-age-only anchor.

If the current partial state is `NORMAL`, a fresh partial shock exists, or the recent-shock age is unavailable, recovery probabilities remain unavailable. V19 does not fit probabilities.

## Preregistered Development acceptance

V19 Development is supported only if **all** are true:

### Data / identity

- pooled evaluable checkpoints >= 30,000;
- pooled reference episodes >= 300;
- each Development year has >= 50 reference episodes;
- pooled E-15s checkpoint coverage >= 0.98;
- each year checkpoint coverage >= 0.95;
- exact upstream blob / constant guards pass.

### Primary checkpoint state quality

- pooled risk precision >= 0.98;
- pooled risk recall >= 0.98;
- pooled false-positive rate <= 0.005;
- each year risk precision >= 0.95;
- each year risk recall >= 0.95;
- each year false-positive rate <= 0.01;
- pooled exact three-state agreement >= 0.90.

### Episode continuity

- pooled reference-episode capture rate >= 0.98;
- pooled false machine-episode rate <= 0.10;
- pooled reference-episode fragmentation rate <= 0.05;
- uncensored reference-episode same-checkpoint onset rate >= 0.80;
- each year uncensored same-checkpoint onset rate >= 0.70.

### Transition continuity

- pooled `NORMAL -> UNSAFE` same-checkpoint UNSAFE recall >= 0.80;
- pooled `RECOVERING -> UNSAFE` same-checkpoint UNSAFE recall >= 0.80;
- pooled `UNSAFE -> RECOVERING` same-checkpoint RECOVERING recall >= 0.80;
- close-confirmed risk rows have premature-NORMAL rate <= 0.02.

### Recovery-surface integrity

- every scored V16/V17 probability row satisfies `p15 <= p30 <= p60`;
- 60m equals the frozen age-only anchor exactly within `1e-15`;
- no probability fit, threshold search, lead-time search, persistence-length search, projection change, or post-hoc subgroup selection occurs.

### Governance

- Validation not queried;
- 2024+ 3s not queried;
- 2026 3s not queried;
- BlackBox not queried;
- PnL not computed;
- no trading rule created;
- `production_authority=false`.

## Decisive outcomes

If all gates pass:

`FREEZE_V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_AND_STOP_BEFORE_VALIDATION`

If any gate fails:

`V19_DEVELOPMENT_REJECTED_OR_DIAGNOSTIC_ONLY`

A failure cannot be rescued by switching to the raw partial sequence, selecting E-6s/E-3s, changing hysteresis, changing thresholds, or looking at Validation.
