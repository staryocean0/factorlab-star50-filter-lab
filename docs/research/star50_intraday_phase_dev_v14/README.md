# STAR50 intraday-phase V14 — Development only

Question: does STAR50 HighVol onset become a cost-covering 3-minute continuation/reversal module only in a fixed structural time-of-day regime?

Event: causal `NormalVol -> HighVol` on `000688.SH`.

Fixed half-session phase bins (no tuning):
- early: minute 35–60
- middle: minute 61–90
- late: minute 91–120

Also retain half-session identity: AM (`/0`) vs PM (`/1`). Views are `all`, the 3 phase bins, and the fixed 2×3 half×phase bins.

Direction reference: sign of latest five valid one-minute close-to-close returns. Execution diagnostic: next-minute open, fixed 3-minute hold, same half-session, complete valid path, non-overlapping accepted events.

Report continuation and reversal for 2021/2022/2023 and pooled. A view is `mechanism_promising` only if all three years have >=15 events and either continuation or reversal is positive after 1 bp per leg in every year. No candidate is automatically nominated.

Development 2021–2023 only; 2020 warm-up allowed; no Validation; no BlackBox.
