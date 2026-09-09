# Unified parent-state router v1 history anchor — 2026-09-08

The current worktree intentionally removes the completed router implementation after its detailed VALIDATION failure.

Full corrected implementation is preserved at commit:

`d3ffab43c9e2d7ad4f644a81e3d15d0628686811`

Workflow runs:

- first attempt `34222093181`: 13 tests passed, then fail-closed before event construction because the runner incorrectly re-estimated the already-certified directional-change scale under the later reusable DEV window; no router outcome and no BLACKBOX access occurred;
- corrected attempt `34222392969`: reused the certified frozen scale, passed tests, ran detailed 2021–2025 VALIDATION, failed the frozen router gates, and skipped BLACKBOX.

The full implementation tree contains the protocol, DEV/VALIDATION runner, low-bandwidth BLACKBOX certifier, tests and bounded workflow.

Current scientific evidence is retained in:

- `docs/research/rmr_unified_parent_state_router_program_review_20260908.md`
- `docs/research/rmr_unified_parent_state_router_v1_validation_adjudication_20260908.md`
- `docs/research/rmr_unified_parent_state_router_v1_closeout_20260908.md`

No BLACKBOX query #4 occurred.
