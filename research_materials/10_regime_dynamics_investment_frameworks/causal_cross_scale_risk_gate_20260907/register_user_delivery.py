"""Register three explicitly user-provided PDFs after byte-preserving moves."""

import csv
import json
import subprocess
import sys

from acquire import inspect
from audit_archive import LIB, ROOT, append_csv, digest

DELIVERY = [
    (
        "biomet%2F41.1-2.100.pdf",
        "page_1954_continuous_inspection_schemes.pdf",
        16,
        "d8912c002df77c41420ba70f0158bf8c5a7ef3a165a993e969c70e0f35acfd3d",
        "Continuous Inspection Schemes",
        "10.1093/biomet/41.1-2.100",
    ),
    (
        "nbac031.pdf",
        "kwok_2024_autocorrelated_jump_occurrences.pdf",
        30,
        "56c059b335ce1c38049072a93c194758fdc158f92bc26c3d52b276ddb35fd95a",
        "A Consistent and Robust Test for Autocorrelated Jump Occurrences",
        "10.1093/jjfinec/nbac031",
    ),
    (
        "nbae009.pdf",
        "chen_2024_jump_clustering_forecasting.pdf",
        28,
        "9a186c3fdaface3107495c85529c40745329c194806c61e98ccc0a7ee76ec3b5",
        "Jump Clustering, Information Flows, and Stock Price Efficiency",
        "10.1093/jjfinec/nbae009",
    ),
]


def main():
    records = []
    for source, target, pages, expected, title, doi in DELIVERY:
        path = ROOT / target
        evidence = inspect(path.read_bytes())
        assert evidence["sha256"] == expected and evidence["pages"] == pages
        assert not (ROOT.__class__("/home/starryocean/桌面") / source).exists()
        records.append(
            {
                "source": "桌面/" + source,
                "target": str(path.relative_to(LIB)),
                "title": title,
                "doi": doi,
                "source_sha256_before_move": expected,
                "byte_preserving_move": True,
                "visual_title_author_verified": True,
                "acquisition": "user_provided",
                **evidence,
            }
        )
    receipt = {
        "schema": "user_pdf_delivery@1.0",
        "date": "2026-09-07",
        "records": records,
        "main_works_complete": "14/14",
        "supplementary_works_complete": "1/1",
        "missing_fulltexts": [],
        "authority": "local_internal_research_only",
    }
    (ROOT / "user_delivery_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    items = json.loads((ROOT / "sources.json").read_text())
    for item in items:
        if item["id"] in {"R02", "R04"}:
            item["version"] = "用户提供2024出版者全文；2026-09-07从桌面重命名移入；非本助手联网下载"
            item["acquisition"] = "user_provided"
    (ROOT / "sources.json").write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    subprocess.run([sys.executable, str(ROOT / "audit_archive.py"), "--accept-visual"], check=True)
    append_csv(
        LIB / "_source_migration_audit.csv",
        [
            {
                "源文件": r["source"],
                "字节数": r["bytes"],
                "SHA256": r["sha256"],
                "处置": "moved_renamed_user_provided_fulltext",
                "目标或说明": r["target"],
            }
            for r in records
        ],
        "源文件",
    )
    page = records[0]
    append_csv(
        LIB / "_catalog.csv",
        [
            {
                "分类": ROOT.parent.name,
                "文件": page["target"],
                "题名": page["title"],
                "类型": "PDF",
                "页数": 16,
                "内容简介": "Page (1954) CUSUM原始论文，100–115页。",
                "版本与验真": "用户提供完整扫描副本；首页视觉、作者、页数及移动前后SHA核验；内部研究。",
                "来源链接": "https://doi.org/" + page["doi"],
                "SHA256": page["sha256"],
            }
        ],
        "文件",
    )
    # Refresh only the explicitly edited historical source record's catalog binding.
    old = ROOT.parent / "volatility_three_state_router_methods_20260828/page_1954_source_record.md"
    with (LIB / "_catalog.csv").open(encoding="utf-8-sig", newline="") as handle:
        catalog = list(csv.DictReader(handle))
    for row in catalog:
        if row["文件"] == str(old.relative_to(LIB)):
            row["SHA256"] = digest(old)
            row["内容简介"] = "保留官方访问受限历史；现已有用户提供16页全文，链接至风险门控专题。"
            row["版本与验真"] = "2026-09-07用户补齐；全文题名、作者、页数及哈希通过。"
            append_csv(LIB / "_catalog.csv", [row], "文件")
    sums = LIB / "SHA256SUMS"
    prior = dict(line.split("  ", 1)[::-1] for line in sums.read_text().splitlines() if line.strip())
    scoped = [f for f in ROOT.iterdir() if f.is_file()]
    scoped += [old, LIB / "_catalog.csv", LIB / "_source_migration_audit.csv"]
    for path in scoped:
        prior[str(path.relative_to(LIB))] = digest(path)
    sums.write_text("".join(f"{value}  {key}\n" for key, value in prior.items()))
    print("PASS: 3 matching PDFs moved without byte changes; 14 main + 1 supplementary fulltexts complete")


if __name__ == "__main__":
    main()
