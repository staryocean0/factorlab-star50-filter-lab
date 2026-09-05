"""Export immutable development carriers only; no strategy or performance evaluation."""
import hashlib
import json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/drawdown_material"
OUT.mkdir(parents=True, exist_ok=True)
receipt = {"schema": "star50_drawdown_material@1", "performance_computed": False, "latest_allowed_day": "2025-12-31", "views": []}
manifest = json.loads((ROOT / "data/manifest.json").read_text())
for item in manifest["views"]:
    path = ROOT / item["file"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    df = pd.read_parquet(path)
    days = df["trading_day"].astype(str).str[:10]
    df = df.loc[days <= "2025-12-31"].copy()
    assert df["trading_day"].astype(str).str[:10].max() <= "2025-12-31"
    target = OUT / path.name
    df.to_parquet(target, index=False)
    receipt["views"].append({"view_id":item["view_id"],"source_sha256":item["sha256"],"export_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"rows":len(df),"columns":list(df.columns)})
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt, indent=2))
