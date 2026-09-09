# Broad reversal program review after two promotions — 2026-09-08

Program identity: `broad_reversal_mean_reversion_discovery_program_v1`

Trigger: the frozen Stage-1 budget allowed at most two lane promotions without a new program review. The program now has exactly two progressed mechanisms:

1. R1 cross-scale pullback / parent-integrity mechanism;
2. R5-C same-scale event-density state mechanism.

This review does **not** open the 2023–2025 reserve and does not authorize PnL optimization.

## Evidence compared

### R1 — cross-scale parent integrity

Fine S1-inside-S2:

- stability events: 763;
- severity-only Brier `0.18090`;
- parent+severity Brier `0.17229`;
- approximate absolute improvement `0.00861`;
- annual improvement: 2020, 2021, 2022.

Coarse S2-inside-S3:

- stability events: 291;
- severity-only Brier `0.16285`;
- parent+severity Brier `0.15601`;
- approximate absolute improvement `0.00684`;
- annual improvement: 2020 and 2022; slightly negative in 2021.

### R5-C — event-density state

S1:

- stability events: 2,329;
- severity-only Brier `0.2501610`;
- severity+event-density-z Brier `0.2494158`;
- absolute improvement `0.0007452`;
- annual improvement: 2020, 2021, 2022.

S2:

- stability events: 831;
- severity-only Brier `0.2489933`;
- augmented Brier `0.2489006`;
- absolute improvement `0.00009275`;
- annual improvement: 2020 and 2022; small deterioration in 2021.

## Required comparison dimensions

### 1. Effect strength

**Winner: R1 by a wide margin.**

R1's held-forward Brier improvement is roughly an order of magnitude larger than R5-C's at both comparable fine/coarse views. R5-C's effect is real enough for progression but small enough that it could disappear under a stricter dedicated baseline.

### 2. Stability

**Roughly tied on sign stability, R1 stronger on magnitude.**

Both mechanisms improve in all three fine-scale stability years and 2/3 coarse-scale years. R1 maintains much larger absolute gains.

### 3. Sample supply

**Winner: R5-C.**

R5-C has substantially more resolved stability events. Its small effect therefore is not a tiny-sample artifact, but the larger sample does not compensate for the much weaker incremental magnitude.

### 4. Data quality and cost

**Tie.**

Both use the same admitted CSI1000 1m source, the same frozen chronological roles, and causal directional-change machinery. Neither needs fundamentals, news or cross-asset data for its next mechanism step.

### 5. Definition complexity

**R5-C is simpler.**

R5-C adds one scalar state variable to a severity baseline. R1 uses several parent-structure measurements and therefore has more representation risk.

However, R1's higher complexity is still low-capacity and its effect is much larger, so complexity alone does not reverse the ranking.

### 6. Independence from legacy R4

**Both pass.**

R1 is a cross-scale structural mechanism. R5-C is a statistical event-state mechanism. Neither is a repackaging of overnight-gap / relative-gap V21 evidence.

### 7. Economic interpretability

**Winner: R1.**

R1 has a direct structural interpretation: for equally severe counter-moves, an intact parent state changes recovery-before-failure probability.

R5-C is interpretable as market event activity / state intensity, but Stage-1 has not yet established whether high or low density is the important side or why it changes reversal odds.

## Program priority decision

### Priority A — R1 specialist

R1 receives the **first dedicated deeper-mechanism budget** outside the broad repo.

This does not authorize trading optimization. The dedicated identity must first compress/interpret parent integrity, freeze its small candidate family, then test the untouched 2023–2025 mechanism holdout.

### Priority B — R5-C specialist

R5-C remains **progressed but secondary**.

It deserves one bounded dedicated mechanism-validation identity because the signal is cross-scale and stable enough to survive Stage-1. But it should not receive prolonged optimization until it demonstrates a stable direction/shape and survives a stricter event-geometry baseline.

### R2 / R3 / R4 / R5-A / R5-B

No status change:

- R2 hold; no rescue tuning;
- R3 Stage-1 v1 closed;
- R4 V21 P2 family closed, Audit A/B sealed;
- R5-A and R5-B closed under R5 Stage-1 v1.

## Budget reset after review

The two-promotion review requirement is now satisfied.

The broad direction-finder may define **one new shallow results-blind discovery lane at a time**, but:

- it must not promote a third mechanism without another explicit cross-lane review;
- it must not consume the 2023–2025 reserve to design the next lane;
- it must not become the R1 or R5-C optimization repository;
- specialist deep work belongs in dedicated identities/handoffs.

## Next broad-program action

The next broad action is **new-lane definition, not empirical tuning**.

Use the still-unexplored parts of the program charter/literature map to write one bounded, results-blind shallow preanalysis before opening any new outcome slice. A natural candidate class is a frequency-band / multi-scale statistical-state mechanism, but it must receive a new identity and a very small measurement budget rather than being appended post hoc to R5 v1.

The 2023–2025 internal reserve remains unopened.

Production authority remains false.
