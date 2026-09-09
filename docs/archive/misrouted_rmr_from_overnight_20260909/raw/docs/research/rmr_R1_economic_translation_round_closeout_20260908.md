# R1 economic translation round closeout — 2026-09-08

Parent mechanism:

`rmr_cross_scale_pullback_parent_integrity_v2`

Parent mechanism status remains strong: reusable DEV/VALIDATION passed and the low-bandwidth 2026 BLACKBOX certification returned `PASS` without detail release.

This document closes the first economic-translation round. It does **not** downgrade the mechanism result; it separates mechanism validity from trading validity.

## Three bounded economic identities tested on DEV / VALIDATION

### v1 — probability edge only

Rule: trade when `p_parent_integrity > p_severity_only`, next-minute entry, original structural exits, 10bp round-trip cost.

Decision: `VALIDATION_FAIL_BLACKBOX_NOT_QUERIED`.

The filter improved over trading every R1 event, but PAIR_A mean return remained negative and PAIR_B annual stability failed.

### v2 — binary-boundary structural expectancy

Rule: v1 probability edge plus `p*recovery_gross + (1-p)*failure_gross - 10bp > 0`.

Decision: `VALIDATION_FAIL_BLACKBOX_NOT_QUERIED`.

The filter was too selective and still not stable across years/scales.

### v3 — direct realized-return regression

Rule: fixed Ridge(alpha=1) direct-return model with baseline `severity + recovery_gross + failure_gross`; candidate adds only parent integrity; trade if candidate predicted net > 0 and > baseline prediction.

Decision: `VALIDATION_FAIL_BLACKBOX_NOT_QUERIED`.

PAIR_A almost stopped trading; PAIR_B retained sample but remained economically negative and unstable.

## Cross-version conclusion

The evidence supports the following distinction:

> Parent integrity robustly helps classify recovery versus parent-state failure, but the currently tested execution geometry does not turn that information into stable positive index-reference trading returns after 10bp cost.

The failure is not evidence that the mechanism is false. It means the economic implementation is not established.

Three materially different low-capacity translations have now failed before BLACKBOX. Continuing to invent v4/v5 against the same detailed VALIDATION would create a growing risk of fitting the validation set rather than learning a general economic rule.

## Governance decision

- stop automatic R1 economic translation iteration after v3;
- BLACKBOX economic query count remains zero; total project BLACKBOX query count remains one;
- do not inspect any additional BLACKBOX detail;
- keep R1 mechanism certification as a research asset;
- production authority remains false;
- next active research budget moves to `rmr_event_density_state_reversal_v2` (R5-C), using the same reusable three-role data policy.

A future R1 economic identity is allowed only if motivated by new execution/instrument theory, not by another tweak to the same probability/geometry filters.
