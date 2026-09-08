# STAR50 fixed mechanism-cube falsification V7

Role: **Development-only falsification**, 2021-2023. Validation and BlackBox are not queried.

After the downside-break route failed Validation and several Development-only repair hypotheses failed, the purpose of this round is to stop serial filter invention and test the limits of the already-established coarse HighVol onset feature basis.

The basis is fixed and contains exactly 16 cells:

- recent 5m direction: up / down;
- prior 30m aligned with recent direction: true / false;
- `tail2_share >= 0.60`: true / false;
- 5m path efficiency `>= 0.60`: true / false.

All events are `NormalVol -> HighVol` onsets under the existing continuous-vol definition. No continuous thresholds are swept and no cells are ranked by best return.

For every cell, simulate direction-following 3-minute trades (up=long, down=short), entering next-minute open, same half-session, complete valid path, non-overlapping.

A cell is called `development_economically_stable` only if all of these predeclared gates hold:

- pooled trades >= 60;
- each of 2021/2022/2023 has >=15 trades;
- each year mean net after 1bp/leg >0;
- pooled mean net after 1bp/leg >0;
- pooled one-way break-even >1bp.

The screen is falsification/discovery, not candidate validation. A passing cell is only a hypothesis for a separately frozen candidate; it is not automatically promoted. If no cell passes, conclude that the current four-bit onset-path basis is insufficient for a stable STAR50 3-minute module and stop adding filters inside this basis.

Workflow must physically contain only 2020 warm-up plus 2021-2023 STAR50 files. BlackBox remains untouched.
