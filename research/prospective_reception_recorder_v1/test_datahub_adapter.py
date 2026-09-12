import unittest
from datetime import datetime, timezone

from recorder import ReceptionRecorder
from datahub_adapter import (
    CaptureBuffer,
    ReceptionAwareQuotesParser,
    TdxReceptionHqTap,
    canonical_symbol,
    canonicalize_sdk_quote,
)


class ListSink:
    def __init__(self): self.items=[]
    def append(self, item): self.items.append(item)


class SeqClock:
    def __init__(self, values): self.values=iter(values)
    def __call__(self): return next(self.values)


class FakeHq:
    def __init__(self, payload): self.payload=payload; self.calls=[]
    def get_security_quotes(self, symbols, market, *, endpoint=None, connection=None):
        self.calls.append((list(symbols), market, endpoint, connection))
        return self.payload


class FakeParser:
    def __init__(self, *, fail=False, shorten=False): self.fail=fail; self.shorten=shorten
    def parse_quotes(self, payload):
        if self.fail: raise ValueError("boom")
        rows=[]
        for item in payload:
            rows.append({"symbol": item.get("code"), "last_price": item.get("price"), "trading_day":"2025-06-11", "timestamp":"2099-01-01T00:00:00+00:00"})
        return rows[:-1] if self.shorten else rows


