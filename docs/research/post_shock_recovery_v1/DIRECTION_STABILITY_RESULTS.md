# Shock-direction stability results

Date: 2026-09-07. Protocol: `DIRECTION_STABILITY_PROTOCOL.md`. Actions run `34131684547` succeeded; two frozen tests passed.

**Conclusion: first-shock direction does not add stable predictive value beyond the current five-minute recovery ratio. Keep the post-shock state machine direction-agnostic.**

## Training support warning

The pooled 2024 training set contains 54 first-shock episodes but is highly direction-imbalanced:

- up-shock events: 50;
- down-shock events: 4.

Therefore this diagnostic is not capable of establishing a reliable asymmetric up/down state mechanism. The imbalance itself is a reason not to promote direction-specific states from these data.

## 2025 fixed evaluation

81 checkpoints from 22 first-shock episodes; next-Unsafe base rate 33.3%.

| Model | Inputs | Log loss | Brier | AUC |
|---|---|---:|---:|---:|
| ratio_only | log(current recovery ratio) | **0.577842** | 0.201884 | 0.731139 |
| plus_direction | ratio + shock sign | 0.579610 | **0.200373** | **0.738683** |
| plus_interaction | ratio + sign + interaction | 0.584054 | 0.200809 | 0.735254 |

Paired event-cluster bootstrap delta log-loss versus ratio-only (negative would favor the challenger):

- plus_direction: point +0.00215; 95% interval **[-0.00956, +0.01382]**;
- plus_interaction: point +0.00617; 95% interval **[-0.00901, +0.02244]**.

Both intervals include zero and both point log-loss differences are worse. AUC/Brier move slightly in different directions, so there is no stable metric-level advantage.

## 2026 descriptive replay

41 checkpoints from 12 reconstructable events:

- ratio_only log loss 0.74172, AUC 0.72619;
- plus_direction log loss 0.74303, AUC 0.74524;
- plus_interaction log loss 0.74252, AUC 0.75238.

Again, rank metrics improve slightly while proper-score log loss/Brier do not. With the small and already-opened 2026 sample, this does not justify a direction-specific state.

## Implication

Do not add up/down shock direction, direction-specific thresholds, or sign interactions to the durable post-shock state representation. The supported primary state variable remains:

`recovery_ratio = trailing completed-5m RMS / fixed pre-shock sigma_pre`

with Unsafe >=1.5, otherwise Recovering, and no online Clean.

Future genuinely independent data may be used to revisit directional asymmetry only under a new preregistered protocol with adequate down-shock event support. No current threshold/window/event definition is changed.
