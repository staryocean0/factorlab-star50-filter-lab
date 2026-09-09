# R5-C reusable specialist closeout — 2026-09-08

Research identity: `rmr_event_density_state_reversal_v2`

Final decision:

`R5C_V2_DETAILED_VALIDATION_PASS_REUSABLE_BLACKBOX_FAIL_CLOSE_IDENTITY`

## What survived detailed validation

The dedicated specialist test was materially stricter than the original Stage-1 screen. Event density had to add information beyond nearby event geometry:

- completed-wave severity;
- completed-wave duration;
- bars since the previous same-scale confirmation.

The only candidate increment was the frozen 240-bar event-density z-score normalized by the preceding 100 same-scale observations.

Detailed 2021–2025 VALIDATION passed on both co-primary scales:

- S1 pooled Brier improvement `0.0002169367`, pooled log-loss improvement `0.0004382590`, annual Brier direction 4/5;
- S2 pooled Brier improvement `0.0009287248`, pooled log-loss improvement `0.0019145031`, annual Brier direction 5/5.

This is legitimate evidence that event density contains small incremental state information beyond simple nearby event geometry in the reusable detailed validation pool.

## What the BLACKBOX established

After the preregistered DEV+VALIDATION final refit, candidate bundle

`36e40c3b209f3179dd0d9612af3396277cf96af0513c259a6090e39a2306fc7a`

was submitted as project BLACKBOX query #2.

Public result:

**FAIL**

That is the complete allowed BLACKBOX scientific output. No exact metric, count, date, month, scale-specific result, event, probability, subgroup or failure example was released or used for diagnosis.

## Interpretation

The result must not be rewritten as “event density has no information.” Detailed reusable VALIDATION says the dedicated feature did add small stable information historically. The BLACKBOX says the frozen R5-C v2 package did **not** earn final certification on the current reusable recent-data certifier.

Both statements are simultaneously true.

Because no BLACKBOX breakdown is available, no R5-C v2 rescue may be justified by recent-period behavior. In particular, do not:

- choose S1 or S2 based on the BLACKBOX;
- change the 240-bar density window;
- search the 100-observation normalization history;
- add a z threshold;
- add interactions or extra state features;
- relax BLACKBOX gates;
- infer which period or event class failed.

## Program implication

R5-C v2 is closed. R1 parent-integrity remains the only currently BLACKBOX-certified mechanism, while its first economic-translation family is separately closed after VALIDATION failure.

The next research budget should not create R5-C v3 automatically. A new R5-C identity would require an independently motivated scientific representation, not a response to this BLACKBOX FAIL.

Production authority remains false.
