#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifest.json"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> None:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert man["symbol"] == "000688.SH"
    for view in man["views"]:
        path = ROOT / view["file"]
        if not path.is_file():
            raise SystemExit(f"missing {path}")
        if sha256(path) != view["sha256"]:
            raise SystemExit(f"hash drift {path}")
        df = pd.read_parquet(path, columns=["symbol"])
        if set(df["symbol"].astype(str).unique()) != {"000688.SH"}:
            raise SystemExit(f"symbol leak {path}")
        if len(df) != int(view["rows"]):
            raise SystemExit(f"row drift {path}")
    usage = json.loads((ROOT / "docs/governance/data_usage_declaration.json").read_text())
    if usage["production_authority"]:
        raise SystemExit("production_authority must be false")
    print("theme package ok", len(man["views"]), "views")

if __name__ == "__main__":
    main()
