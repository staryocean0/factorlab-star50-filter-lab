# Recovery score window-length diagnostic

Date: 2026-09-07. Diagnostic only; the five-minute primary score was already frozen before this comparison and is not changed here.

## Question

Could a shorter two-minute activity window react faster without losing forward-risk information, or would a longer ten-minute window provide materially better stability than the current five-minute score?

At post-shock checkpoints, compare trailing 2m / 5m / 10m RMS (each divided by fixed event-time `sigma_pre`) against the following five-minute realized RMS ratio.

## 2024-2025 historical comparison

At +5/+10/+15/+20 checkpoints, where 2m and 5m are both available:

| Period | Predictor | log-risk RMSE | Spearman vs next5 |
|---|---|---:|---:|
| 2024 | trailing 2m | 0.699 | 0.419 |
| 2024 | **trailing 5m** | **0.556** | 0.401 |
| 2025 | trailing 2m | 0.855 | 0.366 |
| 2025 | **trailing 5m** | **0.471** | **0.641** |
| pooled | trailing 2m | 0.745 | 0.407 |
| pooled | **trailing 5m** | **0.534** | **0.477** |

The shorter score is much noisier in magnitude, especially in 2025.

For checkpoints where a full trailing ten-minute window also exists:

- pooled log-RMSE: 2m 0.815, 5m 0.547, 10m 0.543;
- pooled Spearman: 2m 0.267, **5m 0.403**, 10m 0.396;
- in 2025, 5m is better than 10m on both RMSE (0.500 vs 0.523) and rank (0.498 vs 0.453).

Thus ten minutes provides no stable enough gain to justify doubling the reaction lag.

## 2026 fixed validation snapshot

The already-exported 2026 checkpoint table contains both trailing2 and trailing5 without any new fitting:

- trailing2: log-RMSE about 0.666, Spearman about 0.371;
- **trailing5: log-RMSE about 0.536, Spearman about 0.433**.

The direction therefore matches the prior diagnostic: the two-minute window reacts faster but is materially noisier as a forward state proxy.

## Decision

Keep the frozen primary recovery score unchanged:

`recovery_ratio = trailing 5m RMS / fixed pre-shock sigma_pre`

Implementation may update this rolling five-minute score every completed minute. The window length is five minutes; the update interval does not need to be five minutes.

Do not substitute trailing2 for a faster `Clean` decision. Do not switch to trailing10 merely for smoother curves. Any future alternative window must be registered before genuinely new independent data are opened.
