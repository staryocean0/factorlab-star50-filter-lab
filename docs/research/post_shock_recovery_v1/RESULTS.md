# Post-shock recovery state V1 results

Date: 2026-09-07. Branch: `research/first-shock-seconds-v2-20260907`.

**Result: post-shock risk duration is measurable, but no tested causal hard-release rule is safe enough. Keep `Unsafe -> Recovering`; do not promote an online `Clean` transition yet.**

## Data and frozen outcome

Uses the sealed V2 first-event universe in 2024-2025: 52 STAR50 events and 25 CSI1000 events. No new data, no 2026, no trading. The primary future-risk state at lag k is the RMS of the next five minute returns divided by the event's pre-shock `sigma_pre`: `Unsafe >=1.5`, `Recovering 1.0..1.5`, `Clean-candidate <1.0`.

Descriptive release-start requires **two consecutive non-overlapping future five-minute blocks** both below pre-shock background. Because that condition needs ten future minutes, an online observer can only confirm it ten minutes after the release-start. Missing/session-truncated outcomes are censored, not Clean.

## 1. Risk decays, but not immediately

| Index | Unsafe immediately after shock | Unsafe at +5m | Unsafe at +10m | Unsafe at +15m | Unsafe at +30m |
|---|---:|---:|---:|---:|---:|
| STAR50 | 54.9% | 40.0% | 20.8% | 22.9% | 18.8% |
| CSI1000 | 56.0% | 52.0% | 20.0% | 20.8% | 10.5% |

The denominators shrink at longer lags because a half-session ends; these are descriptive observed fractions, not censor-adjusted survival probabilities.

The same pattern remains in `quiet_first` events: risk is high immediately after the first shock and decays over the following tens of minutes. This confirms that the post-shock state effect is not only driven by events that were already active before the shock.

## 2. Censor-adjusted release duration

Kaplan-Meier correction is used because unreleased/session-truncated events otherwise bias the duration downward.

| Index | Events | Raw censor share | KM median release-start | KM released by 10m | by 15m | by 30m |
|---|---:|---:|---:|---:|---:|---:|
| STAR50 | 52 | 28.8% | **14m** | 37.0% | 52.5% | 73.4% |
| CSI1000 | 25 | 24.0% | **19m** | 36.0% | 44.9% | 73.7% |

Online confirmation of the median descriptive release occurs ten minutes later: about **24 minutes for STAR50** and **29 minutes for CSI1000** under this strict definition.

For `quiet_first`, the KM median release-start is 14m for STAR50 and 11m for CSI1000. Small samples, especially CSI1000-2025, remain a major limitation.

## 3. Simple online release rules fail

Three rules were frozen before evaluation:

- R1: trailing five-minute RMS < background;
- R2: R1 + no trailing minute exceeds 1.5 sigma;
- R3: R2 + trailing two-minute RMS <0.8 sigma.

They trigger often, but the next ten minutes frequently reactivate. Pooled stable-release precision / false-release share:

| Rule | STAR50 | CSI1000 |
|---|---:|---:|
| R1 | 34.1% / **65.9% false** | 33.3% / **66.7% false** |
| R2 | 36.6% / **63.4% false** | 31.6% / **68.4% false** |
| R3 | 41.2% / **58.8% false** | 31.6% / **68.4% false** |

Fixed releases at +10/+15/+20/+30 minutes are not reliable either. In pooled 2024, releasing at +10m has only 15.4% stable-next-10m precision; +15m only 22.4%. Waiting a fixed amount of time does not by itself establish safety.

## 4. Small causal release model has ranking signal, but no high-confidence Clean state

A fixed logistic model was registered after the rule failure, trained on pooled 2024 and evaluated on pooled 2025. Inputs: elapsed time, trailing 5m/2m activity, event amplitude/background, quiet-first, index, and event-minute 3s path concentration/efficiency. No feature or hyperparameter search.

2025 evaluation: 70 checkpoint rows from 20 events, stable-next-10m base rate 30.0%. ROC AUC = **0.778**, Brier = **0.176**. However **no row reaches the preregistered 0.80 or 0.90 release probability threshold**. Therefore the model has some ranking information but cannot support a high-confidence hard release.

The strongest standardized coefficient is lower trailing-two-minute activity (coefficient -1.13 for activity, so lower recent activity raises stable probability), followed by elapsed time and background sigma. These coefficients are exploratory and should not be interpreted causally.

## 5. State definition after this round

The evidence supports a three-state research framework, but only two states are currently causally observable with confidence:

- **Unsafe:** first ~10 minutes after a first shock should remain explicitly high-risk; the future-five-minute Unsafe fraction is still about 20% even around +10m.
- **Recovering:** after ~10 minutes, risk generally declines toward background but retains a substantial reactivation tail. Current price-only cooling rules cannot safely terminate this state.
- **Clean:** **not yet validated as an online transition.** For scientific labels, Clean may be assigned retrospectively only after the two future low-volatility blocks; this is an outcome label, not a deployable signal.

Do not convert the descriptive median duration into a fixed production timeout.

## 6. Next research direction

Existing data are sufficient. The next experiment should predict `stable_next10` using richer **post-shock** 3-second information in the first 1/2/5 minutes (short-horizon concentration, path efficiency, realized variation, reversals, and gap-aware activity), with 2024 fit and 2025 fixed evaluation. The target remains post-shock release, not pre-first-shock prediction.

No user assistance or new data is currently required.
