#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

TERMS = {
    "row_count_349923": re.compile(r"349[,_ ]?923", re.I),
    "v0615": re.compile(r"v?0\.6\.15|v0615|0615", re.I),
    "leg_universe": re.compile(r"leg[-_ ]?universe|published[-_ ]?leg|strict[-_ ]?pair", re.I),
    "source_identity": re.compile(r"expected[-_ ]?source[-_ ]?(sha|hash)|source[-_ ]?(sha256|identity|hash)", re.I),
    "identity_manifest": re.compile(r"expected[-_ ]?(sha|hash)|identity[-_ ]?(receipt|manifest)|frozen[-_ ]?identity", re.I),
    "sha256_literal": re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", re.I),
}
MAX_BLOB = 5_000_000


def sh(*args: str, check: bool = True) -> str:
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError(f"{' '.join(args)}\n{p.stderr}")
    return p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", required=True, help="strict pre-v0.6.17 boundary; use instant before first v0.6.17 commit")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()

    commits = [x for x in sh("git", "rev-list", "--all", f"--before={a.cutoff}").splitlines() if x]
    if not commits:
        raise RuntimeError("no commits before cutoff")

    # Restrict object traversal to the exact pre-cutoff commit set rather than --all,
    # because later v0.6.17 blobs must never become their own 'prior identity' evidence.
    objects = sh("git", "rev-list", "--objects", *commits).splitlines()
    blobs: dict[str, set[str]] = {}
    for line in objects:
        parts = line.split(" ", 1)
        oid = parts[0]
        path = parts[1] if len(parts) > 1 else ""
        if not path:
            continue
        if sh("git", "cat-file", "-t", oid, check=False).strip() != "blob":
            continue
        size_txt = sh("git", "cat-file", "-s", oid, check=False).strip()
        if not size_txt or int(size_txt) > MAX_BLOB:
            continue
        blobs.setdefault(oid, set()).add(path)

    hits = []
    source_candidates = []
    leg_candidates = []
    for oid, paths in blobs.items():
        raw = subprocess.check_output(["git", "cat-file", "blob", oid])
        if b"\x00" in raw[:8192]:
            continue
        text = raw.decode("utf-8", "replace")
        found = []
        snippets = []
        for name, rx in TERMS.items():
            m = rx.search(text)
            if m:
                found.append(name)
                line = text.count("\n", 0, m.start()) + 1
                lo = max(0, m.start() - 120)
                hi = min(len(text), m.end() + 180)
                snippets.append({"term": name, "line": line, "snippet": text[lo:hi].replace("\n", " ")[:360]})
        if not found:
            continue
        path = sorted(paths)[0]
        history = sh(
            "git", "log", "--all", f"--before={a.cutoff}", "--format=%H|%cI|%s",
            f"--find-object={oid}", "--", path, check=False,
        ).splitlines()
        item = {
            "blob": oid,
            "paths": sorted(paths),
            "terms": sorted(set(found)),
            "snippets": snippets,
            "history": history[:10],
        }
        hits.append(item)
        ts = set(found)
        # Source receipt must itself bind the exact 349,923-row surface to an explicit SHA-256 value.
        if {"row_count_349923", "source_identity", "sha256_literal"}.issubset(ts):
            source_candidates.append(item)
        # Leg-universe receipt must itself identify v0.6.15/frozen leg overlays and an explicit SHA-256 value.
        if {"v0615", "leg_universe", "sha256_literal"}.issubset(ts):
            leg_candidates.append(item)

    recovered = bool(source_candidates and leg_candidates)
    out = {
        "schema": "v0617_prior_identity_audit_v2",
        "cutoff": a.cutoff,
        "cutoff_semantics": "strictly before the first v0.6.17 implementation commit",
        "commits_scanned": len(commits),
        "text_blobs_scanned": len(blobs),
        "hits": hits,
        "authoritative_source_candidates": source_candidates,
        "v0615_leg_universe_candidates": leg_candidates,
        "required_precommit_identity_recovered": recovered,
        "decision_if_false": "V0617_PRIOR_IDENTITY_IRRECOVERABLE_REPLAY_PERMANENTLY_BLOCKED_UNDER_FROZEN_PROTOCOL",
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "commits_scanned": len(commits),
        "text_blobs_scanned": len(blobs),
        "hit_blobs": len(hits),
        "authoritative_source_candidates": len(source_candidates),
        "v0615_leg_universe_candidates": len(leg_candidates),
        "required_precommit_identity_recovered": recovered,
    }, indent=2))
    for label, arr in (("SOURCE", source_candidates), ("LEGS", leg_candidates)):
        for h in arr:
            print(label, h["blob"], h["paths"], h["terms"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
