# V13 exact recent-shock-age composition — Development results

Status: **REJECT simple exact-age composition explanation**.

Execution authority:

- branch: `research/highvol-exact-age-composition-v13-20260910`
- execution commit: `0468f359ccb997c7509746f95cabf0b6ace789d4`
- Actions run: `34453481183`
- artifact: `10142490057`
- artifact SHA256: `431e6ad640a4a2b7b8d1fc0f41e2084efccbae9ff26034eb51a1887cac70a897`
- Development only: 2021–2023, 2020 warm-up
- Validation queried: false
- BlackBox queried: false

## Primary 60-minute adjudication

On exact ages common to both states, the raw pooled 60m recovery gap remained negative:

`P60(RECOVERING) - P60(UNSAFE) = -0.0579430`.

After forcing both states onto the same exact recent-shock-age distribution, the pooled gap was still negative:

`standardized gap = -0.0269627`.

Annual standardized 60m gaps were also negative in all three Development years:

- 2021: `-0.0315496`
- 2022: `-0.0210470`
- 2023: `-0.0428553`

Therefore the V11 60m state-rank crossover is not explained by a simple Simpson-style exact-age composition artifact.

## Exact-age structure

For pooled 60m recovery, `RECOVERING - UNSAFE` was negative at exact ages 1 through 10 bars. It turned positive only at ages 11–14, where UNSAFE support becomes very small beyond the fixed 12-bar volatility window.

The pooled state age distributions were not dramatically different within the main support:

- UNSAFE: n=1,832, median recent-shock age=6 bars; 99.73% at ages 1–11.
- RECOVERING: n=5,495, median=6 bars; 89.08% at ages 1–11.

Standardizing that difference did not remove the 60m reversal.

## Interpretation

`UNSAFE` and `RECOVERING` are useful risk states, but they are **not a horizon-invariant ordinal severity scale**. Their meaning is horizon dependent:

- near-term (15m/30m): RECOVERING implies higher normalization probability than UNSAFE;
- 60m: on the same recent-shock-age distribution, UNSAFE can have higher cumulative normalization probability.

This does not invalidate the validated 15m V6/V9/V10 risk object. It rejects only the stronger assumption that one scalar state ordering should hold across 15/30/60m horizons.

Next Development question: test whether `current_state` adds predictive information beyond recent-shock age separately at each fixed horizon. If yes, define a horizon-specific risk surface rather than forcing a single ordinal survival curve.

No Validation is authorized from V13 itself. `production_authority=false`.
