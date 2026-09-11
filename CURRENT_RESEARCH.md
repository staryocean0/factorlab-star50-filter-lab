# Current research entry

## 2026-09-11 current authority

**Current task: STAR50 / CSI1000 bottom-layer K-line risk-state research only.**

The research product of this bucket is a causal risk annotation/state machine. It is not a directional trading strategy.

## Current integrated episode-level authority — V19 Development

V19 tests whether the already frozen entry and recovery components form one coherent causal realtime risk-episode state machine at the existing `E-15s` checkpoint.

V19 does **not** refit V9/V16/V17/V18, does not change E-15s, and does not optimize a persistence length. Its only hysteresis rule is deterministic and risk-first:

1. frozen V9 partial `UNSAFE` / `RECOVERING` is emitted immediately at E-15s;
2. if partial state is `NORMAL` while the previous completed 5m state is still `UNSAFE` / `RECOVERING`, retain the previous risk state until the bar actually closes;
3. otherwise emit `NORMAL`.

This is the close-confirmed-exit semantics already implied by V17's `provisional_normal = unavailable` gating.

### Frozen V19 Development authority

- branch: `research/highvol-risk-episode-state-machine-v19-20260911`;
- execution commit: `6fad49e5dc674d9a48b5c1719e060eceabc166d2`;
- run: `34611126345`;
- job: `103301597623`;
- artifact: `10267923594`;
- artifact SHA256: `3d64999976ca5ad001e7924aa4d6e668e412411e58e1bb10daebb747f4ee5aea`;
- Development years: 2021-2023 only;
- 3s queried: 2021-2023 only;
- evaluable E-15s checkpoints: `68,338`;
- `development_supported=true`;
- `validation_eligible_but_not_authorized=true`.

Exact upstream identity guards passed:

- V9 runner blob `ae2a7e095df58692ef9df0dfee5856cac727ca44`;
- V18 runner blob `62c207badff1c3e37cbb1a8e17ef89feeea611d8`;
- V17 runner blob `397d80037806ba11cadf7f77717d36d55fbafc91`;
- V16 frozen surface blob `1f88966cf5dd3fb102f0d75746d5d00434555647`.

### V19 pooled checkpoint result

Across 68,338 evaluable checkpoints:

- reference E-15s risk rows: `9,613`;
- machine risk rows: `9,561`;
- TP / FP / FN / TN: `9531 / 30 / 82 / 58695`;
- risk precision: **`0.9968622529`**;
- risk recall: **`0.9914698845`**;
- false-positive rate: **`0.0005108557`**;
- exact three-state agreement: **`0.9975123650`**.

The raw frozen V9 E-15s partial sequence, used only as a diagnostic comparator, had risk recall `0.9027358785` and exact three-state agreement `0.9851034563`. The close-confirmed exit rule therefore removes most premature-safe flicker without increasing the already-low false-positive rate.

Annual primary-machine risk recall remains high:

- 2021: `0.998767`;
- 2022: `0.990690`;
- 2023: `0.984306`.

### V19 episode-level result

Reference E-15s risk episodes: `867`.
Machine episodes: `890`.

- captured reference episodes: `861 / 867`;
- capture rate: **`0.9930795848`**;
- fragmented reference episodes: **`0`**;
- fragmentation rate: **`0.0`**;
- false machine episodes: `29 / 890`;
- false machine-episode rate: **`0.0325842697`**;
- same-checkpoint onset: `785 / 867`;
- same-checkpoint onset rate: **`0.9054209919`**;
- onset-lag median: `0` checkpoints;
- maximum onset lag among captured episodes: `1` checkpoint.

Annual episode capture / same-checkpoint onset:

- 2021: `0.986486 / 0.986486`;
- 2022: `0.996656 / 0.892977`;
- 2023: `0.996324 / 0.830882`.

All preregistered episode gates passed.

### V19 transition continuity

At the unchanged E-15s checkpoint:

- `NORMAL -> UNSAFE`: `794 / 876`, recall **`0.9063926941`**;
- `RECOVERING -> UNSAFE`: `463 / 485`, recall **`0.9546391753`**;
- `UNSAFE -> RECOVERING`: `1083 / 1097`, recall **`0.9872379216`**.

Close-confirmed exits are the key hysteresis result:

- exit rows: `853`;
- V19 primary-machine premature `NORMAL`: **`0 / 853`**;
- raw partial state was already `NORMAL` on `844 / 853` exit rows.

Therefore a raw partial-state sequence would almost always declare safety during the final 15 seconds of the exit bar, while V19's frozen close-confirmed rule preserves risk continuity until the final 5m state is actually known.

### V16/V17 recovery attachment inside V19

V19 attaches the existing frozen recovery probabilities only where V17 gating permits:

- scored rows: `7,716`;
- probability coverage of machine risk rows: `0.8070285535`;
- all scored rows satisfy `p15 <= p30 <= p60`;
- maximum absolute 60m frozen age-anchor difference: `0.0`.

No probability was fitted or changed.

Primary sealed V19 evidence:

- `research/highvol_risk_episode_state_machine_v19/PROTOCOL.md`;
- `research/highvol_risk_episode_state_machine_v19/FROZEN_DEVELOPMENT_CONTRACT.json`;
- `research/highvol_risk_episode_state_machine_v19/DEVELOPMENT_RESULTS.md`;
- `research/highvol_risk_episode_state_machine_v19/DECISIVE_RECEIPT.json`.

