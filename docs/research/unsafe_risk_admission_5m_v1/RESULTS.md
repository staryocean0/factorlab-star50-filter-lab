# Original-5m Unsafe risk/admission routing — results

Date: 2026-09-08

Status: consumed-history mechanism study. No production/trading promotion.

## Receipt

Canonical successful run:

- branch: `research/unsafe-risk-admission-5m-v1-20260908`
- market-run commit: `e37a08b699734b1314f4dd0e090990134f779946`
- GitHub Actions run: `34188439709`
- artifact id: `10041343483`
- artifact SHA256: `dbe5afc4c99caa152f094ee2bb9a3e633d66e02d2c8d9e5d6de30f912c861cdf`

The frozen Phase-4 tests passed before market interpretation. The 5m `baseline_ungated` annual gross/turnover/exposure/booked-return fingerprints reproduce the accepted Phase-2 anchor for both indices; maximum numerical difference is about `4.55e-12`.

## Policies

- `baseline_ungated`: original 5m signal ignores state;
- `unsafe_hard_off`: only NoEpisode/Recovering may hold the signal; Unsafe/Unknown target flat;
- `unsafe_entry_block`: Unsafe blocks entry/reversal but does not by itself close an existing same-direction position; Unknown still targets flat.

All use the same 5m / ~60m causal Butterworth / ~240m sigma / k=1 structure, two-bar execution latency, and half-session-flat boundary.

## Pooled 2021-2025

### STAR50

| policy | gross bp | turnover | BE one-way cost | net at 1bp |
|---|---:|---:|---:|---:|
| baseline | 10,740.56 | 11,050 | 0.972bp | -309.44 |
| hard off | 10,683.82 | 11,066 | 0.965bp | -382.18 |
| entry block | **11,025.13** | **11,020** | **1.000bp** | **+5.13** |

The pooled STAR50 entry-block point estimate looks better, but it is not stable enough to promote.

Annual gross delta vs baseline:

| year | hard off | entry block |
|---:|---:|---:|
| 2021 | -22.08 | -25.51 |
| 2022 | +24.25 | -26.11 |
| 2023 | -102.15 | -62.30 |
| 2024 | +169.22 | +332.76 |
| 2025 | -125.98 | +65.74 |
| 2026 consumed replay | +85.83 | +56.54 |

The entry-block pooled improvement is highly regime-concentrated, especially in 2024. On the 74 affected 2021-2025 half-sessions, its paired mean gross delta is +3.85bp/session-equivalent day contribution, but the trading-day bootstrap 95% interval includes zero (approximately -2.52 to +11.06bp for the mean daily affected delta). Hard-off is near zero on average and also crosses zero widely.

Tail behavior is directionally better: on affected STAR50 sessions, baseline worst gross is -363.07bp; both overlays reduce the observed worst to about -231.19bp. The 5% session quantile improves from -107.93bp to roughly -95 to -98bp. This is useful risk evidence, but not enough to convert either overlay into a stable trade rule.

**STAR50 conclusion:** Unsafe is informative for risk, but neither `hard_off` nor `entry_block` is sufficiently stable as a direct deterministic control of the original 5m strategy. Do not mechanically stop or switch frequency solely from current evidence.

### CSI1000

| policy | gross bp | turnover | BE one-way cost | net at 1bp |
|---|---:|---:|---:|---:|
| baseline | 11,653.50 | 10,750 | 1.084bp | +903.50 |
| hard off | **11,811.29** | 10,756 | **1.098bp** | **+1,055.29** |
| entry block | 11,751.48 | **10,738** | 1.094bp | +1,013.48 |

On the 29 affected 2021-2025 half-sessions, baseline gross is -124.81bp. Hard-off changes that to +32.97bp; entry-block to -26.83bp. The observed worst affected-session gross improves from -251.28bp to about -226.71bp, and the 5% quantile improves from -100.48bp to about -84.75/-80.76bp.

Annual gross delta vs baseline:

| year | hard off | entry block |
|---:|---:|---:|
| 2021 | 0.00 | 0.00 |
| 2022 | +12.55 | +15.88 |
| 2023 | +19.93 | +21.17 |
| 2024 | +35.35 | -33.41 |
| 2025 | +89.96 | +94.33 |
| 2026 consumed replay | **-28.92** | +8.19 |

Thus hard-off improves every active consumed historical year 2022-2025 but fails in the already-opened 2026 replay. Entry-block is positive in 2022/2023/2025/2026 but fails in 2024. The affected-day bootstrap intervals remain wide and cross zero because the number of affected days is small.

**CSI1000 conclusion:** the evidence is stronger that Unsafe has economic value as a risk-admission variable for the original 5m strategy, but the exact deterministic action is not identified. Hard-off and entry-block each have a clear counterexample. Preserve both as diagnostics; do not choose one on this consumed sample.

## Architecture implication

The research now distinguishes three layers:

1. **State measurement:** `first shock -> {Unsafe <-> Recovering}` remains the durable state abstraction.
2. **Frequency routing:** high volatility expands short-horizon movement budget, but whole-strategy physical-clock contraction is rejected; CSI1000 has only a cost-fragile exploratory 3m execution-cadence candidate.
3. **Risk admission:** STAR50 does not yet support a deterministic 5m state gate; CSI1000 does show repeated economic relevance of Unsafe, but exact hard-off vs entry-block policy remains unresolved.

This means the state machine should not currently be encoded as `Unsafe = no trading` across both indices.

A more defensible current design is:

- STAR50: expose Unsafe as a risk score / risk-budget input, not a hard strategy switch;
- CSI1000: Unsafe may justify reducing or withholding new 5m strategy risk, but the exact action needs independent validation; the 3m route also needs real execution data.

## Next step

Do not invent another policy on 2021-2026.

The next mechanism study is an **imperfect-state fidelity stress test**: assume a future warning system reproduces observed Unsafe with 80%/90% episode-level recall and explicitly controlled false alarms, then quantify how much of the perfect-state economic effect survives. This is only a sensitivity/upper-bound study, not evidence that such a warning system already exists.

The next independent market validation after 2026-08-21 remains reserved and must not be used to tune the state or routing rules.
