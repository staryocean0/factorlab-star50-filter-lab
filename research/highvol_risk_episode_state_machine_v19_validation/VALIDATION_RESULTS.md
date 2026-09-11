# V19 causal realtime risk-episode state machine — reusable Validation result

## Decision

**PASS — `full_validation_supported=true`.**

The exact frozen V19 E-15s close-confirmed risk-episode state machine passed every preregistered reusable Validation gate on 2024–2025 existing 3s coverage without refitting or changing any V19/V18/V17/V16/V9 rule.

Decisive state:

`V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_REUSABLE_VALIDATION_SUPPORTED_2024_2025`

## Execution authority

- branch: `research/highvol-risk-episode-state-machine-v19-validation-20260911`
- execution commit: `b4527e2f431f5dfb2ef801f262d39f509253820f`
- run: `34612330970`
- job: `103305638445`
- artifact: `10268853374`
- artifact SHA256: `5989514df544ffc26c0559a185829f5c027df954a311dd9a43f3f0c9912238af`
- frozen V19 runner blob: `ee2fce299d5ee21abf1ab2c2c5183bac101ae822`
- frozen V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`
- frozen V18 runner blob: `62c207badff1c3e37cbb1a8e17ef89feeea611d8`
- frozen V17 runner blob: `397d80037806ba11cadf7f77717d36d55fbafc91`
- frozen V16 surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`

## Frozen machine

At exactly E-15s:

1. partial `UNSAFE` / `RECOVERING` is emitted immediately;
2. provisional partial `NORMAL` while the previous completed 5m state is still `UNSAFE` / `RECOVERING` is latched to that prior risk state until bar close;
3. otherwise emit `NORMAL`.

No threshold, persistence length, lead time, feature, probability, projection, subgroup, or target was selected in Validation.

## Validation boundary

- scored years: 2024 and 2025 only;
- queried 3s years: 2024 and 2025 only;
- 5m 2020–2025 was present only to preserve the frozen causal reference history;
- no 2026 3s file was checked out or queried;
- BlackBox was not queried;
- `production_authority=false`.

## Pooled checkpoint result

Across **45,590** causal-evaluable E-15s checkpoints:

- checkpoint coverage: `1.000000`;
- reference risk rows: `6,137`;
- machine risk rows: `6,104`;
- TP / FP / FN / TN: `6071 / 33 / 66 / 39420`;
- risk precision: **`0.9945937090`**;
- risk recall: **`0.9892455597`**;
- false-positive rate: **`0.0008364383`**;
- exact three-state agreement: **`0.9963149814`**.

The raw E-15s partial-state comparator, without close-confirmed exit semantics, had:

- risk precision: `0.9940764674`;
- risk recall: **`0.9023953072`**;
- exact three-state agreement: `0.9848651020`.

Thus the V19 hysteresis mechanism again removes premature-safe flicker while preserving very high precision.

## Annual stability

| Year | checkpoints | risk precision | risk recall | FPR | exact 3-state agreement |
|---|---:|---:|---:|---:|---:|
| 2024 | 22,748 | 0.994318 | 0.991189 | 0.000920 | 0.996351 |
| 2025 | 22,842 | 0.994891 | 0.987158 | 0.000754 | 0.996279 |

Both years passed every frozen annual gate.

## Symbol stability

| Symbol | checkpoints | risk precision | risk recall | FPR | exact 3-state agreement |
|---|---:|---:|---:|---:|---:|
| `000688.SH` | 22,795 | 0.994464 | 0.988350 | 0.000863 | 0.996008 |
| `000852.SH` | 22,795 | 0.994725 | 0.990154 | 0.000810 | 0.996622 |

## Episode continuity

There are **542** reference E-15s risk episodes and **570** machine episodes.

- captured reference episodes: `541 / 542`;
- capture rate: **`0.9981549815`**;
- fragmented reference episodes: `1 / 542`;
- fragmentation rate: **`0.0018450185`**;
- false machine episodes: `28 / 570`;
- false machine-episode rate: **`0.0491228070`**;
- same-checkpoint onset: `477 / 542`;
- same-checkpoint onset rate: **`0.8800738007`**;
- onset lag median: `0` checkpoints;
- maximum onset lag among captured episodes: `1` checkpoint.

Annual episode stability:

| Year | reference episodes | capture | false machine episode rate | fragmentation | same-checkpoint onset |
|---|---:|---:|---:|---:|---:|
| 2024 | 270 | 0.996296 | 0.056140 | 0.000000 | 0.896296 |
| 2025 | 272 | 1.000000 | 0.042105 | 0.003676 | 0.863971 |

## Transition continuity

- `NORMAL -> UNSAFE`: `484 / 550`, recall **`0.880000`**;
- `RECOVERING -> UNSAFE`: `236 / 260`, recall **`0.907692`**;
- `UNSAFE -> RECOVERING`: `637 / 662`, recall **`0.962236`**.

Close-confirmed exits:

- exit rows: `520`;
- primary V19 machine premature `NORMAL`: **`0 / 520`**;
- raw partial state already `NORMAL`: `514 / 520` (`0.988462`).

The central V19 mechanism therefore reproduces out of sample: provisional E-15s `NORMAL` is not sufficient evidence to terminate an already-confirmed risk episode, while E-15s risk transitions remain highly informative.

## Frozen recovery attachment integrity

- scored recovery-probability rows: `4,944`;
- coverage of machine risk rows: `0.8099606815`;
- every scored curve obeys `p15 <= p30 <= p60`;
- maximum absolute 60m age-anchor difference: **`0.0`**.

Unscored rows remain governed by the frozen V17/V16 gating and are not repaired post hoc.

## Governance conclusion

Every preregistered acceptance gate passed.

- threshold search: `false`;
- lead-time search: `false`;
- persistence-length search: `false`;
- probability fit: `false`;
- projection change: `false`;
- post-hoc subgroup selection: `false`;
- queried 2026 3s: `false`;
- BlackBox queried: `false`;
- PnL computed: `false`;
- trading rule created: `false`;
- production authority: `false`.

The validated V19 object is a causal risk-state annotation/state machine, not a directional strategy.
