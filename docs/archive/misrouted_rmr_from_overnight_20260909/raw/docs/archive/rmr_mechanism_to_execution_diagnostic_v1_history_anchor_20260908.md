# Mechanism-to-execution diagnostic v1 — history anchor

Date: 2026-09-08  
Identity: `rmr_mechanism_to_execution_diagnostic_v1`

This file preserves the bounded implementation/execution history after completed diagnostic machinery is removed from the current repository surface.

## Frozen implementation

Final scientific execution commit:

`f35f64dcb567b681f583ae16881226c6ca738784`

At that commit the frozen implementation surface was:

- `scripts/run_rmr_mechanism_to_execution_diagnostic_v1.py`
- `tests/test_rmr_mechanism_to_execution_diagnostic_v1.py`
- `.github/workflows/mechanism-to-execution-diagnostic-v1.yml`
- `docs/research/rmr_mechanism_to_execution_diagnostic_v1_preanalysis_20260908.md`

The implementation reused certified R1/R2 event engines and frozen bundles without refit, read historical data only through `2025-12-31`, charged fixed 10bp round trip, used the certified 1200-bar structural horizon, and reported all fixed markouts `[1,5,15,30,60,120,240]` plus all fixed probability bins.

## Workflow execution

Authoritative scientific run:

- workflow run: `34226850838`
- job: `102062955823`
- conclusion: `completed / success`
- boundary/governance tests: `6/6 passed`
- detailed artifact ID: `10056093829`
- artifact ZIP SHA256: `841e079c9b4a9835c3c323f7dff010258a38f54d7afecfb49d215fc6a81df67a`

The full detailed JSON receipt was printed into the successful job log and uploaded as `rmr_mechanism_to_execution_diagnostic_v1.json` inside the workflow artifact.

There was one earlier workflow run, `34226460522`, which failed **before scientific execution** because a unit test incorrectly expected `NaN` for a mathematically valid break-even probability greater than 1.0. The implementation formula was correct; only that test expectation was fixed. No empirical diagnostic result was opened by that failed run and no research definition changed.

## Governance guarantees

The successful run verified:

- `max_read_day = 2025-12-31`
- `BLACKBOX_opened = false`
- `BLACKBOX_query_created = false`
- `selection_or_strategy_optimization_performed = false`
- `refit_performed = false`
- `production_authority = false`

The reusable BLACKBOX query count remained exactly 3. There is no query #4 from this study.

## Current retained evidence

Current-tree decisive evidence and interpretation are retained in:

- `docs/research/rmr_mechanism_to_execution_diagnostic_v1_decisive_receipt_20260908.json`
- `docs/research/rmr_mechanism_to_execution_diagnostic_v1_adjudication_20260908.md`

The completed runner, tests, workflow and preanalysis may therefore be deleted from current surface without losing reproducibility: their exact contents remain recoverable from the execution commit and Git history.

## Adjudicated next direction

The diagnostic authorized only a results-blind **R1_B execution-timing theory review**. It did not authorize a new strategy version, a selected markout horizon, instrument mapping, BLACKBOX access or production use.
