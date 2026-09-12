import base64
import json
import tempfile
import unittest
from pathlib import Path

from recorder import ReceptionRecorder, AppendOnlyJsonl, validate_pair, SCHEMA
from validate_capture import validate


class SeqClock:
    def __init__(self, vals):
        self.vals = iter(vals)
    def __call__(self):
        return next(self.vals)


class RecorderTests(unittest.TestCase):
    def make(self, wall=None, mono=None, **kwargs):
        return ReceptionRecorder(
            source="vendorA",
            channel="index",
            recorder_instance_id="inst",
            wall_clock_ns=SeqClock(wall or [1_700_000_000_000_000_000, 1_700_000_000_100_000_000]),
            monotonic_ns=SeqClock(mono or [100, 200]),
            **kwargs,
        )

    def test_stamp_records_raw_hash_and_clocks(self):
        r = self.make()
        s = r.stamp(b"abc")
        self.assertEqual(s.local_sequence, 1)
        self.assertEqual(s.receive_monotonic_ns, 200)
        self.assertEqual(s.raw_payload_sha256, __import__("hashlib").sha256(b"abc").hexdigest())
        self.assertEqual(base64.b64decode(s.raw_payload_b64), b"abc")
        self.assertFalse(s.production_authority)

    def test_sequence_increments(self):
        r = ReceptionRecorder(source="x", recorder_instance_id="i",
            wall_clock_ns=SeqClock([10, 11, 12]), monotonic_ns=SeqClock([20, 21, 22]))
        a, b = r.stamp(b"a"), r.stamp(b"b")
        self.assertEqual((a.local_sequence, b.local_sequence), (1, 2))

    def test_wallclock_regression_is_recorded_not_rejected(self):
        r = ReceptionRecorder(source="x", recorder_instance_id="i",
            wall_clock_ns=SeqClock([1000, 900, 800]), monotonic_ns=SeqClock([100, 200, 300]))
        a, b = r.stamp(b"a"), r.stamp(b"b")
        self.assertLess(b.receive_wallclock_utc_ns, a.receive_wallclock_utc_ns)
        self.assertGreater(b.receive_monotonic_ns, a.receive_monotonic_ns)

    def test_parse_does_not_change_stamp(self):
        r = self.make(); s = r.stamp(b"x")
        p = r.parsed(s, symbol="000688.SH", trading_day="2025-01-02",
            market_event_time_raw="09:30:00", market_event_time_normalized="2025-01-02T09:30:00+08:00",
            market_event_timezone="Asia/Shanghai", event_time_parse_status="PARSED", price=1000.0, source_sequence=5)
        validate_pair(s, p); self.assertEqual(p.receipt_id, s.receipt_id)

    def test_invalid_symbol_rejected(self):
        r = self.make(); s = r.stamp(b"x")
        with self.assertRaises(ValueError):
            r.parsed(s, symbol="000001.SZ", trading_day=None, market_event_time_raw=None,
                market_event_time_normalized=None, market_event_timezone=None, event_time_parse_status="UNPARSED", price=None)

    def test_parsed_requires_timezone(self):
        r = self.make(); s = r.stamp(b"x")
        with self.assertRaises(ValueError):
            r.parsed(s, symbol="000688.SH", trading_day="2025-01-02", market_event_time_raw="09:30:00",
                market_event_time_normalized="2025-01-02T09:30:00+08:00", market_event_timezone=None,
                event_time_parse_status="PARSED", price=1)

    def test_invalid_event_time_can_be_preserved(self):
        r = self.make(); s = r.stamp(b"x")
        p = r.parsed(s, symbol=None, trading_day=None, market_event_time_raw="garbage",
            market_event_time_normalized=None, market_event_timezone=None, event_time_parse_status="INVALID",
            price=None, parse_error="bad timestamp")
        validate_pair(s, p); self.assertEqual(p.event_time_parse_status, "INVALID")

    def test_cross_instance_join_rejected(self):
        a = self.make()
        b = ReceptionRecorder(source="vendorA", recorder_instance_id="other",
            wall_clock_ns=SeqClock([1,2]), monotonic_ns=SeqClock([1,2]))
        s = a.stamp(b"x")
        with self.assertRaises(ValueError):
            b.parsed(s, symbol=None, trading_day=None, market_event_time_raw=None,
                market_event_time_normalized=None, market_event_timezone=None, event_time_parse_status="UNPARSED", price=None)

    def test_append_jsonl(self):
        r = self.make(); s = r.stamp(b"x")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "r.jsonl"; AppendOnlyJsonl(p).append(s)
            row = json.loads(p.read_text()); self.assertEqual(row["receipt_id"], s.receipt_id)

    def test_validator_accepts_wallclock_regression(self):
        r = ReceptionRecorder(source="x", recorder_instance_id="i",
            wall_clock_ns=SeqClock([1000, 900, 800]), monotonic_ns=SeqClock([100, 200, 300]))
        receipts=[]; parsed=[]
        for raw in (b"a", b"b"):
            s=r.stamp(raw); receipts.append(s.__dict__)
            p=r.parsed(s, symbol="000688.SH", trading_day="2025-01-02", market_event_time_raw="09:30:00",
                market_event_time_normalized="2025-01-02T09:30:00+08:00", market_event_timezone="Asia/Shanghai",
                event_time_parse_status="PARSED", price=1.0); parsed.append(p.__dict__)
        self.assertTrue(validate(receipts,parsed)["passed"])

    def test_validator_rejects_monotonic_regression(self):
        receipts=[
            {"schema":SCHEMA,"recorder_version":"prospective_reception_recorder_v1","recorder_instance_id":"i","receipt_id":"i:1","local_sequence":1,"receive_wallclock_utc_ns":1,"receive_monotonic_ns":5,"raw_payload_b64":None,"raw_payload_sha256":"x","raw_payload_size":0},
            {"schema":SCHEMA,"recorder_version":"prospective_reception_recorder_v1","recorder_instance_id":"i","receipt_id":"i:2","local_sequence":2,"receive_wallclock_utc_ns":2,"receive_monotonic_ns":4,"raw_payload_b64":None,"raw_payload_sha256":"x","raw_payload_size":0},
        ]
        out=validate(receipts,[]); self.assertFalse(out["passed"])
        self.assertTrue(any("monotonic clock regressed" in e for e in out["errors"]))

    def test_validator_rejects_noncontiguous_sequence(self):
        r=self.make(); s=r.stamp(b"x").__dict__.copy(); s["local_sequence"]=2
        self.assertFalse(validate([s],[])["passed"])

    def test_raw_payload_can_be_omitted_but_hash_remains(self):
        r=self.make(retain_raw_payload=False); s=r.stamp(b"secret")
        self.assertIsNone(s.raw_payload_b64); self.assertEqual(s.raw_payload_size, 6); self.assertEqual(len(s.raw_payload_sha256),64)

    def test_required_source(self):
        with self.assertRaises(ValueError): ReceptionRecorder(source="  ")

    def test_negative_clock_rejected(self):
        r=ReceptionRecorder(source="x",recorder_instance_id="i",wall_clock_ns=SeqClock([1,-1]),monotonic_ns=SeqClock([1,2]))
        with self.assertRaises(ValueError): r.stamp(b"x")

    def test_non_bytes_payload_rejected(self):
        r=self.make()
        with self.assertRaises(TypeError): r.stamp("x")

    def test_price_must_be_positive(self):
        r=self.make(); s=r.stamp(b"x")
        with self.assertRaises(ValueError):
            r.parsed(s,symbol="000688.SH",trading_day=None,market_event_time_raw=None,market_event_time_normalized=None,
                market_event_timezone=None,event_time_parse_status="UNPARSED",price=0)

    def test_pair_rejects_identity_mismatch(self):
        r=self.make(); s=r.stamp(b"x")
        p=r.parsed(s,symbol=None,trading_day=None,market_event_time_raw=None,market_event_time_normalized=None,
            market_event_timezone=None,event_time_parse_status="UNPARSED",price=None)
        bad=type(p)(**{**p.__dict__,"receipt_id":"other"})
        with self.assertRaises(ValueError): validate_pair(s,bad)

if __name__ == "__main__": unittest.main()
