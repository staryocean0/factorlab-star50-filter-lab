"""Seal exactly the selected Git index, recording real baseline object reuse."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/handoff/cloud_risk_gate_20260907/package_manifest.json"
BASE = "ce7088688f601595ea5c28554949440f5c2f792e"


def main():
    baseline = {}
    for line in subprocess.check_output(
        ["git", "ls-tree", "-rz", BASE], cwd=ROOT
    ).split(b"\0"):
        if line:
            head, name = line.split(b"\t", 1)
            baseline[name.decode()] = head.split()[2].decode()
    records = []
    for line in subprocess.check_output(
        ["git", "ls-files", "-s", "-z"], cwd=ROOT
    ).split(b"\0"):
        if not line:
            continue
        head, rawname = line.split(b"\t", 1)
        name = rawname.decode()
        path = ROOT / name
        if path == DEST:
            continue
        assert path.is_file(), name
        assert not any(
            part in {".env", "credentials", "__pycache__"} for part in path.parts
        )
        blob = head.split()[1].decode()
        assert (
            subprocess.check_output(
                ["git", "hash-object", "--", name], cwd=ROOT, text=True
            ).strip()
            == blob
        ), f"unstaged drift {name}"
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        records.append(
            {
                "path": name,
                "sha256": digest,
                "bytes": path.stat().st_size,
                "git_blob": blob,
                "transfer": "reuse_remote_object"
                if baseline.get(name) == blob
                else "new_or_changed",
            }
        )
    exclusions = (
        subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT
        )
        .decode()
        .split("\0")
    )
    payload = {
        "schema": "cross_index_risk_gate_cloud_package@1.0",
        "destination": "staryocean0/factorlab-star50-filter-lab",
        "baseline_remote_commit": BASE,
        "default_branch_publication": "fast_forward_only_no_force",
        "private_repository_required": True,
        "local_storage_authoritative": True,
        "files": records,
        "untracked_not_uploaded": [
            x for x in exclusions if x and x != str(DEST.relative_to(ROOT))
        ],
        "excluded_reason": "option/account carrier artifacts and provider troubleshooting stay local; current Kline evidence/code/docs included",
        "new_or_changed_files": sum(x["transfer"] == "new_or_changed" for x in records),
        "reused_remote_files": sum(
            x["transfer"] == "reuse_remote_object" for x in records
        ),
        "new_or_changed_bytes": sum(
            x["bytes"] for x in records if x["transfer"] == "new_or_changed"
        ),
        "fresh_oos": False,
        "production_authority": False,
    }
    DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in payload.items()
                if k not in {"files", "untracked_not_uploaded"}
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
