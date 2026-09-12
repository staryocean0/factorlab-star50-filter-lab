# Local integration handoff — prospective true reception recorder

This handoff is for a future local/DataHub integration agent. It is **not** evidence that live recording has begun.

## Goal

Instrument the real index-feed callback for `000688.SH` and `000852.SH` so a true local reception timestamp exists going forward. Do not reconstruct history.

Use `recorder.py` as the reference semantics. The local integration may adapt storage and APIs, but the first semantic operation at the actual callback boundary must capture:
- UTC wall-clock ns;
- monotonic ns;
- local sequence;
- raw payload identity;
before parse/normalization/queueing/model work.

## First integration stage: synthetic/replay only

Before exposing live market rows:
1. integrate the stamp call into the exact callback path;
2. feed synthetic or previously allowed replay payloads;
3. run local unit/integration tests;
4. verify sequence, monotonic, duplicate, parse-failure and restart behavior;
5. measure instrumentation overhead;
6. return only code/test/overhead receipts to the cloud research repository.

Do not call this `measured_feed_latency`.

## Live capture stage and governance

Because new post-2026-08-21 subject data can fall into pending BlackBox-V1, actual prospective rows must remain in protected local storage under repository governance. Do not upload captured row-level timestamps/prices to public GitHub or this chat unless governance explicitly assigns/permits them.

The local recorder integration must record its code commit/config hash/storage identity and recorder version. A process restart creates a new `recorder_instance_id`; monotonic values never bridge silently across restarts.

## Do not modify

Do not alter V19, D2-D5, D5R, thresholds, state labels, recovery tables, payoff/router logic, other strategy repositories or production trading permissions.

`production_authority=false`.
