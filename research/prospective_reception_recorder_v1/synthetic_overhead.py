#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from recorder import ReceptionRecorder
from datahub_adapter import CaptureBuffer, ReceptionAwareQuotesParser, TdxReceptionHqTap


class Sink:
    def __init__(self):
        self.count = 0
    def append(self, record):
        self.count += 1


class FakeHq:
    def get_security_quotes(self, symbols, market, *, endpoint=None, connection=None):
        return [{"code": s.split(".")[0], "price": 1000.0 + i, "sequence_no": i + 1} for i, s in enumerate(symbols)]


class FakeParser:
    def parse_quotes(self, payload):
        return [{"symbol": row["code"] + ".SH", "last_price": row["price"], "sequence_no": row.get("sequence_no")} for row in payload]


def pct(values, p):
    data = sorted(values)
    return data[min(len(data) - 1, max(0, int(round((len(data) - 1) * p))))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=2000)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    symbols = ["000688.SH", "000852.SH"]
    hq, parser = FakeHq(), FakeParser()

    baseline = []
    for _ in range(args.iterations):
        t0 = time.perf_counter_ns()
        payload = hq.get_security_quotes(symbols, "cn_index")
        parser.parse_quotes(payload)
        baseline.append(time.perf_counter_ns() - t0)

    receipts, parsed = Sink(), Sink()
    buffer = CaptureBuffer()
    recorder = ReceptionRecorder(source="tdx_hq_sdk_return", channel="cn_index", retain_raw_payload=False)
    wrapped_hq = TdxReceptionHqTap(hq, recorder=recorder, capture_buffer=buffer, receipt_sink=receipts)
    wrapped_parser = ReceptionAwareQuotesParser(parser, recorder=recorder, capture_buffer=buffer, parsed_sink=parsed)
    wrapped = []
    for _ in range(args.iterations):
        t0 = time.perf_counter_ns()
        payload = wrapped_hq.get_security_quotes(symbols, "cn_index")
        wrapped_parser.parse_quotes(payload)
        wrapped.append(time.perf_counter_ns() - t0)

    expected = args.iterations * len(symbols)
    if receipts.count != expected or parsed.count != expected or buffer.pending_batches() != 0:
        raise AssertionError("synthetic wrapper accounting mismatch")
    result = {
        "schema": "datahub_reception_synthetic_overhead_v1",
        "interpretation": "synthetic GitHub-runner wrapper overhead only; not feed/network/production latency",
        "iterations": args.iterations,
        "quotes_per_iteration": len(symbols),
        "baseline_ns": {"median": int(statistics.median(baseline)), "p95": int(pct(baseline, 0.95)), "p99": int(pct(baseline, 0.99))},
        "wrapped_ns": {"median": int(statistics.median(wrapped)), "p95": int(pct(wrapped, 0.95)), "p99": int(pct(wrapped, 0.99))},
        "incremental_ns": {
            "median": int(statistics.median(wrapped) - statistics.median(baseline)),
            "p95": int(pct(wrapped, 0.95) - pct(baseline, 0.95)),
            "p99": int(pct(wrapped, 0.99) - pct(baseline, 0.99)),
        },
        "receipt_records": receipts.count,
        "parsed_records": parsed.count,
        "pending_batches": buffer.pending_batches(),
        "gate": "descriptive_only_no_production_threshold",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
