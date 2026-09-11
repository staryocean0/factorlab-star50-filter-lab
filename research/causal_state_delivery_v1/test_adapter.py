from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import unittest

from adapter import emit_e15, visible_at, STATES, V9_BLOB

T = datetime(2025, 3, 10, 10, 5, tzinfo=timezone(timedelta(hours=8)))


def inputs(**changes):
    out = dict(symbol="000688.SH", bar_end=T, published_at=T-timedelta(seconds=15),
               previous_bar_end=T-timedelta(minutes=5),
               previous_state_known_at=T-timedelta(minutes=5), previous_state="NORMAL",
               partial_state="UNSAFE", observation_time=T-timedelta(seconds=15),
               observation_known_at=T-timedelta(seconds=15), reference_chain_valid=True,
               checkpoint_available=True, source_runner_blob=V9_BLOB,
               timing_basis="owner_realtime_assumption")
    out.update(changes)
    return out


class DeliveryContractTests(unittest.TestCase):
    def test_nine_frozen_state_combinations(self):
        expected = {
            ("NORMAL", "NORMAL"): "NORMAL", ("NORMAL", "UNSAFE"): "UNSAFE",
            ("NORMAL", "RECOVERING"): "RECOVERING",
            ("UNSAFE", "NORMAL"): "UNSAFE", ("UNSAFE", "UNSAFE"): "UNSAFE",
            ("UNSAFE", "RECOVERING"): "RECOVERING",
            ("RECOVERING", "NORMAL"): "RECOVERING",
            ("RECOVERING", "UNSAFE"): "UNSAFE",
            ("RECOVERING", "RECOVERING"): "RECOVERING",
        }
        for prev in STATES:
            for part in STATES:
                with self.subTest(prev=prev, part=part):
                    self.assertEqual(emit_e15(**inputs(previous_state=prev,
                                                      partial_state=part)).state,
                                     expected[(prev, part)])

    def test_exit_is_pending_not_safe(self):
        x = emit_e15(**inputs(previous_state="RECOVERING", partial_state="NORMAL"))
        self.assertTrue(x.exit_pending)
        self.assertEqual(x.bucket_key, "RECOVERING|PRIOR_CONFIRMED_EXIT_PENDING")
        self.assertEqual(x.partial_state, "NORMAL")

    def test_explicit_state_change(self):
        x = emit_e15(**inputs(previous_state="RECOVERING"))
        self.assertEqual(x.transition, "RECOVERING->UNSAFE")
        self.assertFalse(x.exit_pending)

    def test_unknown_is_not_normal(self):
        for key in ("checkpoint_available", "reference_chain_valid"):
            with self.subTest(key=key):
                x = emit_e15(**inputs(**{key: False}))
                self.assertIsNone(x.state)
                self.assertIsNone(x.partial_state)
                self.assertEqual(x.bucket_key, "UNAVAILABLE")

    def test_missing_fields_fail_closed(self):
        for key in ("previous_state", "partial_state", "previous_bar_end",
                    "previous_state_known_at", "observation_time", "observation_known_at"):
            with self.subTest(key=key):
                self.assertIsNone(emit_e15(**inputs(**{key: None})).state)

    def test_future_inputs_are_unavailable(self):
        for key in ("previous_state_known_at", "observation_known_at"):
            with self.subTest(key=key):
                x = emit_e15(**inputs(**{key: T-timedelta(seconds=14)}))
                self.assertEqual(x.availability_reason, "INPUT_NOT_KNOWN_BY_DECISION")
                self.assertIsNone(x.state)

    def test_future_event_cannot_be_used(self):
        x = emit_e15(**inputs(observation_time=T-timedelta(seconds=3),
                             observation_known_at=T-timedelta(seconds=3)))
        self.assertIsNone(x.state)

    def test_current_final_label_not_accepted(self):
        with self.assertRaises(TypeError):
            emit_e15(**inputs(final_state="NORMAL"))

    def test_future_path_not_accepted(self):
        with self.assertRaises(TypeError):
            emit_e15(**inputs(future_return=1.0))

    def test_historical_available_at_not_accepted(self):
        with self.assertRaises(TypeError):
            emit_e15(**inputs(available_at=T+timedelta(hours=5)))

    def test_publication_not_backdated(self):
        x = emit_e15(**inputs(published_at=T-timedelta(seconds=10)))
        self.assertIsNone(visible_at(x, T-timedelta(seconds=12)))
        self.assertEqual(visible_at(x, T-timedelta(seconds=10)), x)
        with self.assertRaises(ValueError):
            emit_e15(**inputs(published_at=T-timedelta(seconds=16)))

    def test_snapshot_expires_at_close(self):
        x = emit_e15(**inputs())
        self.assertIsNone(visible_at(x, T))
        self.assertIsNone(visible_at(x, T+timedelta(minutes=5)))

    def test_immutable_no_repaint(self):
        x = emit_e15(**inputs())
        before = x.as_dict()
        with self.assertRaises(FrozenInstanceError):
            x.state = "NORMAL"
        emit_e15(**inputs(partial_state="NORMAL"))
        self.assertEqual(x.as_dict(), before)

    def test_invalid_timestamp_order_rejected(self):
        cases = [dict(previous_bar_end=T-timedelta(seconds=1)),
                 dict(previous_state_known_at=T-timedelta(minutes=6)),
                 dict(observation_known_at=T-timedelta(seconds=16))]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                emit_e15(**inputs(**changes))

    def test_old_observation_not_carried_forward(self):
        x = emit_e15(**inputs(observation_time=T-timedelta(minutes=6)))
        self.assertEqual(x.availability_reason, "OBSERVATION_OUTSIDE_CURRENT_BAR")

    def test_naive_times_rejected(self):
        for key in ("bar_end", "published_at", "previous_bar_end", "observation_time"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                emit_e15(**inputs(**{key: T.replace(tzinfo=None)}))

    def test_symbols_and_identity(self):
        self.assertEqual(emit_e15(**inputs(symbol="000852.SH")).symbol, "000852.SH")
        for changes in (dict(symbol="588000.SH"), dict(source_runner_blob="wrong")):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                emit_e15(**inputs(**changes))

    def test_no_2026_realtime_authority(self):
        with self.assertRaises(ValueError):
            emit_e15(**inputs(bar_end=T.replace(year=2026)))

    def test_vocabulary_and_flags(self):
        for changes in (dict(partial_state="BUY"), dict(previous_state="HighVol"),
                        dict(checkpoint_available=1), dict(timing_basis="historical_available_at")):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                emit_e15(**inputs(**changes))

    def test_no_probability_or_trading_claim(self):
        out = emit_e15(**inputs()).as_dict()
        self.assertIsNone(out["recovery_probabilities"])
        self.assertFalse(out["production_authority"])
        self.assertFalse({"order", "position", "return", "trade_allowed"} & out.keys())


if __name__ == "__main__":
    unittest.main()
