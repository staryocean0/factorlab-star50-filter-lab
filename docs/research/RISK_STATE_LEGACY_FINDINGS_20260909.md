# Retained risk-state findings extracted from archived strategy research

Date: 2026-09-09

These findings came from experiments whose primary object was payoff/account performance and therefore no longer belongs in active STAR50 strategy authority. Only the bottom-layer K-line/risk knowledge is retained here.

## 1. Slow-direction conflict is a risk annotation, not a complete loss explanation

The historical drawdown studies defined a causal slow-direction conflict using a much slower low-pass displacement versus the faster working state. This condition carried some information about weaker realized strategy quality and sometimes coincided with large drawdowns.

However:

- it did not explain all large drawdowns;
- its overlap with a working-path chop condition was small in important episodes;
- some large events occurred without the chop condition;
- after one-minute execution delay and cost stress, its historical MDD advantage over an equal-average-exposure control disappeared.

Retained use: **possible risk/context annotation only**. Do not revive the historical half-exposure overlay as current STAR50 policy.

## 2. Working-path chop and slow conflict are not universal `Unsafe` definitions

Historical mutual-state tables showed that no-condition, chop-only, slow-conflict-only and joint states could all have positive average gross contributions under the old strategy/account definition. The joint state was weaker but sparse.

Retained use: these coordinates may help characterize path conflict, but neither is sufficient as a universal `Unsafe` label and neither should be promoted from old PnL tables.

## 3. Displacement concentration is a real morphology coordinate

The `wave_shape_v1` work remains in active research because its primary reusable result concerns K-line path morphology:

- moving the same broad displacement into fewer bars can materially change filter/turning-point timing;
- identical frequency-energy content with different relative phase can produce very different path shapes;
- in historical matched cycles, higher displacement concentration was associated with poorer capture by the old slow filter, while a simple left/right skew sign was not a stable general rule.

Retained use: **displacement concentration / phase arrangement / sharp-move morphology are legitimate bottom-layer attributes**. They are not by themselves a trading rule or causal market mechanism.

## 4. Q12-style concentration persistence was not supported

The archived `three_proposals_v1` study tested whether a recent displacement-concentration statistic persisted into a subsequent non-overlapping block. The predeclared tests did not support stable persistence at that definition/scale.

Retained use: do not build a risk-state transition model that assumes `recent concentrated move -> next block concentrated` without new evidence. This is negative mechanism evidence, not proof that all clustering definitions fail.

## 5. Execution and cost fragility belong outside the state definition

Historical execution-counterexample work showed that the economic benefit of some overlays changed materially with one-minute delay and cost assumptions. This is useful evidence that **state measurement and payoff executability must remain separate layers**.

Retained use: a K-line state may be statistically meaningful even when a particular payoff overlay is not economically stable. Do not define `Unsafe`, `Recovering` or `HighVol` by the PnL of one carrier/account implementation.

## 6. Conditional buckets from ETF/options accounts are not K-line state labels

The archived conditional-account work found different economic behavior across ETF and option implementations for the same signal-side conditions. Some conditions improved one objective but harmed another, and all option accounts in that experiment still lost money.

Retained use: instrument/account response is not a bottom-layer state label. Keep state semantics on the index/K-line surface and map to tradable carriers only in a separate strategy/execution bucket.

## Boundary

These retained findings may motivate new STAR50 risk-state hypotheses, but none of them reopens the archived payoff strategies or grants production authority.

`production_authority=false`.
