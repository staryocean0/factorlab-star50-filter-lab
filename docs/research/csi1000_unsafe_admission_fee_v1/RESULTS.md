# CSI1000 Unsafe admission-gate fee study — results

Date: 2026-09-08

Status: post-selection exploratory evidence only. No production or trading promotion.

## Receipt

Canonical successful run:

- branch: `research/csi1000-unsafe-admission-fee-v1-20260908`
- market-run commit: `a15984e09bac4138de410b178f2b195d699bdef0`
- GitHub Actions run: `34187944619`
- artifact id: `10041172278`
- artifact SHA256: `4db47ab26e82e9cbc19bc6e8cbb94134ed9da57b502b1e64c4fd583b6faa8424`

Seven frozen engineering/policy tests passed before the market comparison. The `hard_gate` annual gross, turnover, exposure and booked-return counts reproduce the accepted Phase-2 CSI1000 fixed-physical 3m anchor exactly; maximum absolute difference is 0.

## Frozen comparison

The signal remains exactly the Phase-2 candidate:

- CSI1000 `000852.SH`;
- 3m sampling/decision cadence;
- fixed physical ~60m causal Butterworth filter;
- ~240m sigma/hysteresis memory;
- Unsafe state;
- two-bar delayed execution;
- half-session flat boundaries.

Only the routing policy changed:

- `hard_gate`: flat whenever decision state is not Unsafe;
- `admission_gate`: Unsafe is required to enter/reverse, but Recovering alone does not force an existing same-direction position out.

Current CFFEX fee-table values are used uniformly as a present-day stress model, not historical fee reconstruction:

- open/ordinary transaction 0.23bp;
- same-day close 2.30bp.

The model still omits futures basis, bid/ask spread, slippage, queueing and broker surcharge.

## Pooled 2021-2025

| policy | gross bp | execution legs | exchange-fee bp | net after exchange fee | extra-friction headroom / leg | net with +0.25bp/leg | net with +0.50bp/leg |
|---|---:|---:|---:|---:|---:|---:|---:|
| hard_gate | 170.55 | 98 | 123.97 | **46.58** | 0.475bp | 22.08 | -2.42 |
| admission_gate | 135.25 | 72 | 91.08 | **44.17** | 0.614bp | 26.17 | 8.17 |

Admission reduces execution legs by about 26.5% and exchange-fee burden by 32.89bp. However it also loses about 35.29bp of gross index PnL relative to hard gating. Thus under the exchange-fee floor alone, the saved fee does **not** compensate for the lost gross edge.

With an added abstract 0.25-0.50bp per execution leg, admission becomes better in the pooled total because it trades less. This pooled improvement is not stable enough to promote because the annual paths diverge sharply.

## Annual results

Exchange-fee-floor net bp:

| year | hard_gate | admission_gate |
|---:|---:|---:|
| 2021 | 0.00 | 0.00 |
| 2022 | **+19.85** | -48.74 |
| 2023 | +7.41 | **+23.55** |
| 2024 | +19.51 | **+125.50** |
| 2025 | **-0.19** | -56.14 |
| 2026 consumed replay | **+6.18** | -4.36 |

Admission helps dramatically in 2023-2024 but is badly wrong in 2022 and 2025 and remains negative in the already-opened 2026 replay. This is exactly the kind of state-dependent instability that should not be repaired by adding a new hold-time or release parameter on the same data.

The hard gate is more stable, but its economic margin is itself thin:

- 2025 is already slightly negative after the exchange-fee floor alone;
- 2026 exchange-only net is +6.18bp total and leaves only about 0.281bp extra friction per execution leg;
- adding 0.25bp per execution leg leaves only +0.68bp total in the 2026 replay;
- adding 0.50bp per execution leg makes the 2026 replay negative.

Therefore the Phase-2 CSI1000 candidate is **execution-cost fragile**.

## Scientific conclusion

Phase 3 rejects the simple fix:

> `Unsafe -> keep the 3m signal longer through Recovering to save same-day close fees`.

The mechanism works mechanically—turnover falls—but the extra Recovering exposure is not consistently profitable. Lower turnover alone is not enough.

The durable interpretation is narrower:

1. Unsafe increases the short-horizon movement budget.
2. CSI1000 showed an exploratory 3m execution-cadence / slow-information-clock candidate.
3. Current exchange-fee stress consumes a large fraction of that candidate's edge.
4. A simple admission-only gate does not robustly rescue it.
5. Further rule invention on 2021-2026 should stop.

## Next action

Keep `hard_gate` only as the frozen CSI1000 routing reference for the next independent snapshot; do not claim it is economically tradable yet.

The next decisive input is real IM futures execution data with point-in-time contract selection, bid/ask/trade observations and effective-dated fee metadata. Until that is available, index-level backtests cannot resolve the remaining ~0.0-0.5bp-per-leg execution margin credibly.

Separately, the repository can still study whether the original 5m strategy should use Unsafe as a pure **risk/admission gate** rather than as a frequency-switch trigger. That question does not require inventing another faster strategy and is the next consumed-history mechanism study.
