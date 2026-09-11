# V19 causal realtime risk-episode state machine — Development result

## Decision

**PASS — `development_supported=true`.**

The preregistered E-15s close-confirmed risk-episode machine passed every Development gate on 2021–2023 without changing the frozen V9/V16/V17/V18 components.

Decisive action:

`FREEZE_V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_AND_STOP_BEFORE_VALIDATION`

Validation is scientifically eligible but is **not authorized** by this result.

## Execution authority

- branch: `research/highvol-risk-episode-state-machine-v19-20260911`
- execution commit: `6fad49e5dc674d9a48b5c1719e060eceabc166d2`
- run: `34611126345`
- job: `103301597623`
- artifact: `10267923594`
- artifact SHA256: `3d64999976ca5ad001e7924aa4d6e668e412411e58e1bb10daebb747f4ee5aea`

Frozen identities:

- V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`
- V18 runner blob: `62c207badff1c3e37cbb1a8e17ef89feeea611d8`
- V17 runner blob: `397d80037806ba11cadf7f77717d36d55fbafc91`
- V16 surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`

## Frozen primary machine

At exactly E-15s:

1. frozen V9 partial `UNSAFE` / `RECOVERING` is emitted immediately;
2. if frozen V9 partial state is `NORMAL` while the previous completed 5m state is still `UNSAFE` / `RECOVERING`, retain that previous risk state until bar close;
3. otherwise emit `NORMAL`.

No persistence length or new threshold was fitted. The raw V9 partial sequence is diagnostic only.

## Pooled checkpoint result

Across **68,338** causal-evaluable checkpoints:

- checkpoint coverage: `1.000000`
- reference E-15s risk rows: `9,613`
- machine risk rows: `9,561`
- TP / FP / FN / TN: `9531 / 30 / 82 / 58695`
- risk precision: **`0.9968622529`**
- risk recall: **`0.9914698845`**
- false-positive rate: **`0.0005108557`**
- exact three-state agreement: **`0.9975123650`**

The raw partial-state comparator, with no close-confirmed exit latch, had:

- risk precision: `0.9965548921`
- risk recall: **`0.9027358785`**
- exact three-state agreement: `0.9851034563`

Thus the preregistered close-confirmed exit semantics mainly remove premature `NORMAL` declarations while preserving the already-low false-positive rate.

## Annual stability

| Year | checkpoints | risk precision | risk recall | FPR | exact 3-state agreement |
|---|---:|---:|---:|---:|---:|
| 2021 | 22,842 | 1.000000 | 0.998767 | 0.000000 | 0.999825 |
| 2022 | 22,748 | 0.996780 | 0.990690 | 0.000570 | 0.997538 |
| 2023 | 22,748 | 0.993457 | 0.984306 | 0.000959 | 0.995164 |

Every annual gate passed.

## Symbol stability

| Symbol | checkpoints | risk precision | risk recall | FPR | exact 3-state agreement |
|---|---:|---:|---:|---:|---:|
| `000688.SH` | 34,169 | 0.996455 | 0.990409 | 0.000619 | 0.996956 |
| `000852.SH` | 34,169 | 0.997323 | 0.992673 | 0.000405 | 0.998068 |

## Episode continuity

There are **867** reference E-15s risk episodes and **890** machine episodes.

- reference episodes captured: `861 / 867`
- reference-episode capture rate: **`0.9930795848`**
- fragmented reference episodes: **`0`**
- fragmentation rate: **`0.0`**
- false machine episodes: `29 / 890`
- false machine-episode rate: **`0.0325842697`**
- same-checkpoint onset: `785 / 867`
- same-checkpoint onset rate: **`0.9054209919`**
- onset-lag median: `0` checkpoints
- maximum onset lag among captured episodes: `1` checkpoint

Annual episode results:

| Year | reference episodes | capture | false machine episode rate | fragmentation | same-checkpoint onset |
|---|---:|---:|---:|---:|---:|
| 2021 | 296 | 0.986486 | 0.000000 | 0.000000 | 0.986486 |
| 2022 | 299 | 0.996656 | 0.035599 | 0.000000 | 0.892977 |
| 2023 | 272 | 0.996324 | 0.062284 | 0.000000 | 0.830882 |

All preregistered episode gates passed.

## Transition continuity

Frozen same-checkpoint transition results:

- `NORMAL -> UNSAFE` switch-on: `794 / 876`, recall **`0.9063926941`**
- `RECOVERING -> UNSAFE` re-escalation: `463 / 485`, recall **`0.9546391753`**
- `UNSAFE -> RECOVERING`: `1083 / 1097`, recall **`0.9872379216`**

Close-confirmed exits:

- exit rows: `853`
- primary machine premature `NORMAL`: **`0 / 853`**
- raw partial state was already `NORMAL` on `844 / 853` exit rows (`0.989449`)

This is the central V19 mechanism result: the raw E-15s measurement is excellent for entry/re-escalation/recovery transitions, but by itself almost always declares `NORMAL` during the final 15 seconds of an exit bar. The frozen close-confirmed rule removes that premature-safe flicker without a fitted persistence window.

## Frozen V16/V17 recovery attachment

- scored recovery-probability rows: `7,716`
- coverage of machine risk rows: `0.8070285535`
- every scored curve obeys `p15 <= p30 <= p60`
- maximum absolute 60m age-anchor difference: **`0.0`**

Unscored reasons are intentional frozen gating:

- fresh partial shock: `992`
- provisional partial `NORMAL`: `59,630`
- scored: `7,716`

V19 does not alter or refit the V16/V17 probability surface.

## Governance

- Development 3s queried: 2021–2023 only
- 2020 5m used only as reference/warm-up
- Validation queried: `false`
- post-2023 3s queried: `false`
- 2026 3s queried: `false`
- BlackBox queried: `false`
- probability fit performed: `false`
- threshold search performed: `false`
- lead-time search performed: `false`
- persistence-length search performed: `false`
- PnL computed: `false`
- trading rule created: `false`
- `production_authority=false`

## Interpretation

V19 supports a coherent causal episode-level state machine at E-15s:

`V18 early switch-on -> UNSAFE / RECOVERING realtime continuity -> V17/V16 recovery surface -> close-confirmed exit`

The supported Development object is a **risk annotation/state machine**, not a trading policy. It must be frozen before any reusable Validation is considered.
