# Fine-activity future-risk V1 — accepted Development result

Date: 2026-09-09
Branch: `research/fine-activity-future-risk-v1-20260909`
Frozen protocol: `FROZEN_PROTOCOL.md`
Successful dedicated run: `34302988723`
Execution commit: `d123afe2014dceb96b902f3233b2ae1ff43ac011`
Artifact id: `10085669383`
Artifact ZIP SHA-256: `9045f66fab1fdcce3c29c138fb59f2a292ad7f8930dbb3f5a21cf8fbecddd075`

## Decision

**`development_structure_not_established`** under the frozen V1 adjudication.

This is not rescued by changing M3 bands, the Unsafe threshold, the 15-minute horizon, or the 5pp criterion.

The run used 2022-05-16..2022-12-31 only as causal fine-scale reference warm-up and evaluated calendar 2023 Development only. Validation was not queried, BlackBox was not queried, no returns/P&L were evaluated, no candidate was nominated, and production authority remains false.

## Main result

Eligible Development rows: `64,887`:

- STAR50: `31,209`
- CSI1000: `33,678`

### STAR50 — M3 bands

| M3 | n | median future 15m RMS (bp) | P(any future Unsafe in 15m) |
|---|---:|---:|---:|
| <=0 | 21,268 | 4.2923 | 28.02% |
| (0,1] | 7,697 | 5.6874 | 30.99% |
| (1,2] | 2,033 | 6.6409 | 34.58% |
| >2 | 211 | 7.4059 | 27.49% |

The future-RMS ladder is strictly increasing and the top/bottom median ratio is far above the frozen 1.10 requirement. But the top M3 band does **not** have Unsafe probability at least 5pp above the bottom; its probability is slightly lower. That single frozen failure is enough to reject STAR50 under V1.

### CSI1000 — M3 bands

| M3 | n | median future 15m RMS (bp) | P(any future Unsafe in 15m) |
|---|---:|---:|---:|
| <=0 | 20,418 | 2.8251 | 29.54% |
| (0,1] | 10,136 | 3.5160 | 30.13% |
| (1,2] | 2,967 | 4.4226 | 35.36% |
| >2 | 157 | 5.9373 | 40.76% |

CSI1000 passes every frozen V1 structural check.

## Incremental control against ordinary 1m activity

Restricting to `C1z < 1` as frozen in advance:

| index | group | n | median future 15m RMS (bp) | P(any future Unsafe) |
|---|---|---:|---:|---:|
| STAR50 | M3<1 | 28,238 | 4.5722 | 28.49% |
| STAR50 | M3>=1 | 1,172 | 6.5510 | 31.48% |
| CSI1000 | M3<1 | 30,111 | 3.0260 | 29.58% |
| CSI1000 | M3>=1 | 1,676 | 4.1447 | 31.44% |

Thus M3 contains Development-period information about future continuous volatility even when ordinary minute-scale activity is not elevated. This is mechanism evidence, not candidate promotion.

## Failure interpretation

A post-result diagnostic using only the already-produced Development rows separated the inherited current-volatility state (`current 5m/preceding-30m RMS ratio >=1.5` = Unsafe) from non-Unsafe rows. No threshold was changed.

Within **current Unsafe**, M3 still strongly ranks future RMS, while future Unsafe probability declines with M3 in both indices:

- STAR50 future Unsafe: about 79.8% at M3<=0 -> 70.3% at M3>2;
- CSI1000 future Unsafe: about 81.0% at M3<=0 -> 70.8% at M3>2.

Within **current non-Unsafe**, future RMS again rises strongly with M3, but future Unsafe probability is not monotone.

This suggests that the V1 failure is not a generic absence of information. It is consistent with two distinct causal risk coordinates:

1. **absolute movement/activity axis** — M3 tracks the amount of subsequent movement;
2. **relative abnormal-state axis** — the inherited 5m/30m volatility ratio tracks Unsafe state/persistence.

The two axes should not be collapsed into one scalar risk ladder without a separate test.

## What remains closed

- No first-shock classifier is reopened.
- No HighVol sign/direction candidate is reopened.
- M3 is not promoted as a universal Unsafe predictor.
- M4 cannot rescue the V1 failure; it shows the same qualitative decoupling on STAR50.
- Validation remains unread by this V1 experiment.
- BlackBox query count remains unchanged at zero.
- `production_authority=false`.

## Legitimate next diagnostic

A separately frozen Development-only **two-coordinate risk decomposition** may test the fixed pair:

- M3 activity surprise;
- inherited current volatility ratio / Unsafe state.

Its role is architecture/mechanism diagnosis only: determine whether future movement magnitude and future Unsafe persistence are genuinely separable risk coordinates. It must not tune M3, the 1.5 Unsafe threshold, or convert the result into a trading rule.
