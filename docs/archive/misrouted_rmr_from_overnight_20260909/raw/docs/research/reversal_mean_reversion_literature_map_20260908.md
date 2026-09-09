# Broad reversal / mean-reversion literature map — 2026-09-08

Purpose: constrain Stage-0/Stage-1 definitions for R1/R2/R3. This is not a complete survey and does not authorize model complexity.

## 1. Horizon and scale are part of the phenomenon, not a nuisance

Several literatures independently imply that “trend” and “reversal” can change sign with horizon.

- Moskowitz, Ooi & Pedersen, **Time Series Momentum**, JFE 2012, DOI `10.1016/j.jfineco.2011.11.003`: persistence over roughly 1–12 months followed by partial reversal at longer horizons across multiple asset classes.
- Jegadeesh, Luo, Subrahmanyam & Titman, **Short-Term Reversals and Longer-Term Momentum around the World: Theory and Evidence**, RFS 2025, DOI `10.1093/rfs/hhaf057`: short-horizon reversal transitions toward momentum at longer horizons.
- Plerou/related trend-reversion literature summarized in **Trends and reversion in financial markets on time scales from minutes to decades**, Physica A 2025, DOI `10.1016/j.physa.2025.130796`: the sign and strength of trend/reversion behavior varies across time scales.
- **Chinese stock return predictability: A time–frequency and shrinkage modeling approach**, Pacific-Basin Finance Journal 2026, DOI `10.1016/j.pacfin.2026.103201`: predictive content is heterogeneous across decomposed time scales in Chinese equities.

**Constraint for this program:** never define reversal without declaring lower/current/parent scale. A “sharp fall” is not intrinsically a reversal signal.

## 2. Event-based waves are a legitimate alternative to fixed clock windows

- Aloud, Tsang, Olsen & Dupuis, **A Directional-Change Event Approach for Studying Financial Time Series**, Economics 2012, DOI `10.5018/economics-ejournal.ja.2012-36`: directional-change events create an event-based or “intrinsic time” representation based on completed price moves rather than equal clock intervals.
- **Volatility measurement with directional change in Chinese stock market: Statistical property and investment strategy**, Physica A 2017, DOI `10.1016/j.physa.2016.11.113`: applies directional-change measurement to the Chinese stock market and emphasizes event-based capture of significant movements.

**Constraint for this program:** completed-wave representations are admissible, but the reversal confirmation that marks a wave complete must be causal. Future extrema may not be used to label the parent state at event time. Thresholds are measurement scales, not a free strategy-search axis.

## 3. Technical shape can be made testable, but pattern naming is not evidence

- Lo, Mamaysky & Wang, **Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation**, Journal of Finance / NBER 2000, DOI `10.3386/w7613`: converts visual chart patterns into systematic nonparametric recognition and compares conditional with unconditional return distributions.
- The classic trading-range / moving-average literature associated with Brock, Lakonishok & LeBaron shows why range/breakout rules can be stated mechanically, while later work highlights data-snooping concerns.

**Constraint for R2:** “support”, “resistance”, “range” and “breakout” must be algorithmic and causal. Stage 1 should study reentry versus continuation distributions, not rely on chart labels or optimized breakout filters.

## 4. Regime dependence is central to momentum/reversal coexistence

- **A regime-switching model of stock returns with momentum and mean reversion**, Economic Modelling 2023, DOI `10.1016/j.econmod.2023.106237`: a duration-dependent semi-Markov structure can generate short-term momentum followed by reversal.
- Focardi, Fabozzi & Mazza, **Modeling local trends with regime shifting models with time-varying probabilities**, International Review of Financial Analysis 2019, DOI `10.1016/j.irfa.2019.06.007`: persistence and switching of local trends can be represented with duration-dependent hidden-state models.
- Hammerschmid & Lohre, **Regime shifts and stock return predictability**, International Review of Economics & Finance 2018, DOI `10.1016/j.iref.2017.10.021`: regime factors can add predictive information beyond common predictors.
- Earlier Markov-switching work also documents state-dependent volatility and return dynamics.

**Constraint for R3:** it is reasonable to condition the expected path/distribution on market state, but Stage 1 should first test whether state conditioning improves residual reversion using a low-capacity state representation. Complex hidden-state models are not the starting point.

## 5. Koopman / latent dynamics is a possible later implementation, not the first hypothesis

- Liao et al., **Residual-Enhanced Adaptive Koopman Autoencoder: A Deep Latent Dynamics Model for Stock Prediction**, ICASSP 2026, DOI `10.1109/ICASSP55912.2026.11465125`: explicitly combines latent dynamics with a residual component for stock prediction.

This is aligned with the broad idea that a market may have multiple latent dynamics and that unexplained residual structure can carry information.

**Constraint for R3:** first show with simple state conditioning that (a) multiple states matter and (b) conditional residuals revert more cleanly than unconditional deviations. Only then consider Koopman/operator-count/residual architecture work.

## 6. Program-level synthesis

The literature does **not** imply that markets are generally mean reverting or generally trending. Instead it supports the program’s main framing:

1. behavior changes with **scale**;
2. behavior changes with **state/regime**;
3. an observed move must be judged relative to a **normal state appropriate to that scale/regime**;
4. the useful research target is the boundary between **temporary deviation** and **state transition**.

Therefore R1/R2/R3 are intentionally different ways to operationalize the same discrimination problem rather than three unrelated strategies.

## 7. First-pass implications

- R1 should compare lower-scale counter-moves under strong versus weak parent-state integrity, not simply “buy after a large fall.”
- R2 should define the range and its boundary causally, then compare reentry and extension without optimizing dozens of breakout thresholds.
- R3 should compare unconditional deviation with low-capacity regime-conditioned residual before any deep latent model.

The first empirical pass should be small enough that a negative result can close a lane honestly.
