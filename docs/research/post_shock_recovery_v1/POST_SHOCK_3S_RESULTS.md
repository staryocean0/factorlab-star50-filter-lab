# Post-shock 3-second recovery prediction results

Date: 2026-09-07. Protocol: `POST_SHOCK_3S_PROTOCOL.md`.

**Result: first 2/5 minutes of gap-clean 3-second price path do not produce a high-confidence release signal on 2025. Do not promote online Clean.**

Common complete-path support: 52 pooled 2024 events for fitting and 20 pooled 2025 events for evaluation. The stable-next-10m rate on this support is 13.46% in 2024 and 15.0% in 2025.

At the fixed +5 minute checkpoint:

| Model | 2025 AUC | Brier | max predicted P(stable) | releases at P>=0.80 |
|---|---:|---:|---:|---:|
| E0 event-only | 0.392 | 0.138 | 0.341 | 0 |
| E2 + first 2m 3s path | 0.529 | 0.154 | 0.616 | 0 |
| E5 + first 5m 3s path | 0.588 | **0.131** | 0.358 | 0 |

No model produces any release at the preregistered 0.80 or 0.90 probability threshold. E5 slightly improves Brier versus E0 and AUC versus E0/E2, but the evaluation set is only 20 events and the absolute discrimination remains weak. This is insufficient for a hard release gate.

Therefore the current conclusion is unchanged:

- post-shock risk duration is real and measurable;
- `Unsafe -> Recovering` is supported;
- neither minute cooling rules nor the observed first 2/5 minute 3-second price path validates a causal `Recovering -> Clean` transition;
- do not search more thresholds on the same 2024-2025 events.

The next legitimate way to improve statistical support is to use earlier eligible historical years under a newly frozen sequential split, or obtain additional truly independent future data. No additional market field is missing for the former; it is a sample-support / research-design issue, not an order-book-data blocker.
