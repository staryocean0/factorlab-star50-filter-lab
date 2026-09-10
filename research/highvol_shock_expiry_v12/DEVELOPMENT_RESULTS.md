# HighVol shock-expiry mechanism V12 — Development result

## Decision

**SIMPLE SHOCK-EXPIRY MECHANISM NOT SUPPORTED.**

Run `34450670358` completed successfully on Development-only data. Artifact `10141425271`, SHA256 `1dad9361257feb006656550ee4557db9425e7961ed29c03d9104ba4cd4db1829`.

The V11 60-minute crossover is strongly associated with whether the most recent shock is still inside the 12-bar `rv12` window, but the preregistered causal explanation "UNSAFE catches up because normalization spikes when the shock rolls out" is contradicted.

## Structural 60m split

Pooled rows with 13 future bars available:

| stratum | state | n | P(Normal within 60m) |
|---|---|---:|---:|
| latest shock still inside rv12 | UNSAFE | 1,822 | 0.9298 |
| latest shock still inside rv12 | RECOVERING | 4,849 | 0.8623 |
| latest shock already outside rv12 | UNSAFE | 5 | 0.8571 |
| latest shock already outside rv12 | RECOVERING | 598 | 0.9833 |

For the in-window stratum, `P60(RECOVERING)-P60(UNSAFE) = -0.06753`, and the gap is negative in 2021, 2022 and 2023.

For the expired stratum the pooled gap is positive, but only **5** UNSAFE observations exist across all three years (3 / 1 / 1). Therefore this apparent reversal cannot be treated as a stable state comparison.

## Deterministic expiry hazard

Among rows whose shock is still inside `rv12` and which remain non-Normal until the shock's deterministic window expiry:

- UNSAFE: n=1,736; `P(Normal in first 15m post-expiry)=0.7244`
- RECOVERING: n=4,350; `P(...)=0.7833`
- UNSAFE minus RECOVERING = `-0.05892`

The same sign holds in all three years:

- 2021: `-0.03250`
- 2022: `-0.06752`
- 2023: `-0.08433`

Thus normalization does **not** spike more strongly for current UNSAFE when the recent shock exits `rv12`.

## Structural implication

An important state property is nevertheless established descriptively: once the latest shock is older than the 12-bar realized-volatility window, `UNSAFE` is almost absent. The current UNSAFE label is therefore overwhelmingly a short-horizon/in-window state, while RECOVERING can persist after the shock return itself has left `rv12`.

This means V11's 60m crossover should not be explained by a simple expiry jump. The next Development-only test should first control the recent-shock clock **exactly at each 5m age 1..11** to determine whether the crossover survives exact-age standardization or is a bucket-composition/Simpson effect.

`validation_queried=false`  
`blackbox_queried=false`  
`production_authority=false`
