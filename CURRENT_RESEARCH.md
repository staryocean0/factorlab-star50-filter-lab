# Current research entry

## 2026-09-11 current authority

**Current task: STAR50 / CSI1000 bottom-layer K-line risk-state research only.**

The research product of this bucket is a causal risk annotation/state machine. It is not a directional trading strategy.

## Current mathematical stopping decision — V19 residual audit

The validated V19 object remains the current integrated realtime authority. A post-validation residual audit has now closed the question of whether the remaining V19 errors justify V20.

**Decision: `NO_V20_FROM_V19_RESIDUALS`.**

Sealed diagnostic evidence:

- `research/v19_residual_failure_audit/PROTOCOL.md`;
- `research/v19_residual_failure_audit/RESULTS.md`;
- `research/v19_residual_failure_audit/DECISIVE_RECEIPT.json`.

Successful audit authority:

- execution commit: `a066a64ee22cf6e23911f5bccc1a90eafe2de9e4`;
- run: `34614008432`;
- job: `103311278481`;
- artifact: `10270156874`;
- artifact SHA256: `b49c61d8b2345e0441c69fa7d94d25bf9425d572d13953e40e83aede72f4d0fb`.

The first audit run `34613545773` failed only because a temporary diagnostic boolean column was initialized with float dtype. It produced no scientific output. The successful rerun used a dtype-only implementation wrapper; the preregistered taxonomy, thresholds, diagnostic checkpoints and decision rule were unchanged.

### What the residuals actually are

On the already-consumed 2024-2025 Validation pool:

- **66 risk false negatives:** all `NORMAL -> UNSAFE` final shocks; all were below the frozen 3σ shock threshold at E-15 and above it by close. Of these, `48` become risk by E-6, `16` by E-3, and only `2` form after E-3/by close.
- **33 risk false positives:** all transient E-15 partial shocks from `NORMAL` that finish `NORMAL`; `27` resolve by E-6 and `6` by E-3. None persists through E-3 and only resolves at close.
- These `66 + 33 = 99` rows exhaust the binary risk errors. The false negatives and false positives are mirror-image threshold crossings around the same unchanged 3σ boundary.
- **69 `UNSAFE`/`RECOVERING` state mismatches** occur while both reference and machine already agree that the market is risky. They are only `0.00151349` of all 45,590 checkpoints; `46/69` converge by E-6 and `62/69` by E-3.

Episode residuals are equally bounded:

- uncaptured reference episodes: `1`, caused by a risk FN;
- fragmented reference episodes: `1`, caused by an FN at a `SWITCH_ON` transition;
- false machine episodes: `28`, all exactly one checkpoint/bar long;
- `23/28` false episodes resolve by E-6 and `5/28` by E-3.

Development 2021-2023 reproduces the same mechanism: 82 late-forming FN shocks, 30 transient E-15 FP shocks, and one-checkpoint false episodes. Therefore this is not a new Validation-only pathology.

### Why V20 is not mathematically justified

Repairing these residuals would require at least one of:

1. moving the already-validated 3σ shock threshold, which trades late false negatives against transient false positives;
2. moving the product checkpoint from E-15 to E-6/E-3 after those later checkpoints have already been inspected;
3. fitting new features, persistence rules or exceptions on already-consumed Validation data.

None constitutes a distinct causal state mechanism. In addition, there is no authorized fresh realtime 3s holdout after 2025 for clean validation of a newly fitted V20.

Therefore **do not open V20 to optimize V19 residuals**. A future version requires either genuinely new independent realtime data or a qualitatively new causal research question.

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

The exact frozen V19 machine passed reusable Validation on existing 2024-2025 3s coverage with the Development scientific thresholds unchanged.

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

Episode Validation:

- reference episodes: `542`;
- machine episodes: `570`;
- capture: `541 / 542 = 0.9981549815`;
- fragmentation: `1 / 542 = 0.0018450185`;
- false machine-episode rate: `0.0491228070`;
- same-checkpoint onset rate: `0.8800738007`;
- onset-lag median: `0` checkpoints;
- maximum onset lag among captured episodes: `1` checkpoint.

Transition continuity at E-15s:

- `NORMAL -> UNSAFE`: recall `0.880000`;
- `RECOVERING -> UNSAFE`: recall `0.907692`;
- `UNSAFE -> RECOVERING`: recall `0.962236`;
- close-confirmed exit rows: `520`;
- V19 premature `NORMAL`: `0 / 520`;
- raw partial state was already `NORMAL` on `514 / 520` exit rows.

Frozen V16/V17 recovery attachment remains intact: 4,944 probability rows were scored, all satisfy `p15 <= p30 <= p60`, and the 60m age-only anchor matches exactly.

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

V18 remains the validated entry-side component on 2024-2025 3s coverage: E-15s precision / recall / FPR = `0.9511228534 / 0.8888888889 / 0.0008608054`; `full_validation_supported=true`.

V18 does not claim to predict the first shock before within-bar evidence exists.

### V17 — realtime recovery

V17 remains the validated E-15s realtime recovery authority on 2024-2025 3s coverage. It transfers frozen V16 without refit: 15m/30m use state + recent-shock age; 60m uses the recent-shock-age-only anchor.

### V16 — final-5m recovery

V16 remains the final-5m recovery authority through `2026-08-21`: 15m/30m use current state + recent-shock age; 60m uses recent-shock age only.

The recovery clock rule remains: every new shock resets the recovery clock; recovery risk is indexed by time since the most recent shock.

## Current validated causal risk architecture

`V18 switch-on -> V19 close-confirmed UNSAFE / RECOVERING continuity -> V17/V16 recovery surface -> close-confirmed Normal`

Realtime V19/V18/V17 3s authority ends at `2025-12-31`. V16 final-5m authority extends through `2026-08-21`; that does not create 2026 realtime authority.

## Completed evidence chain that must not be casually reopened

- V3-V6: post-shock recovery-state / recent-shock-age mechanism;
- V7: frozen 1m realtime recall gate failed;
- V8-V10: 3s realtime state/probability transfer and E-15s checkpoint;
- V11-V15: horizon-dependent state value; unified 60m state+age surface rejected;
- V16: frozen and validated horizon-adaptive final-5m recovery surface;
- V17: validated E-15s realtime recovery transfer;
- V18: validated E-15s causal UNSAFE switch-on;
- V19: validated E-15s close-confirmed episode-level state machine;
- V19 residual audit: remaining errors diagnosed as final-15s threshold timing, with `NO_V20_FROM_V19_RESIDUALS`.

Do not rerun these versions merely to reconfirm them.

## Scope and governance

This repository owns bottom-layer causal K-line risk-state research only. It does not own directional payoff optimization, holding period, stop/target, sizing, leverage, account overlays, or payoff routers.

Forward data roles:

- 2020: warm-up only where needed;
- Development: 2021-2023;
- reusable 5m Validation: 2024 through 2026-08-21 under frozen protocols;
- realtime 3s reusable Validation: 2024-2025 only;
- protected BlackBox-V1: strictly under its separate frozen aggregate-only protocol.

No validated result automatically authorizes BlackBox access.

## Current breakpoint

Current decisive state:

`V19_VALIDATED_RESIDUAL_PATH_CLOSED_NO_V20`

Do not rerun/refit V19, alter E-15s, move the 3σ threshold, select E-6/E-3 post hoc, tune persistence/features against consumed Validation, synthesize 2026 3s, or query BlackBox merely to improve residual metrics.

`v19_validation_queried=true`.
`v19_residual_audit_completed=true`.
`v20_started=false`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`pnl_computed=false`.
`production_authority=false`.
