#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

PROTOCOL_MARKERS = (
    "frozen_protocol", "protocol.md", "protocol.json", "preregistration", "pre_registration", "freeze_receipt",
)
RESULT_MARKERS = (
    "result.md", "results.md", "validation_results.md", "execution_receipt", "decisive_receipt",
    "validation_receipt", "closeout", "program_state.json",
)
RUNNER_MARKERS = ("run_", "runner", ".github/workflows/")


def sh(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def changed_files(ref: str) -> list[str]:
    base = sh("git", "merge-base", "refs/remotes/origin/main", ref)
    text = sh("git", "diff", "--name-only", "--diff-filter=AM", base, ref)
    return [x for x in text.splitlines() if x]


def has_marker(paths: list[str], markers: tuple[str, ...]) -> bool:
    return any(any(m in p.lower() for m in markers) for p in paths)


def branch_runs(repo: str, branch: str, token: str | None) -> dict:
    if not token:
        return {"queried": False}
    q = urllib.parse.urlencode({"branch": branch, "per_page": 100})
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/runs?{q}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    runs = payload.get("workflow_runs", [])
    scientific = [x for x in runs if x.get("path") != ".github/workflows/ci.yml"]
    completed_success = [x for x in scientific if x.get("status") == "completed" and x.get("conclusion") == "success"]
    completed_failed = [x for x in scientific if x.get("status") == "completed" and x.get("conclusion") not in (None, "success", "skipped")]
    return {
        "queried": True,
        "total_runs": len(runs),
        "scientific_runs": len(scientific),
        "scientific_success_runs": len(completed_success),
        "scientific_failed_runs": len(completed_failed),
        "latest_scientific_run_id": scientific[0].get("id") if scientific else None,
        "latest_scientific_conclusion": scientific[0].get("conclusion") if scientific else None,
        "latest_scientific_workflow": scientific[0].get("name") if scientific else None,
    }


def classify(protocol: bool, runner: bool, result: bool, runs: dict) -> str:
    success = int(runs.get("scientific_success_runs", 0))
    if protocol and runner and not result and success:
        return "EXECUTED_RESULT_NOT_PERSISTED"
    if protocol and runner and not result and not success:
        return "FROZEN_NOT_SUCCESSFULLY_EXECUTED"
    if protocol and not runner and not result:
        return "FROZEN_DESIGN_ONLY"
    if protocol and result:
        return "RESULT_PRESENT"
    if runner and not result and success:
        return "EXECUTED_NO_RESULT_MARKER"
    return "OTHER"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    refs = sh("git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/research/").splitlines()
    token = os.getenv("GITHUB_TOKEN")
    rows = []
    for ref in refs:
        if not ref or ref.endswith("/HEAD"):
            continue
        branch = ref.removeprefix("origin/")
        paths = changed_files(ref)
        protocol = has_marker(paths, PROTOCOL_MARKERS)
        runner = has_marker(paths, RUNNER_MARKERS)
        result = has_marker(paths, RESULT_MARKERS)
        runs = branch_runs(args.repo, branch, token)
        row = {
            "branch": branch,
            "head_sha": sh("git", "rev-parse", ref),
            "changed_files": len(paths),
            "protocol_marker": protocol,
            "runner_marker": runner,
            "result_marker": result,
            "protocol_files": [p for p in paths if any(m in p.lower() for m in PROTOCOL_MARKERS)],
            "result_files": [p for p in paths if any(m in p.lower() for m in RESULT_MARKERS)],
            "runner_files": [p for p in paths if any(m in p.lower() for m in RUNNER_MARKERS)],
            "actions": runs,
        }
        row["classification"] = classify(protocol, runner, result, runs)
        rows.append(row)
    priority = {
        "EXECUTED_RESULT_NOT_PERSISTED": 0,
        "FROZEN_NOT_SUCCESSFULLY_EXECUTED": 1,
        "FROZEN_DESIGN_ONLY": 2,
        "EXECUTED_NO_RESULT_MARKER": 3,
        "RESULT_PRESENT": 4,
        "OTHER": 5,
    }
    rows.sort(key=lambda x: (priority[x["classification"]], x["branch"]))
    summary = {}
    for row in rows:
        summary[row["classification"]] = summary.get(row["classification"], 0) + 1
    out = {
        "schema": "research_backlog_audit_v1",
        "research_branches_scanned": len(rows),
        "classification_counts": summary,
        "priority_candidates": [x for x in rows if x["classification"] in {
            "EXECUTED_RESULT_NOT_PERSISTED", "FROZEN_NOT_SUCCESSFULLY_EXECUTED", "FROZEN_DESIGN_ONLY"
        }],
        "branches": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"research_branches_scanned": len(rows), "classification_counts": summary}, indent=2, sort_keys=True))
    for row in out["priority_candidates"]:
        print(row["classification"], row["branch"], "success_runs=", row["actions"].get("scientific_success_runs"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
