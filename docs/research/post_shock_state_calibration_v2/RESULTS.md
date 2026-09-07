# Post-shock state calibration V2 — accepted result

Date: 2026-09-08  
Protocol: `FROZEN_PROTOCOL.md`  
Scientific execution commit: `2bc6f0974df9bb7d5fa6757a9f14c21723c39ffa`  
Dedicated run: `34144466459`, job `101813353588` — **PASS**  
Full repository CI: run `34144466478`, job `101813353092` — **PASS**  
Evidence artifact: `post-shock-state-calibration-v2-34144466459`, artifact id `10027147885`, digest `sha256:b0005ce36e97578e70fb831fd5800c44fe846ab652f8fe83c0fccd95f0b92491`.

## Decision

**`state_calibration_not_supported`** under the pre-registered V2 adjudication.

This is a negative result for the proposed **three-state calibration**. It does not say the current risk ratio is useless. It says the fixed `LOW_CANDIDATE / RECOVERING / UNSAFE` partition does not preserve the required risk ordering out to both 5 and 10 trading minutes.

No threshold, checkpoint, horizon, event, or bootstrap setting was changed after observing the result. `LOW_CANDIDATE` is not promoted to `Clean`.

## Identity and reproducibility acceptance

The first V2 attempt failed closed before scientific outputs because it rebuilt CSI1000 first events on the individual index minute surface and obtained 26 instead of the sealed 25. Historical V2 evidence was then recovered and identity-bound before rerun:

- historical review run `34094586286`;
- historical review artifact digest `sha256:a7699589a8da489612a68caf9937a149c49e67dbe763f79210b2f215e6183b73`;
- exact inherited event universe SHA-256 `08bed092f87f9f08d617c117b1d0f4584eea1006cdb390d53b353e91b07b47ff`;
- exact event-ID match after restoring the already-sealed V2 joint-minute/common-session support semantics;
- STAR50 52 events, CSI1000 25 events, 77 total;
- 308 fixed checkpoint rows (`77 × 4`);
- bounded inputs are only 2024/2025 1m partitions for the two indices;
- `read_2026=false`, `fresh_oos=false`, economic/trading outcomes not evaluated.

The accepted run produced 286 eligible checkpoint rows for the 5-minute horizon and 268 for the 10-minute horizon; 22 and 40 rows respectively were censored/unobserved rather than bridged across session support.

Independent cloud review downloaded the Actions artifact, recomputed every entry in `output_manifest.json`, and found **0 hash/size mismatches**. The six scientific-output hashes in `execution_receipt_v2.json` also matched the downloaded files exactly.

The trailing-five-minute window semantics were independently checked against the inherited engine: session `minute` is 1..120. For an event at minute `m`, the +5 checkpoint uses returns from `m+1..m+5`; the next five-minute block uses `m+6..m+10`. The shock-minute return is therefore not accidentally included in the post-shock trailing-five score, and no off-by-one repair is required.

## Primary pooled calibration

Future outcome is the fixed state `UNSAFE` (`future z >= 1.5`) at the pre-registered 5- and 10-trading-minute horizons. Row-level Wilson intervals are descriptive because repeated checkpoints from the same event are dependent; event-cluster bootstrap is the supporting uncertainty check.

| Horizon | Current state | Rows | Distinct events | Future Unsafe | P(future Unsafe) | Row-level Wilson 95% |
|---|---|---:|---:|---:|---:|---:|
| 5m | LOW_CANDIDATE | 80 | 47 | 7 | 8.75% | 4.30%–16.98% |
| 5m | RECOVERING | 102 | 58 | 16 | 15.69% | 9.89%–23.97% |
| 5m | UNSAFE | 104 | 52 | 53 | 50.96% | 41.49%–60.36% |
| 10m | LOW_CANDIDATE | 74 | 44 | 12 | 16.22% | 9.53%–26.24% |
| 10m | RECOVERING | 98 | 58 | 13 | 13.27% | 7.92%–21.38% |
| 10m | UNSAFE | 96 | 50 | 29 | 30.21% | 21.93%–40.01% |

The required pooled ordering is monotone at 5m:

`8.75% <= 15.69% <= 50.96%`.

It fails at 10m because:

`16.22% > 13.27% < 30.21%`.

