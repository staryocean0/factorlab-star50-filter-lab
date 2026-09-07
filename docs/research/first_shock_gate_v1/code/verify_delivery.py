"""Verify delivered research files, not market inputs or scientific validity."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "delivery_manifest.json").read_text())
for item in manifest["files"]:
    path = (root / item["path"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"missing or unsafe path: {item['path']}")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise ValueError(f"hash mismatch: {item['path']}")
print(json.dumps({"status": "passed", "files": len(manifest["files"]),
                  "market_validation": False, "production_authority": False}))
