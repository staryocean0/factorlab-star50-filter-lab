# 000852.SH 5m data provenance

These yearly Parquet shards were copied without transformation from:

`staryocean0/factorlab-trend-reversion-regime-lab`

Source paths:

`data/market/5m/000852.SH/{2015..2020}.parquet`

They are retained as yearly shards so cloud/connector tooling can read them directly without relying on the larger aggregated `data/development/5m_offset_0.parquet` file.
