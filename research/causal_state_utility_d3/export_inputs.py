"""Transport-only: verify twelve prior D2 5m sources and export lossless CSV.

No 3s read, no state calculation, no endpoint generation, fit, or D3 evaluation.
"""
from __future__ import annotations
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import urllib.request
import urllib.parse
import zipfile

import numpy as np
import pandas as pd

D2_SHA = "cf1c89e1412fd70f27992d9077af10dd7887a6843072e03ef808902bf5a84096"
D2_MANIFEST_SHA = "aa31cf36b09a4708be98c6867ee1db81063855d0fa87885ec52685c3e5fdd2c3"
SYMBOLS = ("000688.SH", "000852.SH")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/d3_input_transport"


class SafeArtifactRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != "https":
            raise RuntimeError("artifact redirect must remain HTTPS")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and urllib.parse.urlsplit(req.full_url).netloc != urllib.parse.urlsplit(newurl).netloc:
            redirected.remove_header("Authorization")
            redirected.remove_header("Accept")
        return redirected


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    token = os.environ["GH_TOKEN"]
    request = urllib.request.Request(
        "https://api.github.com/repos/staryocean0/factorlab-star50-filter-lab/actions/artifacts/10271634055/zip",
        headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"},
    )
    with urllib.request.build_opener(SafeArtifactRedirect()).open(request, timeout=120) as response:
        archive = response.read()
    assert sha(archive) == D2_SHA, "D2 ZIP identity mismatch"
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        b = z.read("input_manifest.json")
    assert sha(b) == D2_MANIFEST_SHA
    (OUT / "d2_input_manifest.json").write_bytes(b)
    manifest = json.loads(b)
    entries = {r["path"]: r for r in manifest["files"] if "path" in r}
    expected_paths = [f"data/market/5m/{s}/{y}.parquet" for s in SYMBOLS for y in range(2020, 2026)]
    got = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "data").rglob("*.parquet"))
    assert got == sorted(expected_paths), ("physical boundary mismatch", got)
    exports = []
    for path in expected_paths:
        p = ROOT / path
        original = p.read_bytes()
        entry = entries[path]
        assert sha(original) == entry["sha256"], path
        blob = hashlib.sha1(f"blob {len(original)}\0".encode() + original).hexdigest()
        assert blob == entry["git_blob"], path
        x = pd.read_parquet(p, columns=["trading_day", "timestamp", "close"])
        symbol, year = p.parent.name, int(p.stem)
        close = pd.to_numeric(x.close, errors="raise").astype(float)
        assert np.isfinite(close).all() and (close > 0).all()
        day = pd.to_datetime(x.trading_day, errors="raise").dt.strftime("%Y-%m-%d")
        wall = pd.to_datetime(x.timestamp.astype(str).str.slice(0, 19), errors="raise")
        assert (day == wall.dt.strftime("%Y-%m-%d")).all()
        assert (wall.dt.year == year).all()
        assert not wall.duplicated().any()
        assert day.value_counts().eq(48).all()
        result = pd.DataFrame({"symbol": symbol, "trading_day": day, "bar_end": wall.dt.strftime("%Y-%m-%dT%H:%M:%S"), "close": close})
        data = result.to_csv(index=False, float_format="%.17g").encode()
        roundtrip = pd.read_csv(io.BytesIO(data), float_precision="round_trip")
        assert np.array_equal(roundtrip.close.to_numpy(), close.to_numpy())
        filename = f"{symbol}_{year}.csv.gz"
        packed = gzip.compress(data, mtime=0)
        (OUT / filename).write_bytes(packed)
        exports.append({"source_path": path, "source_sha256": entry["sha256"], "source_git_blob": blob,
                        "csv_file": filename, "csv_gzip_sha256": sha(packed), "rows": len(result),
                        "price_roundtrip_exact": True, "first_day": day.min(), "last_day": day.max()})
    source_paths = [
        "research/causal_state_utility_d3/PROTOCOL.md", "research/causal_state_utility_d3/export_inputs.py",
        "scripts/validate_data_usage_policy.py", "docs/governance/DATA_USAGE_POLICY_V2.md",
        "docs/governance/data_usage_declaration.json", "docs/governance/blackbox_query_ledger.json",
    ]
    source_files = []
    for path in source_paths:
        b = (ROOT / path).read_bytes()
        dest = OUT / "source" / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b)
        source_files.append({"path": "source/" + path, "sha256": sha(b)})
    receipt = {
        "schema": "d3_input_transport_v1", "execution_location": "github_actions_transport_only",
        "execution_commit": os.environ.get("GITHUB_SHA"), "run_id": os.environ.get("GITHUB_RUN_ID"),
        "d2_artifact_id": 10271634055, "d2_zip_sha256": D2_SHA, "d2_input_manifest_sha256": D2_MANIFEST_SHA,
        "exports": exports, "source_files": source_files, "statistical_analysis_performed": False,
        "fit_performed": False, "queried_3s": False, "queried_2026": False,
        "blackbox_queried": False, "production_authority": False,
    }
    (OUT / "TRANSPORT_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"exported_files": len(exports), "all_price_roundtrips_exact": True,
                      "statistical_analysis_performed": False, "exports": exports}, sort_keys=True))


if __name__ == "__main__":
    main()
