"""Validate this archive and mechanically append scoped library metadata."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

from acquire import inspect

ROOT = Path(__file__).resolve().parent
LIB = ROOT.parent.parent
PROJECT = LIB.parent
NAME = "从“滤波”转向“风险分桶”：跨频段突发波动的事前门控研究.md"
SOURCE = Path("/home/starryocean/桌面") / NAME
TEMP = PROJECT / "tmp/pdfs/causal_risk_gate_archive_20260907"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def append_csv(path, additions, key):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    updates = {row[key]: row for row in additions}
    present = {row[key] for row in rows}
    merged = [updates.get(row[key], row) for row in rows]
    merged.extend(row for row in additions if row[key] not in present)
    if merged != rows:
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(merged)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--accept-visual", action="store_true")
    args = parser.parse_args()
    items = json.loads((ROOT / "sources.json").read_text())
    assert SOURCE.read_bytes() == (ROOT / NAME).read_bytes(), "source changed"
    used = set(re.findall(r"turn\d+(?:view|search)\d+", (ROOT / NAME).read_text()))
    mapped = {token for item in items for token in item["tokens"]}
    assert used == mapped, (used - mapped, mapped - used)
    records, images = [], []
    TEMP.mkdir(parents=True, exist_ok=True)
    for item in items:
        path = ROOT / item.get("existing", item["file"])
        row = {"id": item["id"], "title": item["title"], "status": "missing"}
        if path.exists():
            row.update(inspect(path.read_bytes()), status="fulltext", path=str(path.relative_to(ROOT)))
            if args.render:
                prefix = TEMP / item["id"]
                subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-scale-to", "950", "-png", str(path), str(prefix)], check=True)
                images.append(str(prefix.with_suffix(".png")))
            first = subprocess.check_output(["pdftotext", "-f", "1", "-l", "3", str(path), "-"], text=True)
            row["first_three_pages_text_sha256"] = hashlib.sha256(first.encode()).hexdigest()
        records.append(row)
    if images:
        for i in range(0, len(images), 4):
            subprocess.run(
                ["montage", *images[i : i + 4], "-tile", "2x2", "-geometry", "+10+10", str(TEMP / f"sheet_{i // 4 + 1}.png")], check=True
            )
    report = {
        "schema": "literature_archive_audit@1.0",
        "source_sha256": digest(SOURCE),
        "source_copy_identical": True,
        "original_citation_tokens": sorted(used),
        "citation_mapping_basis": "author/content reconstruction; original URLs absent; bipower version ambiguous",
        "fulltext_count": sum(r["status"] == "fulltext" for r in records),
        "missing_ids": [r["id"] for r in records if r["status"] == "missing"],
        "visual_review_accepted": args.accept_visual,
        "records": records,
        "duplicate_same_hash_ids": ["R01", "R08"],
        "existing_library_reuse": ["R14"],
        "production_authority": False,
    }
    (ROOT / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if not args.accept_visual:
        print(json.dumps({"fulltexts": report["fulltext_count"], "missing": report["missing_ids"], "render_dir": str(TEMP)}))
        return
    category = ROOT.parent.name
    additions = []
    for item, record in zip(items, records, strict=True):
        if record["status"] != "fulltext" or "existing" in item:
            continue
        path = ROOT / item["file"]
        additions.append(
            {
                "分类": category,
                "文件": str(path.relative_to(LIB)),
                "题名": item["title"],
                "类型": "PDF",
                "页数": record["pages"],
                "内容简介": "跨频段突发风险门控综述来源，参见专题目录与来源映射。",
                "版本与验真": item["version"] + "；PDF解析、全文文本提取、首页视觉与题名核验。",
                "来源链接": item["urls"][0],
                "SHA256": digest(path),
            }
        )
    for file, title, kind in [
        (NAME, NAME[:-3], "项目研究综述"),
        ("README.md", "跨频段突发波动事前门控文献包", "专题目录"),
        ("sources.json", "风险门控14项文献来源映射", "元数据"),
        ("missing_fulltexts.md", "风险门控文献全文缺口", "书目记录"),
    ]:
        path = ROOT / file
        additions.append(
            {
                "分类": category,
                "文件": str(path.relative_to(LIB)),
                "题名": title,
                "类型": kind,
                "页数": "",
                "内容简介": f"{report['fulltext_count']}项主要文献全文可读，{len(report['missing_ids'])}项未取得；补充文献见专题目录。",
                "版本与验真": "原文逐字节复制；文献归档不授策略权限。",
                "来源链接": "",
                "SHA256": digest(path),
            }
        )
    append_csv(LIB / "_catalog.csv", additions, "文件")
    append_csv(
        LIB / "_source_migration_audit.csv",
        [
            {
                "源文件": "桌面/" + NAME,
                "字节数": SOURCE.stat().st_size,
                "SHA256": digest(SOURCE),
                "处置": "copied_original_preserved",
                "目标或说明": str((ROOT / NAME).relative_to(LIB)),
            }
        ],
        "源文件",
    )
    # Preserve all prior hash records, update only this task's metadata surfaces.
    sums = LIB / "SHA256SUMS"
    prior = dict(line.split("  ", 1)[::-1] for line in sums.read_text().splitlines() if line.strip())
    scoped = [p for p in ROOT.iterdir() if p.is_file()]
    scoped += [
        LIB / "README.md",
        ROOT.parent / "README.md",
        LIB / "目录（内容简介）.md",
        LIB / "_catalog.csv",
        LIB / "_source_migration_audit.csv",
    ]
    for p in scoped:
        prior[str(p.relative_to(LIB))] = digest(p)
    sums.write_text("".join(f"{value}  {key}\n" for key, value in prior.items()))
    print(
        json.dumps(
            {"accepted": True, "fulltexts": report["fulltext_count"], "missing": report["missing_ids"], "catalog_additions": len(additions)}
        )
    )


if __name__ == "__main__":
    main()
