# Current research entry

## 2026-09-11 current authority

**Current task: STAR50 / CSI1000 bottom-layer K-line risk-state research only.**

The research product of this bucket is a causal risk annotation/state machine. It is not a directional trading strategy.

## Current integrated episode-level authority — V19 reusable Validation supported

V19 integrates the already frozen entry and recovery components into one coherent causal realtime risk-episode state machine at the unchanged `E-15s` checkpoint.

Frozen primary machine:

1. frozen V9 partial `UNSAFE` / `RECOVERING` is emitted immediately at E-15s;
2. if partial state is `NORMAL` while the previous completed 5m state is still `UNSAFE` / `RECOVERING`, retain the previous risk state until the bar actually closes;
3. otherwise emit `NORMAL`.

There is no fitted persistence length. This is deterministic close-confirmed-exit hysteresis, consistent with V17's frozen `provisional_normal = unavailable` gating.

### V19 Development authority

- execution commit: `6fad49e5dc674d9a48b5c1719e060eceabc166d2`;
- run: `34611126345`;
- artifact: `10267923594`;
- artifact SHA256: `3d64999976ca5ad001e7924aa4d6e668e412411e58e1bb10daebb747f4ee5aea`;
- Development years: 2021-2023 only;
- evaluable checkpoints: `68,338`;
- risk precision / recall / FPR: `0.9968622529 / 0.9914698845 / 0.0005108557`;
- exact three-state agreement: `0.9975123650`;
- reference episodes: `867`;
- episode capture: `0.9930795848`;
- fragmentation: `0.0`;
- `development_supported=true`.

### V19 reusable Validation authority

The exact frozen V19 machine has passed reusable Validation on existing 2024-2025 3s coverage with the Development scientific thresholds unchanged.

- branch: `research/highvol-risk-episode-state-machine-v19-validation-20260911`;
- execution commit: `b4527e2f431f5dfb2ef801f262d39f509253820f`;
- run: `34612330970`;
- job: `103305638445`;
- artifact: `10268853374`;
- artifact SHA256: `5989514df544ffc26c0559a185829f5c027df954a311dd9a43f3f0c9912238af`;
- frozen V19 runner blob: `ee2fce299d5ee21abf1ab2c2c5183bac101ae822`;
- Validation years: 2024-2025 only;
- queried 3s years: 2024 and 2025 only;
- evaluable E-15s checkpoints: `45,590`;
- `full_validation_supported=true`.

Pooled Validation:

- reference risk rows: `6,137`;
- machine risk rows: `6,104`;
- TP / FP / FN / TN: `6071 / 33 / 66 / 39420`;
- risk precision: **`0.9945937090`**;
- risk recall: **`0.9892455597`**;
- false-positive rate: **`0.0008364383`**;
- exact three-state agreement: **`0.9963149814`**.

Raw frozen V9 E-15s partial state, diagnostic only, had risk recall `0.9023953072` and exact three-state agreement `0.9848651020`. The close-confirmed rule therefore reproduces out of sample as the main continuity mechanism.

Annual Validation stability:

- 2024: precision `0.994318`, recall `0.991189`, FPR `0.000920`, exact three-state agreement `0.996351`;
- 2025: precision `0.994891`, recall `0.987158`, FPR `0.000754`, exact three-state agreement `0.996279`.

Both symbols passed:

- `000688.SH`: precision `0.994464`, recall `0.988350`, FPR `0.000863`;
- `000852.SH`: precision `0.994725`, recall `0.990154`, FPR `0.000810`.

### V19 episode continuity — Validation

Reference episodes: `542`.
Machine episodes: `570`.

- captured reference episodes: `541 / 542`;
- capture rate: **`0.9981549815`**;
- fragmented reference episodes: `1 / 542`;
- fragmentation rate: **`0.0018450185`**;
- false machine episodes: `28 / 570`;
- false machine-episode rate: **`0.0491228070`**;
- same-checkpoint onset: `477 / 542`;
- same-checkpoint onset rate: **`0.8800738007`**;
- onset-lag median: `0` checkpoints;
- maximum onset lag among captured episodes: `1` checkpoint.

Annual episode capture / same-checkpoint onset:

- 2024: `0.996296 / 0.896296`;
- 2025: `1.000000 / 0.863971`.

### V19 transition continuity — Validation

At the unchanged E-15s checkpoint:

- `NORMAL -> UNSAFE`: `484 / 550`, recall **`0.880000`**;
- `RECOVERING -> UNSAFE`: `236 / 260`, recall **`0.907692`**;
- `UNSAFE -> RECOVERING`: `637 / 662`, recall **`0.962236`**.

Close-confirmed exits remain the decisive hysteresis result:

- exit rows: `520`;
- V19 primary-machine premature `NORMAL`: **`0 / 520`**;
- raw partial state was already `NORMAL` on `514 / 520` exit rows.

Thus provisional E-15s `NORMAL` is not sufficient evidence to terminate an already-confirmed risk episode, while E-15s risk transitions remain informative.

### V16/V17 recovery attachment inside validated V19

