# STAR50 HighVol state-age mechanism study V8

Role: **Development-only mechanism research**, 2021-2023. No Validation or BlackBox query.

V7 exhaustively falsified the existing four-bit onset-path basis: none of the 16 fixed `{5m direction × slow alignment × tail2 acceleration × 5m efficiency}` cells met the common three-year economic gates. This round therefore leaves that onset feature space rather than adding another filter.

## Question

Does STAR50 become more directionally tradable only after HighVol has persisted for several consecutive completed minutes?

For every within-half-session consecutive `HighVol` run, define causal `highvol_age`:

- first HighVol minute in run: age 1;
- second consecutive HighVol minute: age 2;
- etc.;
- age resets when state is not HighVol or at half-session boundary.

Use four predeclared landmarks, at most once per run:

- `onset`: age 1;
- `early_persist`: age 2;
- `mature`: age 4;
- `late`: age 7.

These are state-age landmarks, not an optimization grid.

At each landmark, using information available through that completed minute:

- compute recent completed 5-minute net return and its sign;
- enter next-minute open in that sign direction;
- measure fixed 3-minute open-to-open signed continuation;
- also report unsigned 3-minute absolute displacement as a physical cost-capacity diagnostic.

No efficiency, tail2, slow-trend or cross-index filter is used. No candidate is nominated in this round.

## Outputs

For each landmark and 2021/2022/2023 plus pooled:

- eligible landmark count;
- mean/median signed 3m continuation;
- continuation hit rate;
- mean signed return after 1bp/leg;
- mean absolute 3m displacement;
- one-way break-even cost implied by mean signed continuation.

Interpretation rule: a landmark is merely `mechanism_promising` if each year has >=15 observations and each year's mean signed continuation after 1bp/leg is positive. This is not candidate promotion; any promising landmark must generate a separate Development candidate protocol before Validation.

## Governance

Workflow physically includes only STAR50 2020 warm-up and 2021-2023 Development rows. Validation and BlackBox rows are absent. BlackBox remains untouched.
