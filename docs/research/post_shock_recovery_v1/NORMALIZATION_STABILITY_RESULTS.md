# Recovery-ratio normalization stability results

Date: 2026-09-07. Protocol: `NORMALIZATION_STABILITY_PROTOCOL.md`. Actions run `34131277843` succeeded; two frozen tests passed.

**Conclusion: background pre-shock volatility does not add stable predictive value beyond the normalized recovery ratio. Keep `recovery_ratio = trailing5m RMS / fixed sigma_pre` without a separate volatility-regime state.**

## 2025 fixed evaluation

Fit pooled STAR50+CSI1000 2024 only; evaluate 81 checkpoints from 22 2025 first-shock episodes.

| Model | 2025 log loss | Brier | AUC |
|---|---:|---:|---:|
| ratio_only | 0.577842 | 0.201884 | 0.731139 |
| plus_background | **0.577597** | **0.201715** | **0.732510** |
| plus_interaction | 0.580272 | 0.202973 | 0.731139 |

The tiny point improvement from adding `log(sigma_pre)` is not stable. Paired event-cluster bootstrap delta log-loss versus ratio-only:

- plus_background: point -0.00049; 95% interval **[-0.00150, +0.00064]**;
- plus_interaction: point +0.00233; 95% interval **[-0.00314, +0.00785]**.

Both intervals include zero. The interaction point estimate is worse.

## 2026 descriptive replay

41 checkpoints from 12 reconstructable events:

- ratio_only log loss 0.74172, AUC 0.72619;
- plus_background log loss 0.74278, AUC 0.72381;
- plus_interaction log loss 0.74007, AUC 0.71905.

No model wins consistently across scoring rules, and none provides a reason to change the frozen normalization.

## Background-volatility strata

2024 log-sigma tertiles were frozen and applied to 2025/2026 only for descriptive checks. Several low/mid-sigma state cells contain very few events, so cell percentages must not be treated as calibration targets. The sparse strata do not support a separate regime-specific threshold.

## Implication

The current denominator is adequate for the operational research abstraction found so far: the latest normalized activity ratio carries the useful state information without requiring a separate background-volatility state or interaction.

This does **not** prove exact distributional invariance across volatility regimes. It only says current data do not justify complicating the state machine.

No 1.0/1.5 boundary, event definition, five-minute window, Clean policy or trading rule is changed.
