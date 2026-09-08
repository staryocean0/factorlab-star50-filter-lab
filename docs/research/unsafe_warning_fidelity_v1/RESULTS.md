# Unsafe warning-fidelity economic stress — results

Date: 2026-09-08

Status: hypothetical fidelity sensitivity only. This is **not** evidence that Unsafe can already be predicted before onset.

## Receipt

Canonical successful run:

- branch: `research/unsafe-warning-fidelity-v1-20260908`
- market-run commit: `65dc90163e476cb319e814bc72a3fd54f4ffdee5`
- GitHub Actions run: `34188901961`
- artifact id: `10041519152`
- artifact SHA256: `55a6b7d61b144ecd0198b801911f6193ea492a0e19c20bbeee542009565c80d3`

All frozen tests passed before market interpretation. The 100% recall / 100% precision scenario reproduces Phase-4 policy totals for both symbols and both periods; maximum numerical anchor difference is below `2e-12`.

True Unsafe support used by the stress:

- STAR50 2021-2025: 112 Unsafe runs / 177 Unsafe 5m bars;
- STAR50 2026 replay: 14 runs / 27 bars;
- CSI1000 2021-2025: 45 runs / 92 bars;
- CSI1000 2026 replay: 10 runs / 15 bars.

False alarms are matched to the true run's year, half-session side, start clock and run length and are placed only on true non-Unsafe/non-Unknown quality-valid bars.

## What 80%/90% means here

The fidelity unit is a contiguous Unsafe **run**, not an individual minute.

For each scenario:

- true Unsafe runs are retained with the target recall;
- false runs are added at a rate targeting the requested run-level precision;
- the full two-bar delayed strategy path is rerun 1,000 times;
- no PnL is used to choose false-alarm locations.

This is a contemporaneous state-mask fidelity stress. It does not model actual warning lead time.

## STAR50

### Hard-off

Perfect-state hard-off was already negative on pooled 2021-2025 versus the original 5m baseline: about **-56.7bp gross** and **-72.7bp at 1bp one-way friction**. Warning imperfection does not rescue that policy in a scientifically meaningful way. Median deltas remain negative across all 80/90 scenarios.

Therefore STAR50 `Unsafe -> hard flat` should remain rejected for the current 5m strategy family.

### Entry-block

Perfect-state entry-block improved pooled 2021-2025 gross by about **+284.6bp** and 1bp-net by **+314.6bp**, but Phase 4 showed that this improvement was highly concentrated in later years, especially 2024, and its affected-day bootstrap interval crossed zero.

Fidelity stress shows that **prediction error is not the main weakness of this candidate**:

| run recall | run precision | median gross delta | 95% interval | median fraction of perfect gross retained |
|---:|---:|---:|---:|---:|
| 80% | 80% | +235.8bp | -1.7 to +430.3 | 82.9% |
| 80% | 90% | +232.8bp | +3.2 to +412.8 | 81.8% |
| 90% | 80% | +266.5bp | +48.4 to +408.8 | 93.6% |
| 90% | 90% | +259.4bp | +80.4 to +390.1 | 91.2% |

The already-opened 2026 replay also has positive median deltas for all four fidelity scenarios, although its small 14-run support leaves wide intervals.

**Interpretation:** if a future warning system can reproduce the relevant STAR50 Unsafe runs at roughly 80%-90% quality, the entry-block economics are not automatically destroyed. But the underlying entry-block policy itself is still not stable enough across 2021-2025 to promote. The bottleneck is policy/regime stability, not classifier fidelity.

## CSI1000

Both Phase-4 perfect-state policies were positive on pooled 2021-2025, with hard-off stronger historically.

### Hard-off

Perfect state:

- gross delta vs baseline: **+157.8bp**;
- 1bp-net delta: **+151.8bp**.

Imperfect warning stress:

| run recall | run precision | median gross delta | 95% interval | positive gross draws | retained perfect gross |
|---:|---:|---:|---:|---:|---:|
| 80% | 80% | +123.3bp | -49.8 to +293.1 | 92.7% | 78.1% |
| 80% | 90% | +121.5bp | -31.4 to +253.6 | 94.1% | 77.0% |
| 90% | 80% | +137.1bp | -34.0 to +275.8 | 94.3% | 86.9% |
| 90% | 90% | **+139.4bp** | **+10.3 to +254.9** | **98.6%** | **88.4%** |

At 1bp one-way friction, the CSI1000 hard-off 90%/90% scenario also retains a positive 95% lower bound in this Monte Carlo stress (about +2.1bp total delta at the lower bound).

This is the strongest fidelity result in the study: **a 90% run-recall / 90% run-precision warning would be accurate enough, conditional on the historical hard-off economics being real.**

However the already-opened 2026 replay is the crucial counterexample: even the **perfect** hard-off mask loses about -28.9bp versus baseline. The 80/90 imperfect versions inherit the same negative median. No classifier can fix a routing policy whose perfect-state action is wrong in that regime.

### Entry-block

Perfect-state pooled 2021-2025 gross delta is +98.0bp. Median improvement remains positive in every 80/90 scenario, retaining roughly 83%-94% of the perfect gross effect. But the 95% intervals still cross zero, including at 90%/90%.

In the 2026 replay, entry-block perfect-state delta is +8.2bp and all four imperfect scenarios have the same positive median, but the sample is only 10 Unsafe runs and the intervals remain wide.

## Main conclusion

The user's 80%-90% reproduction hypothesis is economically plausible **as a fidelity target**. The warning system does not need to be perfect for observed-state routing value to survive.

But the study changes the priority of the research problem:

> **The larger bottleneck is no longer warning fidelity. It is whether the action taken in Unsafe is itself stable across regimes and executable after costs.**

Specifically:

- STAR50: 80%-90% warning fidelity would preserve much of the exploratory entry-block effect, but the entry-block policy itself is historically regime-concentrated and not validated.
- CSI1000: 90%/90% fidelity is sufficient to preserve the historical hard-off effect with a positive Monte Carlo lower bound, but 2026 shows that hard-off can be wrong even with perfect state knowledge.
- CSI1000 3m routing remains additionally constrained by real execution costs; Phase 3 showed very little friction margin after current exchange-fee stress.

Therefore improving the predictor from 80% to 95% is unlikely to solve the current core problem by itself.

## Architecture implication

The current research architecture should be viewed as:

`warning model (future work) -> state estimate -> index-specific action policy -> execution-cost gate`

The second arrow is no longer allowed to be assumed as a universal `Unsafe = stop trading` rule.

Before production-style use, two independent validations are needed:

1. **state prediction:** new post-2026-08-21 data must show that past-only information can actually warn about future Unsafe with acceptable recall/false-alarm burden;
2. **action stability:** the chosen STAR50/CSI1000 action in the predicted state must also survive the same independent period without retuning.

For CSI1000, real IM futures execution data is also required because the remaining theoretical edge is close to the fee/spread/slippage scale.

## Stop rule

Do not search more warning-fidelity levels or invent more state policies on 2021-2026. The 80/90 question is now answered as a sensitivity study.

Until new independent data arrive, useful remaining work should focus on reproducible routing/execution architecture and on specifying the exact future acceptance tests, not on mining additional thresholds from consumed history.