- scored recovery-probability rows: `4,944`;
- coverage of machine risk rows: `0.8099606815`;
- every scored curve satisfies `p15 <= p30 <= p60`;
- maximum absolute 60m frozen age-anchor difference: `0.0`.

No V16/V17 probability was refitted or changed.

Primary sealed V19 evidence:

- `research/highvol_risk_episode_state_machine_v19/PROTOCOL.md`;
- `research/highvol_risk_episode_state_machine_v19/FROZEN_DEVELOPMENT_CONTRACT.json`;
- `research/highvol_risk_episode_state_machine_v19/DEVELOPMENT_RESULTS.md`;
- `research/highvol_risk_episode_state_machine_v19/DECISIVE_RECEIPT.json`;
- `research/highvol_risk_episode_state_machine_v19_validation/PROTOCOL.md`;
- `research/highvol_risk_episode_state_machine_v19_validation/FROZEN_VALIDATION_CONTRACT.json`;
- `research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md`;
- `research/highvol_risk_episode_state_machine_v19_validation/DECISIVE_RECEIPT.json`.

## Validated component authorities

### V18 — switch-on

V18 remains the validated entry-side component on 2024-2025 3s coverage:

- run `34607566312`;
- artifact `10265993683`;
- evaluable bars `43,793`;
- true switch-ons `810`;
- E-15s precision / recall / FPR: `0.9511228534 / 0.8888888889 / 0.0008608054`;
- `full_validation_supported=true`.

V18 does not claim to predict the first shock before within-bar evidence exists.

### V17 — realtime recovery

V17 remains the validated E-15s realtime recovery authority on 2024-2025 3s coverage. It transfers the frozen V16 horizon-adaptive object without refit:

- 15m = frozen V16 `state + recent-shock age` using frozen V9 provisional state;
- 30m = frozen V16 `state + recent-shock age` using frozen V9 provisional state;
- 60m = frozen V16 recent-shock-age-only anchor.

V17 reusable Validation: run `34604089926`, artifact `10265472702`, `full_validation_supported=true`.

### V16 — final-5m recovery

V16 remains the final-5m recovery authority through `2026-08-21`:

- 15m = `current_state + time-since-most-recent-shock`;
- 30m = `current_state + time-since-most-recent-shock`;
- 60m = `time-since-most-recent-shock only`.

V16 reusable Validation: run `34602527314`, artifact `10264689647`, `full_validation_supported=true`.

The recovery clock rule remains:

> Every new shock resets the recovery clock. Recovery risk is indexed by time since the most recent shock, not time since the first shock of the episode.

## Current validated causal risk architecture

The integrated realtime risk-state architecture is now reusable-Validation supported on available 2024-2025 3s coverage:

`V18 switch-on -> V19 close-confirmed UNSAFE / RECOVERING continuity -> V17/V16 recovery surface -> close-confirmed Normal`

Important data-boundary distinction:

1. V19/V18/V17 realtime 3s authority ends at `2025-12-31`;
2. V16 final-5m authority extends through `2026-08-21`;
3. V16's 2026 final-5m authority does not create 2026 3s realtime authority.

## Completed evidence chain that must not be casually reopened

- V3-V6: post-shock recovery-state / recent-shock-age mechanism;
- V7: frozen 1m realtime recall gate failed;
- V8-V10: 3s realtime state/probability transfer and E-15s checkpoint;
- V11-V15: horizon-dependent state value; unified 60m state+age surface rejected;
- V16: frozen and validated horizon-adaptive final-5m recovery surface;
- V17: validated E-15s realtime recovery transfer;
- V18: validated E-15s causal UNSAFE switch-on;
- V19: validated E-15s close-confirmed episode-level state machine.

Do not rerun these versions merely to reconfirm them.

## Scope-repaired bucket authority

This repository owns bottom-layer causal K-line risk-state research only, including volatility level/expansion, shock isolation/recurrence, `Unsafe / Recovering / HighVol` state evolution, switch-on, persistence/hysteresis, recovery, recovery probability, and cross-scale 3s/1m/5m risk attributes.

It does **not** own directional payoff optimization, holding period, stop/target, sizing, leverage, account overlays, or payoff routers. Historical payoff/router material remains archive evidence only.

## Data and governance

Forward data roles:

- 2020: warm-up only where needed;
- Development: 2021-2023;
- reusable 5m Validation: 2024 through 2026-08-21 under separately frozen protocols;
- realtime 3s reusable Validation coverage: 2024-2025 only;
- protected BlackBox-V1: strictly after the cutoff under its frozen aggregate-only protocol.

No validated result automatically authorizes BlackBox access.

## Current breakpoint

The current decisive state is:

`V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_REUSABLE_VALIDATION_SUPPORTED_2024_2025`

Do **not** rerun/refit V19, alter E-15s, select a persistence length post hoc, replace the primary machine with raw partial state, alter V18/V17/V16/V9 frozen rules, synthesize 2026 3s coverage, inspect protected post-2026-08-21 data, or query BlackBox merely to reconfirm the result.

No V20 protocol has been started.

`v19_validation_queried=true`.
`queried_3s_years_for_v19=[2024,2025]`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`pnl_computed=false`.
`production_authority=false`.
