# Unsafe warning fidelity V1 — reviewed results

Date: 2026-09-08

Status: **completed exploratory stress test; no strategy promotion**.

This note seals the Phase-5 warning-fidelity stress and a post-result concentration falsification of the already-sealed Phase-4 routing effects. It does **not** claim a first-shock predictor, a live trading rule, or fresh out-of-sample evidence.

## Frozen question

If a future warning layer could reproduce the causal `Unsafe` state only imperfectly, would the Phase-4 5-minute risk-routing conclusions survive?

The stress is deliberately **run-level**, not independent minute flips:

- recall/precision targets: `(0.8,0.8)`, `(0.8,0.9)`, `(0.9,0.8)`, `(0.9,0.9)`;
- 1,000 draws per imperfect scenario;
- perfect `(1.0,1.0)` anchor;
- false Unsafe runs matched on year, half-session, start clock and run length and placed only in real non-Unsafe/non-Unknown space;
- seed `20260908`;
- 1 bp one-way abstract cost stress retained from Phase 4;
- 2021–2025 remains consumed history;
- 2026 remains already-opened consistency replay only.

This is a **hypothetical contemporaneous state-fidelity stress**, not a predictor test. It says nothing about whether the state can be forecast before onset.

## Execution receipt

- GitHub Actions run: `34188901961`
- artifact: `unsafe-warning-fidelity-34188901961`
- artifact SHA-256: `55a6b7d61b144ecd0198b801911f6193ea492a0e19c20bbeee542009565c80d3`
- frozen execution commit: `65dc90163e476cb319e814bc72a3fd54f4ffdee5`
- all frozen tests passed;
- perfect-state Phase-4 anchor passed.

## Main Phase-5 result

### 1. `unsafe_entry_block` is much more robust than `unsafe_hard_off`

`unsafe_entry_block` means Unsafe blocks **new or reversing risk** but does not force an immediate exit from an already-held same-direction position. `unsafe_hard_off` forces flat when Unsafe is signaled.

#### STAR50 — 2021–2025

Perfect state:

- entry block: `+284.57 bp` gross delta; `+314.57 bp` delta after 1 bp one-way cost;
- hard off: `-56.74 bp` gross delta; `-72.74 bp` net-cost delta.

At 90% run recall / 90% run precision:

- entry block gross delta median `+259.43 bp`, 2.5–97.5% range `[+80.36, +390.13]`;
- entry block net-1bp delta median `+289.44 bp`, range `[+108.31, +421.11]`;
- hard off gross delta median `-59.38 bp`, range `[-296.98, +165.34]`;
- hard off net-1bp delta median `-75.04 bp`, range `[-319.87, +152.64]`.

At 80%/80%, entry block still has positive median gross/net deltas (`+235.78 / +266.30 bp`), but the gross 2.5% tail crosses zero (`-1.73 bp`).

#### STAR50 — 2026 already-opened replay

Perfect state:

- entry block: `+56.54 bp` gross delta, `+64.54 bp` net-1bp delta;
- hard off: `+85.83 bp` gross delta, `+89.83 bp` net-1bp delta.

With imperfect warning, both policies retain positive medians, but all tested entry-block 2.5% gross tails cross below zero. Thus 2026 does not provide a distribution-level confirmation of a robust imperfect-warning rule.

#### CSI1000 — 2021–2025

Perfect state:

- entry block: `+97.98 bp` gross delta; `+109.98 bp` net-1bp delta;
- hard off: `+157.78 bp` gross delta; `+151.78 bp` net-1bp delta.

At 90%/90%:

- entry block gross delta median `+92.40 bp`, range `[-22.98, +176.43]`;
- entry block net-1bp delta median `+105.41 bp`, range `[-14.26, +190.32]`;
- hard off gross delta median `+139.44 bp`, range `[+10.32, +254.89]`;
- hard off net-1bp delta median `+132.73 bp`, range `[+2.11, +250.36]`.

So in consumed 2021–2025 history the CSI1000 hard-off policy tolerates a 90/90 run-fidelity stress better than STAR50.

#### CSI1000 — 2026 already-opened replay

Perfect state:

- entry block: `+8.19 bp` gross delta; `+10.19 bp` net-1bp delta;
- hard off: `-28.92 bp` gross and net-cost delta.

At every tested imperfect-fidelity scenario, hard-off has a negative median in 2026. Entry-block medians remain mildly positive (`~+8.19 bp` gross) but lower tails cross zero.

Therefore the historical CSI1000 hard-off advantage does **not** carry into the already-opened 2026 replay.

## Concentration falsification

The Phase-4 improvements are sparse and materially concentrated.

### STAR50 `unsafe_entry_block`

2021–2025 affected half-sessions: `74`.

- positive delta: `16` sessions;
- negative delta: `12`;
- exactly unchanged: `46`;
- gross delta sum: `+284.57 bp`;
- positive contributions: `+619.62 bp`;
- negative contributions: `-335.05 bp`;
- top 5 affected half-sessions account for about `52.1%` of total absolute gross change.

Year deltas are highly uneven:

- 2021 `-25.51 bp`
- 2022 `-26.11 bp`
- 2023 `-62.30 bp`
- 2024 `+332.76 bp`
- 2025 `+65.74 bp`
- 2026 replay `+56.54 bp`

**Leave-2024-out gross delta becomes `-48.19 bp`.** Therefore the positive 2021–2025 pooled result is not year-robust.

### CSI1000 `unsafe_entry_block`

2021–2025 affected half-sessions: `29`.

- positive delta: `9`;
- negative delta: `7`;
- unchanged: `13`;
- gross delta sum: `+97.98 bp`;
- positive contributions: `+280.61 bp`;
- negative contributions: `-182.63 bp`;
- top 5 affected half-sessions account for about `54.8%` of total absolute gross change.

Year deltas:

- 2021 `0.00 bp`
- 2022 `+15.88 bp`
- 2023 `+21.17 bp`
- 2024 `-33.41 bp`
- 2025 `+94.33 bp`
- 2026 replay `+8.19 bp`

**Leave-2025-out gross delta is only `+3.64 bp`.** The pooled advantage is therefore also strongly year-concentrated.

### CSI1000 `unsafe_hard_off`

The 2021–2025 gross delta is positive (`+157.78 bp`) and remains positive under every single-year deletion, but the 2026 replay reverses to `-28.92 bp`. This is a cross-period falsification against promoting hard-off as a universal rule.

## Scientific interpretation

1. **Do not promote `Unsafe => flat`.** It is unstable across index and period, even when the state is known perfectly.
2. **If a future high-quality warning layer exists, `Unsafe => block new/reversing risk` is the safer research candidate.** It degrades more gracefully under run-level recall/precision errors and avoids mechanically crystallizing positions when state changes.
3. **But current evidence is not sufficient for promotion.** The apparent gains are sparse and strongly year-concentrated, especially STAR50-2024 and CSI1000-2025.
4. **Phase 5 does not rescue the first-shock prediction problem.** It assumes a hypothetical contemporaneous warning fidelity. Earlier seconds-path work did not establish a stable pre-onset first-shock predictor.
5. **No further parameter or policy search should be justified from these same consumed years.** The next scientifically clean promotion step requires genuinely future data and a frozen warning model/routing policy, not another retrospective rule variant.

## Decision

**No live/production promotion.**

Retain `Unsafe` as a causal research/risk annotation. If future prospective data support a warning model with approximately 90% run-level recall/precision, pre-register `unsafe_entry_block` as the first routing policy to test; treat `unsafe_hard_off` as rejected for universal use unless new prospective evidence specifically rehabilitates it.