The decisive V19 action is:

`FREEZE_V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_AND_STOP_BEFORE_VALIDATION`

A reusable Validation is scientifically eligible but has **not** been authorized or run.

## Current validated switch-on component — V18

V18 remains the validated entry-side component. It measures causal intrabar `NORMAL/RECOVERING -> UNSAFE` switch-on at exactly E-15s using the unchanged frozen V9 state machine.

Reusable Validation authority:

- run `34607566312`;
- artifact `10265993683`;
- Validation period: 2024-2025 only;
- evaluable bars: `43,793`;
- true switch-ons: `810`;
- E-15s precision / recall / FPR: `0.9511228534 / 0.8888888889 / 0.0008608054`;
- both years and both indices passed;
- `full_validation_supported=true`.

V18 does not claim to predict the first shock before within-bar evidence exists. E-6s/E-3s remain diagnostics and cannot replace E-15s post hoc.

## Current validated realtime recovery component — V17

V17 remains the validated recovery-side realtime authority on available 2024-2025 3s coverage. At E-15s it transfers the frozen V16 horizon-adaptive recovery object without refit:

- 15m = frozen V16 `state + recent-shock age` using frozen V9 provisional state;
- 30m = frozen V16 `state + recent-shock age` using frozen V9 provisional state;
- 60m = frozen V16 recent-shock-age-only anchor.

V17 reusable Validation: run `34604089926`, artifact `10265472702`, 4,540 cohort rows, 4,516 realtime-scored, coverage `0.9947136564`, `full_validation_supported=true`.

## Current validated final-5m recovery component — V16

V16 remains the final-5m recovery authority through `2026-08-21`:

- 15m = `current_state + time-since-most-recent-shock`;
- 30m = `current_state + time-since-most-recent-shock`;
- 60m = `time-since-most-recent-shock only`.

V16 reusable Validation: run `34602527314`, artifact `10264689647`, 5,908 scored rows through 2026-08-21, `full_validation_supported=true`.

The recovery clock rule remains:

> Every new shock resets the recovery clock. Recovery risk is indexed by time since the most recent shock, not time since the first shock of the episode.

## Current supported causal risk architecture

The component-level validated architecture plus V19 Development integration is now:

`V18 switch-on -> V19 close-confirmed episode continuity -> UNSAFE / RECOVERING -> V17/V16 recovery surface -> close-confirmed Normal`

Important authority distinction:

1. V18 switch-on is reusable-Validation supported on 2024-2025 3s;
2. V17 realtime recovery is reusable-Validation supported on 2024-2025 3s;
3. V16 final-5m recovery is reusable-Validation supported through 2026-08-21;
4. **V19 integrated episode-level state machine is Development-supported only until separately authorized Validation.**

## Completed evidence chain that must not be casually reopened

- V3-V6: post-shock recovery-state / recent-shock-age mechanism;
- V7: frozen 1m realtime recall gate failed;
- V8-V10: 3s realtime state/probability transfer and E-15s checkpoint;
- V11-V15: horizon-dependent state value; unified 60m state+age surface rejected;
- V16: frozen and validated horizon-adaptive final-5m recovery surface;
- V17: validated E-15s realtime recovery transfer;
- V18: validated E-15s causal UNSAFE switch-on;
- V19: Development-supported E-15s close-confirmed episode-level state machine.

Do not rerun these versions merely to reconfirm them.

## Scope-repaired bucket authority

This repository owns bottom-layer causal K-line risk-state research only, including volatility level/expansion, shock isolation/recurrence, `Unsafe / Recovering / HighVol` state evolution, switch-on, persistence/hysteresis, recovery, recovery probability, and cross-scale 3s/1m/5m risk attributes.

It does **not** own directional payoff optimization, holding period, stop/target, sizing, leverage, account overlays, or payoff routers. Historical payoff/router material remains archive evidence only.

## Data and governance

Read before new work:

- `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`;
- `docs/governance/DATA_USAGE_POLICY_V2.md`;
- `docs/governance/data_usage_declaration.json`;
- `docs/governance/blackbox_query_ledger.json`.

Forward data roles:

- 2020: warm-up only where needed;
- Development: 2021-2023;
- reusable 5m Validation: 2024 through 2026-08-21 only under separately authorized protocols;
- realtime 3s Validation coverage: 2024-2025 only under separately authorized protocols;
- protected BlackBox-V1: strictly after the cutoff under its frozen aggregate-only protocol.

No prior component or V19 Development result automatically authorizes BlackBox access.

## Current breakpoint

The current decisive state is:

`V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_DEVELOPMENT_SUPPORTED_VALIDATION_NOT_AUTHORIZED`

Do **not** run V19 reusable Validation unless separately authorized. Do not alter the frozen E-15s checkpoint, V9 thresholds, V18 switch-on rule, V16/V17 probabilities, or V19 close-confirmed-exit semantics after seeing Development.

Do not synthesize/fabricate 2026 3s coverage, inspect protected post-2026-08-21 data, or query BlackBox.

`v19_validation_queried=false`.
`queried_post_2023_3s_for_v19=false`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`pnl_computed=false`.
`production_authority=false`.