Therefore the protocol requires `state_calibration_not_supported`; no discretion remains to merge bins or move 1.0/1.5.

## Event-cluster uncertainty

Fixed 2,000-draw event-cluster bootstrap, seed `20260908`:

| Horizon | Contrast | Point difference | Cluster-bootstrap 95% |
|---|---|---:|---:|
| 5m | UNSAFE − LOW_CANDIDATE | +42.21pp | +30.83pp to +52.75pp |
| 5m | RECOVERING − LOW_CANDIDATE | +6.94pp | −2.41pp to +17.06pp |
| 10m | UNSAFE − LOW_CANDIDATE | +13.99pp | −0.60pp to +27.89pp |
| 10m | RECOVERING − LOW_CANDIDATE | −2.95pp | −14.12pp to +7.91pp |

Interpretation: the strongest reusable evidence is **short-horizon persistence of the already-Unsafe state**, not a stable three-level recovery ladder. The separation between RECOVERING and LOW_CANDIDATE is weak at 5m and reverses in the pooled 10m table. Even UNSAFE-vs-LOW separation is no longer cluster-bootstrap positive at the 10m horizon.

## Symbol/year stability

All three state bins have sufficient denominators for STAR50 2024, STAR50 2025, and CSI1000 2024. CSI1000 2025 is too small to test all three bins under the pre-registered denominator rule.

- STAR50 2024: 5m monotone; **10m non-monotone**.
- STAR50 2025: 5m monotone; 10m monotone.
- CSI1000 2024: 5m monotone; **10m non-monotone**.
- CSI1000 2025: insufficient LOW/RECOVERING denominators for formal three-bin stability adjudication.

The failure is therefore not produced only by the small CSI1000-2025 slice; both indices already show 10m non-monotonicity in 2024.

## Transition interpretation

Pooled 5m transitions:

- LOW_CANDIDATE → LOW/RECOVERING/UNSAFE: 61.25% / 30.00% / 8.75%;
- RECOVERING → LOW/RECOVERING/UNSAFE: 46.08% / 38.24% / 15.69%;
- UNSAFE → LOW/RECOVERING/UNSAFE: 11.54% / 37.50% / 50.96%.

Pooled 10m transitions:

- LOW_CANDIDATE → LOW/RECOVERING/UNSAFE: 52.70% / 31.08% / 16.22%;
- RECOVERING → LOW/RECOVERING/UNSAFE: 50.00% / 36.73% / 13.27%;
- UNSAFE → LOW/RECOVERING/UNSAFE: 29.17% / 40.63% / 30.21%.

This supports a decaying post-shock memory picture rather than a time-homogeneous three-state Markov interpretation based only on the current ratio.

## Elapsed-time secondary audit

The pre-registered elapsed-time audit finds residual descriptive information (within-state future-Unsafe probability spread >=10pp across denominator-sufficient checkpoints) in every state/horizon combination except LOW_CANDIDATE at the 5m horizon. In particular, current UNSAFE has 5m future-Unsafe probabilities of 63.41%, 36.36%, 53.33%, and 46.67% at +5/+10/+15/+20 checkpoints respectively.

These patterns are descriptive and dependent within events. They are evidence that the current ratio alone does not fully summarize post-shock age/state, not authority to optimize a timeout from these four values.

## What this closes

Closed under V2:

1. A simple three-bin state machine using only the current trailing-5m ratio is **not accepted** as a stable 5/10m recovery calibration.
2. `RECOVERING` is **not** empirically separable from `LOW_CANDIDATE` with the required stability.
3. The strong remaining signal is short-horizon `UNSAFE` persistence, strongest at 5m.
4. Elapsed time retains residual descriptive information, so a memoryless current-state-only representation is incomplete.

## Still frozen

This result does **not** change:

- `morphology_replication_not_yet_accepted`;
- the separate v0.6.17 prior-identity blocker;
- direction or third-wave labels;
- returns / P&L / MDD;
- fresh OOS;
- trading, position sizing, execution, or production;
- online `Clean` release authority.

A legitimate next experiment may study the **decay/survival of UNSAFE persistence as a function of post-shock age** with event-clustered inference and without tuning the 1.5 threshold. It must be separately pre-registered before its outcomes are computed.
