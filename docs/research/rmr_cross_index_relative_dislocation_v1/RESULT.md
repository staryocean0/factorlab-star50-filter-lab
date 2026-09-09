# RMR cross-index relative dislocation V1 — RESULT

Run: `34325030243`

Verdict: **`broad_signal_source_not_established`**.

Development-only rows: 58,160 across 2021–2023. Validation and BlackBox were not queried.

The tested mechanism showed the opposite of mean reversion:

- high-Z median signed future residual was positive in every year;
- pooled high-Z `signed_F15` median = +5.1128 bp;
- pooled recovery50 probability fell from 40.23% in low-Z to 16.56% in high-Z;
- both `STAR50_rich` and `STAR50_cheap` high-Z directions extended rather than reverted.

Therefore temporary paired-index residual displacement under this fixed trailing-OLS definition is **not** an RMR signal source. Do not rescue with HighVol, clock, direction or threshold changes under this identity.

The result may be useful to a momentum/relative-extension program, but that is outside this lane's authority.

`production_authority=false`.
