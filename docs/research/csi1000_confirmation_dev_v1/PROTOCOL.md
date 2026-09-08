# CSI1000 one-minute confirmation Development study V1

Development-only study. Validation and BlackBox are not queried.

Base setup remains the frozen CSI1000 long acceleration structure:

- `NormalVol -> HighVol` onset;
- recent 5m net > 0;
- preceding non-overlapping 30m net > 0;
- `tail2_share >= 0.60`;
- `tail1_share < 0.60`;
- long only;
- fixed 3m hold;
- 1 bp per execution leg as primary abstract friction.

Compare exactly three policies on 2021-2023:

1. `immediate`: enter next minute open.
2. `wait1_persist`: wait one complete minute; enter only if the state at that minute close remains `HighVol`.
3. `wait1_persist_positive`: same as (2), and the confirmation minute close-to-close return must be positive.

Each policy applies its own causal non-overlap rule. An onset that does not trigger a trade does not block later onsets. A completed trade uses exactly two execution legs and must stay within a valid half-session path.

Report annual and pooled trades, mean gross, mean net after 1 bp/leg, hit rate and one-way break-even cost. No threshold search is permitted inside V1.

A confirmation policy is eligible for later reusable Validation only if:

- every Development year has at least 15 trades;
- every Development year has positive mean net after 1 bp/leg;
- pooled trades >= 60;
- pooled one-way break-even cost > 1 bp.

If more than one confirmation policy is eligible, rank first by the worst annual mean net1, then pooled mean net1, then pooled trade count. `immediate` is a benchmark and is not re-nominated as a new candidate.
