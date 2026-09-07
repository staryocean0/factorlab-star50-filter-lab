"""Download declared public sources; preserve failures and never overwrite PDFs."""

import concurrent.futures
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent


def inspect(data):
    if not data.startswith(b"%PDF-"):
        raise ValueError("not a PDF (HTML/challenge/error responses are not full text)")
    with tempfile.NamedTemporaryFile(suffix=".pdf") as handle:
        handle.write(data)
        handle.flush()
        info = subprocess.check_output(["pdfinfo", handle.name], text=True)
        pages = int(re.search(r"Pages:\s+(\d+)", info)[1])
        text = subprocess.check_output(["pdftotext", handle.name, "-"], text=True)
    texts = text.split("\f")
    if not texts[-1].strip():
        texts.pop()
    if not texts or sum(map(len, texts)) < 500:
        raise ValueError("empty or non-text PDF; manual inspection required")
    return dict(
        pages=pages,
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
        first_page_excerpt=texts[0][:400],
        last_page_text_chars=len(texts[-1]),
    )


def acquire(item):
    result = {"id": item["id"], "title": item["title"], "attempts": []}
    existing = ROOT / item.get("existing", item["file"])
    if existing.exists():
        return {**result, "status": "existing", "path": str(existing.relative_to(ROOT)), **inspect(existing.read_bytes())}
    for url in item["urls"]:
        try:
            response = requests.get(url, timeout=(12, 35), headers={"User-Agent": "FactorLab-Research-Archive/1.0"})
            attempt = {"url": url, "status_code": response.status_code, "final_url": response.url}
            result["attempts"].append(attempt)
            response.raise_for_status()
            evidence = inspect(response.content)
            with (ROOT / item["file"]).open("xb") as handle:
                handle.write(response.content)
            return {**result, "status": "downloaded", "path": item["file"], **evidence}
        except Exception as exc:
            result["attempts"].append({"url": url, "error": str(exc)})
    return {**result, "status": "missing"}


if __name__ == "__main__":
    items = json.loads((ROOT / "sources.json").read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(acquire, items))
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    receipt = {
        "retrieved_at": stamp,
        "sources_sha256": hashlib.sha256((ROOT / "sources.json").read_bytes()).hexdigest(),
        "results": results,
    }
    (ROOT / f"download_receipt_{stamp}.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    for row in results:
        print(row["id"], row["status"], row.get("pages", ""), row["title"], flush=True)