class DataHubAdapterTests(unittest.TestCase):
    def make_stack(self, payload, parser=None):
        receipts=ListSink(); parsed=ListSink(); buffer=CaptureBuffer()
        rec=ReceptionRecorder(source="tdx_hq_sdk_return", channel="TdxHqApiAdapter.get_security_quotes",
            recorder_instance_id="test-instance", wall_clock_ns=SeqClock([100,110,120,130,140]), monotonic_ns=SeqClock([1000,1010,1020,1030,1040]), retain_raw_payload=True)
        hq=TdxReceptionHqTap(FakeHq(payload), recorder=rec, capture_buffer=buffer, receipt_sink=receipts)
        qp=ReceptionAwareQuotesParser(parser or FakeParser(), recorder=rec, capture_buffer=buffer, parsed_sink=parsed)
        return rec,hq,qp,receipts,parsed,buffer

    def test_canonical_json_is_key_order_stable(self):
        a=canonicalize_sdk_quote({"price":1.2,"code":"000688"})
        b=canonicalize_sdk_quote({"code":"000688","price":1.2})
        self.assertEqual(a,b)

    def test_canonical_handles_bytes_datetime_tuple(self):
        b=canonicalize_sdk_quote({"x":b"a", "d":datetime(2025,1,1,tzinfo=timezone.utc), "t":(1,2)})
        self.assertIn(b"__bytes_b64__",b); self.assertIn(b"__datetime__",b)

    def test_canonical_rejects_unsupported_object(self):
        with self.assertRaises(TypeError): canonicalize_sdk_quote({"x":object()})

    def test_symbol_exact(self): self.assertEqual(canonical_symbol({"symbol":"000688.SH"},["000688.SH"]),"000688.SH")
    def test_symbol_base_maps_requested(self): self.assertEqual(canonical_symbol({"code":"000688"},["000688.SH"]),"000688.SH")
    def test_symbol_missing_is_none(self): self.assertIsNone(canonical_symbol({},["000688.SH"]))
    def test_symbol_ambiguous_is_none(self): self.assertIsNone(canonical_symbol({"code":"000688"},["000688.SH","000688.SZ"]))

    def test_hq_tap_preserves_return_object_and_stamps_each_row(self):
        payload=[{"code":"000688","price":100.0},{"code":"000852","price":200.0}]
        _,hq,_,receipts,_,buffer=self.make_stack(payload)
        out=hq.get_security_quotes(["000688.SH","000852.SH"],"cn_a",endpoint=("x",7709))
        self.assertIs(out,payload); self.assertEqual(len(receipts.items),2); self.assertEqual(buffer.pending_batches(),1)
        self.assertEqual(receipts.items[0].local_sequence,1); self.assertEqual(receipts.items[1].local_sequence,2)
        self.assertLess(receipts.items[0].receive_monotonic_ns,receipts.items[1].receive_monotonic_ns)

    def test_payload_hash_matches_canonical_sdk_object(self):
        payload=[{"code":"000688","price":100.0}]
        _,hq,_,receipts,_,_=self.make_stack(payload)
        hq.get_security_quotes(["000688.SH"],"cn_a")
        import hashlib
        self.assertEqual(receipts.items[0].raw_payload_sha256,hashlib.sha256(canonicalize_sdk_quote(payload[0])).hexdigest())

    def test_parser_returns_delegate_output_unchanged(self):
        payload=[{"code":"000688","price":100.0}]
        _,hq,qp,_,parsed,_=self.make_stack(payload)
        hq.get_security_quotes(["000688.SH"],"cn_a")
        out=qp.parse_quotes(payload)
        self.assertEqual(out[0]["last_price"],100.0); self.assertEqual(len(parsed.items),1)

    def test_parser_does_not_promote_datahub_parse_timestamp_to_market_event(self):
        payload=[{"code":"000688","price":100.0}]
        _,hq,qp,_,parsed,_=self.make_stack(payload)
        hq.get_security_quotes(["000688.SH"],"cn_a"); qp.parse_quotes(payload)
        row=parsed.items[0]
        self.assertEqual(row.event_time_parse_status,"UNPARSED")
        self.assertIsNone(row.market_event_time_normalized)
        self.assertIsNone(row.market_event_timezone)

    def test_parser_preserves_uncontracted_raw_event_candidate_without_normalizing(self):
        payload=[{"code":"000688","price":100.0,"event_time":"09:45:00"}]
        _,hq,qp,_,parsed,_=self.make_stack(payload)
        hq.get_security_quotes(["000688.SH"],"cn_a"); qp.parse_quotes(payload)
        self.assertEqual(parsed.items[0].market_event_time_raw,"09:45:00")
        self.assertEqual(parsed.items[0].event_time_parse_status,"UNPARSED")

    def test_source_sequence_preserved_when_present(self):
        payload=[{"code":"000688","price":100.0,"seq":123}]
        _,hq,qp,_,parsed,_=self.make_stack(payload)
        hq.get_security_quotes(["000688.SH"],"cn_a"); qp.parse_quotes(payload)
        self.assertEqual(parsed.items[0].source_sequence,"123")

    def test_price_preserved(self):
        payload=[{"code":"000688","price":100.25}]
        _,hq,qp,_,parsed,_=self.make_stack(payload)
        hq.get_security_quotes(["000688.SH"],"cn_a"); qp.parse_quotes(payload)
        self.assertEqual(parsed.items[0].price,100.25)

    def test_capture_buffer_rejects_parser_without_capture(self):
        b=CaptureBuffer()
        with self.assertRaisesRegex(RuntimeError,"no captured"): b.pop_for([])

    def test_capture_buffer_rejects_mutated_payload(self):
        payload=[{"code":"000688","price":100.0}]
        _,hq,qp,_,_,_=self.make_stack(payload)
        hq.get_security_quotes(["000688.SH"],"cn_a"); payload[0]["price"]=101.0
        with self.assertRaisesRegex(RuntimeError,"payload mismatch"): qp.parse_quotes(payload)

    def test_delegate_parser_failure_still_emits_failure_receipt(self):
        payload=[{"code":"000688","price":100.0}]
        _,hq,qp,_,parsed,_=self.make_stack(payload,FakeParser(fail=True))
        hq.get_security_quotes(["000688.SH"],"cn_a")
        with self.assertRaises(ValueError): qp.parse_quotes(payload)
        self.assertEqual(len(parsed.items),1); self.assertIn("delegate_parser_error",parsed.items[0].parse_error)

    def test_cardinality_change_rejected_and_logged(self):
        payload=[{"code":"000688","price":100.0},{"code":"000852","price":200.0}]
        _,hq,qp,_,parsed,_=self.make_stack(payload,FakeParser(shorten=True))
        hq.get_security_quotes(["000688.SH","000852.SH"],"cn_a")
        with self.assertRaisesRegex(RuntimeError,"cardinality"): qp.parse_quotes(payload)
        self.assertEqual(len(parsed.items),2)

    def test_empty_payload_roundtrip(self):
        payload=[]
        _,hq,qp,receipts,parsed,buffer=self.make_stack(payload)
        out=hq.get_security_quotes(["000688.SH"],"cn_a"); self.assertEqual(out,[])
        self.assertEqual(qp.parse_quotes(out),[]); self.assertEqual(receipts.items,[]); self.assertEqual(parsed.items,[]); self.assertEqual(buffer.pending_batches(),0)

    def test_non_list_hq_result_rejected(self):
        _,hq,_,_,_,_=self.make_stack([])
        hq._delegate.payload={"code":"000688"}
        with self.assertRaises(TypeError): hq.get_security_quotes(["000688.SH"],"cn_a")

    def test_non_mapping_hq_item_rejected(self):
        _,hq,_,_,_,_=self.make_stack([])
        hq._delegate.payload=[1]
        with self.assertRaises(TypeError): hq.get_security_quotes(["000688.SH"],"cn_a")

    def test_two_batches_fifo(self):
        payload=[{"code":"000688","price":100.0}]
        _,hq,qp,receipts,parsed,buffer=self.make_stack(payload)
        hq.get_security_quotes(["000688.SH"],"cn_a")
        hq.get_security_quotes(["000688.SH"],"cn_a")
        self.assertEqual(buffer.pending_batches(),2)
        qp.parse_quotes(payload); qp.parse_quotes(payload)
        self.assertEqual(buffer.pending_batches(),0); self.assertEqual(len(receipts.items),2); self.assertEqual(len(parsed.items),2)

    def test_receipt_is_before_parser_by_design_clock_sequence(self):
        payload=[{"code":"000688","price":100.0}]
        _,hq,qp,receipts,parsed,_=self.make_stack(payload)
        hq.get_security_quotes(["000688.SH"],"cn_a"); stamp=receipts.items[0]
        qp.parse_quotes(payload); self.assertEqual(parsed.items[0].receipt_id,stamp.receipt_id)

if __name__ == "__main__": unittest.main()
