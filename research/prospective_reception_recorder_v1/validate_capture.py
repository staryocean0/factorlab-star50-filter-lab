"""Validate prospective reception capture JSONL without inferring missing clocks."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SCHEMA = "factorlab_true_reception_capture_v1"
SUPPORTED = {"000688.SH", "000852.SH"}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{lineno}: row must be object")
            rows.append(obj)
    return rows


def validate(receipts: list[dict], parsed: list[dict]) -> dict:
    errors: list[str] = []
    rec_by_id: dict[str, dict] = {}
    seqs = defaultdict(list)
    monos = defaultdict(list)
    for i, r in enumerate(receipts):
        rid = r.get("receipt_id")
        inst = r.get("recorder_instance_id")
        if r.get("schema") != SCHEMA:
            errors.append(f"receipt[{i}] schema")
        if not rid or not inst:
            errors.append(f"receipt[{i}] missing identity")
            continue
        if rid in rec_by_id:
            errors.append(f"duplicate receipt_id {rid}")
        rec_by_id[rid] = r
        seqs[inst].append(r.get("local_sequence"))
        monos[inst].append(r.get("receive_monotonic_ns"))
        if not isinstance(r.get("receive_wallclock_utc_ns"), int):
            errors.append(f"{rid}: missing wall clock ns")
        if not isinstance(r.get("receive_monotonic_ns"), int):
            errors.append(f"{rid}: missing monotonic ns")
        raw_b64 = r.get("raw_payload_b64")
        if raw_b64 is not None:
            try:
                raw = base64.b64decode(raw_b64, validate=True)
            except Exception:
                errors.append(f"{rid}: invalid base64")
            else:
                if hashlib.sha256(raw).hexdigest() != r.get("raw_payload_sha256"):
                    errors.append(f"{rid}: raw payload hash mismatch")
                if len(raw) != r.get("raw_payload_size"):
                    errors.append(f"{rid}: raw payload size mismatch")
    for inst, values in seqs.items():
        if any(not isinstance(x, int) for x in values):
            errors.append(f"{inst}: non-integer local_sequence")
        elif values != list(range(1, len(values) + 1)):
            errors.append(f"{inst}: local_sequence not contiguous from 1")
    for inst, values in monos.items():
        if all(isinstance(x, int) for x in values):
            if any(b < a for a, b in zip(values, values[1:])):
                errors.append(f"{inst}: monotonic clock regressed")
    # Wall clock is deliberately NOT required to be monotonic; NTP/system clock may move.
    parsed_ids = set()
    for i, p in enumerate(parsed):
        rid = p.get("receipt_id")
        if rid in parsed_ids:
            errors.append(f"duplicate parsed receipt {rid}")
        parsed_ids.add(rid)
        r = rec_by_id.get(rid)
        if r is None:
            errors.append(f"parsed[{i}] missing receipt {rid}")
            continue
        for key in ("schema", "recorder_version", "recorder_instance_id", "local_sequence"):
            if p.get(key) != r.get(key):
                errors.append(f"{rid}: parsed {key} mismatch")
        sym = p.get("symbol")
        if sym is not None and sym not in SUPPORTED:
            errors.append(f"{rid}: unsupported symbol {sym}")
        status = p.get("event_time_parse_status")
        if status not in {"PARSED", "UNPARSED", "INVALID"}:
            errors.append(f"{rid}: bad parse status")
        if status == "PARSED":
            if not p.get("market_event_time_normalized") or not p.get("market_event_timezone"):
                errors.append(f"{rid}: parsed event time lacks normalized/timezone")
        elif p.get("market_event_time_normalized") is not None:
            errors.append(f"{rid}: non-parsed event has normalized time")
    return {
        "schema": "factorlab_true_reception_capture_validation_v1",
        "receipt_rows": len(receipts),
        "parsed_rows": len(parsed),
        "unparsed_receipts": len(receipts) - len(parsed_ids),
        "recorder_instances": len(seqs),
        "errors": errors,
        "passed": not errors,
        "wallclock_monotonicity_required": False,
        "production_authority": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipts", required=True)
    ap.add_argument("--parsed", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    result = validate(load_jsonl(Path(args.receipts)), load_jsonl(Path(args.parsed)))
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
