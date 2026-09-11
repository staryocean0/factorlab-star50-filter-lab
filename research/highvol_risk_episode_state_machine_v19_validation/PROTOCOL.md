# V19 causal realtime risk-episode state machine — reusable Validation protocol

## Decision authority

This protocol is authorized under the user's standing delegation of mathematical research decisions. It validates the exact frozen V19 Development machine without refit or post-hoc rule changes.

## Frozen source authority

- V19 Development execution commit: `6fad49e5dc674d9a48b5c1719e060eceabc166d2`
- V19 Development runner blob: `ee2fce299d5ee21abf1ab2c2c5183bac101ae822`
- V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`
- V18 runner blob: `62c207badff1c3e37cbb1a8e17ef89feeea611d8`
- V17 runner blob: `397d80037806ba11cadf7f77717d36d55fbafc91`
- V16 frozen surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`

## Frozen machine

At exactly E-15s:

1. frozen V9 partial `UNSAFE` / `RECOVERING` is emitted immediately;
2. when frozen V9 partial state is `NORMAL` while the previous completed 5m state remains `UNSAFE` / `RECOVERING`, retain that previous risk state until bar close;
3. otherwise emit `NORMAL`.

No persistence length, threshold, lead time, probability, projection, feature, target, subgroup, or episode definition may be fitted or selected in Validation.

The reference E-15s state remains:

- current final 5m risk state when final state is `UNSAFE` / `RECOVERING`;
- otherwise previous finalized risk state until close when previous finalized state is risk;
- otherwise `NORMAL`.

## Data boundary

Reusable Validation uses:

- 5m reference history: 2020–2025, where 2020–2023 may only provide causal warm-up/history and scored Validation rows are 2024–2025;
- 3s observations: **2024 and 2025 only**;
- symbols: `000688.SH`, `000852.SH`;
- no 2026 3s data may be checked out, synthesized, queried, inferred, or claimed;
- no protected BlackBox data may be queried.

The same-session previous-close/background/prior-window boundary is unchanged. Rows lacking that chain remain excluded; no overnight repair is allowed.

## Frozen acceptance gates

All gates must pass simultaneously.

### Sample / coverage

- pooled evaluable checkpoints >= 30,000;
- pooled reference episodes >= 300;
- each Validation year reference episodes >= 50;
- pooled E-15s checkpoint coverage >= 0.98;
- each Validation year coverage >= 0.95.

### State classification

- pooled risk precision >= 0.98;
- pooled risk recall >= 0.98;
- pooled false-positive rate <= 0.005;
- each Validation year risk precision >= 0.95;
- each Validation year risk recall >= 0.95;
- each Validation year false-positive rate <= 0.01;
- pooled exact three-state agreement >= 0.90.

### Episode continuity

- reference episode capture rate >= 0.98;
- false machine-episode rate <= 0.10;
- reference episode fragmentation rate <= 0.05;
- pooled uncensored same-checkpoint onset rate >= 0.80;
- each Validation year uncensored same-checkpoint onset rate >= 0.70.

### Transition continuity

- `NORMAL -> UNSAFE` same-checkpoint UNSAFE recall >= 0.80;
- `RECOVERING -> UNSAFE` re-escalation recall >= 0.80;
- `UNSAFE -> RECOVERING` same-checkpoint recall >= 0.80;
- close-confirmed exit premature-NORMAL rate <= 0.02.

### Recovery attachment integrity

- every scored V16/V17 probability curve must satisfy `p15 <= p30 <= p60`;
- 60m must equal the frozen V16 recent-shock-age-only anchor exactly within `1e-15`.

### Governance

- frozen V19/V9/V18/V17/V16 identities unchanged;
- threshold search = false;
- lead-time search = false;
- persistence-length search = false;
- probability fit = false;
- projection change = false;
- post-hoc subgroup selection = false;
- queried 3s years exactly `[2024, 2025]`;
- queried 2026 3s = false;
- BlackBox queried = false;
- PnL computed = false;
- trading rule created = false;
- production authority = false.

## Decision rule

If every gate passes: `V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_REUSABLE_VALIDATION_SUPPORTED_2024_2025`.

If any scientific gate fails: seal the failure and do not refit V19 against Validation.
