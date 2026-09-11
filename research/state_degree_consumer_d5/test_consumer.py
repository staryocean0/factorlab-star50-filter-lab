"""Synthetic interface tests, not evidence of live deployment or economics."""
import copy
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import unittest

from consumer import (ATTRIBUTE_FIELDS, BLOBS, EVENT_FIELDS, OUTPUT_FIELDS, TZ,
                      ResearchConsumer, aware, build_snapshot, expected_expiry)


def fixture(kind="E15", end="2024-01-02T10:00:00+08:00", state="RECOVERING"):
    end = aware(end)
    d = end-timedelta(seconds=15) if kind == "E15" else end
    e = dict(schema="causal_kline_delivery_d2_v1", symbol="000688.SH", bar_end=end.isoformat(),
             decision_time=d.isoformat(), published_at=d.isoformat(), valid_until=expected_expiry(end, kind).isoformat(),
             event_id=f"000688.SH|{end.isoformat()}|{kind}", event_type=kind, state=state,
             partial_state=state if kind == "E15" else None, previous_confirmed_state="UNSAFE",
             state_basis="E15_PROVISIONAL" if kind == "E15" else "CLOSE_CONFIRMED",
             transition="UNSAFE_TO_RECOVERING", exit_pending=False, availability_reason="AVAILABLE",
             observation_time=d.isoformat(), observation_known_at=d.isoformat(), shock=False,
             shock_intensity=1.2, vol_ratio=1.3, recent_shock_age_bars=4,
             age_clock="5m_bar_steps_within_trading_day", recovery_probabilities=[.04, .1, .8], recovery_reason="scored",
             probability_target_clock="frozen_V16_horizon_labels_at_reference_bar_end", production_authority=False,
             timing_basis="owner_realtime_assumption", **BLOBS)
    e["bucket_key"] = state+"|"+e["state_basis"]
    a = {k: str(e[k]) for k in ("symbol", "state", "state_basis", "availability_reason", "shock_intensity", "vol_ratio")}
    for k in ("bar_end", "decision_time", "published_at", "valid_until", "observation_time"):
        a[k] = aware(e[k]).replace(tzinfo=None).isoformat(sep=" ")
    a.update(available="True", lag_intensity="1.0", lag_ratio="1.0", delta_intensity="0.2", delta_ratio="0.3", numeric_bucket="I_QHIGH|V_QHIGH")
    return e, a


def missing():
    e, a = fixture()
    for k in ("state", "partial_state", "previous_confirmed_state", "shock", "shock_intensity", "vol_ratio", "recovery_probabilities"):
        e[k] = None
    e.update(availability_reason="REFERENCE_UNAVAILABLE", state_basis="UNAVAILABLE", bucket_key="UNAVAILABLE", transition="UNAVAILABLE", recovery_reason="missing_reference_or_checkpoint")
    for k in ("state", "shock_intensity", "vol_ratio", "lag_intensity", "lag_ratio", "delta_intensity", "delta_ratio"):
        a[k] = ""
    a.update(available="False", availability_reason="REFERENCE_UNAVAILABLE", state_basis="UNAVAILABLE", numeric_bucket="UNAVAILABLE")
    return e, a


class ConsumerTests(unittest.TestCase):
    def packet(self, kind="E15", **kwargs):
        e, a = fixture(kind, **kwargs)
        return build_snapshot(e, a if kind == "E15" else None)

    def test_all_nine_frozen_state_combinations(self):
        for prev in ("NORMAL", "UNSAFE", "RECOVERING"):
            for part in ("NORMAL", "UNSAFE", "RECOVERING"):
                with self.subTest(prev=prev, part=part):
                    e, a = fixture(); state = part if part != "NORMAL" else prev
                    pending = part == "NORMAL" and prev != "NORMAL"
                    basis = "PRIOR_CONFIRMED_EXIT_PENDING" if pending else "E15_PROVISIONAL"
                    e.update(previous_confirmed_state=prev, partial_state=part, state=state, exit_pending=pending,
                             state_basis=basis, bucket_key=state+"|"+basis, recovery_probabilities=None, recovery_reason="provisional_normal")
                    a.update(state=state, state_basis=basis)
                    s=build_snapshot(e,a).as_dict(); self.assertEqual(s["state"],state); self.assertEqual(s["exit_pending"],pending)

    def test_complete_schema_and_numeric_join(self):
        e,a=fixture(); s=build_snapshot(e,a).as_dict()
        self.assertEqual(set(e),EVENT_FIELDS); self.assertEqual(set(a),ATTRIBUTE_FIELDS); self.assertEqual(set(s),OUTPUT_FIELDS)
        self.assertEqual(s['lag_intensity'],1.0)

    def test_close_has_no_e15_enrichment(self):
        e,a=fixture("CLOSE")
        with self.assertRaises(ValueError):build_snapshot(e,a)
        s=build_snapshot(e).as_dict(); self.assertIsNone(s['lag_ratio']); self.assertEqual(s['delta_status'],'NOT_DEFINED_FOR_CLOSE')

    def test_future_label_columns_rejected(self):
        for k in ('final_state','future_tail','episode_end','pnl','trade_allowed','buy','available_at'):
            e,a=fixture(); e[k]=1
            with self.subTest(k=k), self.assertRaises(ValueError):build_snapshot(e,a)

    def test_extra_attribute_column_rejected(self):
        e,a=fixture();a['future_return']=0
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_missing_column_rejected(self):
        e,a=fixture();e.pop('vol_ratio')
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_frozen_versions_rejected(self):
        for k in BLOBS:
            e,a=fixture();e[k]='0'*40
            with self.subTest(k=k),self.assertRaises(ValueError):build_snapshot(e,a)

    def test_schema_rejected(self):
        e,a=fixture();e['schema']='v20'
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_cross_symbol_join_rejected(self):
        e,a=fixture();a['symbol']='000852.SH'
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_future_observation_rejected(self):
        e,a=fixture();e['observation_known_at']=e['bar_end']
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_current_final_observation_rejected(self):
        e,a=fixture();e['observation_time']=e['bar_end']
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_naive_source_time_rejected(self):
        e,a=fixture();e['decision_time']=a['decision_time']
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_csv_timezone_rejected(self):
        e,a=fixture()
        with self.assertRaises(ValueError):build_snapshot(e,a,csv_timezone='UTC')

    def test_consumer_timezone_normalization(self):
        s=self.packet();c=ResearchConsumer();c.ingest(s,received_at=s.published)
        self.assertEqual(c.as_of(s.symbol,s.published),c.as_of(s.symbol,s.published.astimezone(timezone.utc)))
        with self.assertRaises(ValueError):c.as_of(s.symbol,s.published.replace(tzinfo=None))

    def test_backdated_publication_rejected(self):
        e,a=fixture();e['published_at']=(aware(e['decision_time'])-timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_expiry_cannot_be_extended(self):
        e,a=fixture();e['valid_until']=(aware(e['bar_end'])+timedelta(hours=1)).isoformat()
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_delayed_receipt_not_backfilled(self):
        s=self.packet();c=ResearchConsumer();c.ingest(s,received_at=s.published+timedelta(seconds=3))
        self.assertIsNone(c.as_of(s.symbol,s.published)['snapshot'])
        self.assertEqual(c.as_of(s.symbol,s.published+timedelta(seconds=3))['status'],'AVAILABLE')

    def test_receipt_before_publication_rejected(self):
        s=self.packet()
        with self.assertRaises(ValueError):ResearchConsumer().ingest(s,received_at=s.published-timedelta(microseconds=1))

    def test_exact_duplicate_idempotent(self):
        s=self.packet();c=ResearchConsumer();self.assertTrue(c.ingest(s,received_at=s.published))
        self.assertFalse(c.ingest(s,received_at=s.published+timedelta(seconds=1)))
        self.assertEqual(c.as_of(s.symbol,s.published)['consumer_received_at'],s.published.isoformat())

    def test_conflicting_duplicate_rejected(self):
        e,a=fixture();s=build_snapshot(e,a);c=ResearchConsumer();c.ingest(s,received_at=s.published)
        e['shock_intensity']=1.4;a.update(shock_intensity='1.4',delta_intensity='0.4')
        with self.assertRaises(ValueError):c.ingest(build_snapshot(e,a),received_at=s.published)

    def test_missing_enrichment_and_late_patch(self):
        e,a=fixture();s=build_snapshot(e);c=ResearchConsumer();c.ingest(s,received_at=s.published)
        v=c.as_of(s.symbol,s.published);self.assertEqual(v['status'],'STATE_ONLY');self.assertIsNone(v['snapshot']['shock_intensity'])
        with self.assertRaises(ValueError):c.ingest(build_snapshot(e,a),received_at=s.published+timedelta(seconds=1))

    def test_unavailable_is_not_normal(self):
        e,a=missing();s=build_snapshot(e,a);c=ResearchConsumer();c.ingest(s,received_at=s.published)
        v=c.as_of(s.symbol,s.published);self.assertEqual(v['status'],'UNAVAILABLE');self.assertIsNone(v['snapshot']['state'])

    def test_unavailable_numeric_leak_rejected(self):
        e,a=missing();a['lag_ratio']='0.0'
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_nonfinite_and_bool_rejected(self):
        for v in ('nan','inf',True):
            e,a=fixture();a['lag_ratio']=v
            with self.subTest(v=v),self.assertRaises(ValueError):build_snapshot(e,a)

    def test_numeric_mismatch_rejected(self):
        e,a=fixture();a['shock_intensity']='2'
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_delta_mismatch_rejected(self):
        e,a=fixture();a['delta_ratio']='3'
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_quantile_gate_never_delivered(self):
        e,a=fixture();a['numeric_bucket']='BUY_AFTER_SEEING_FUTURE'
        s=build_snapshot(e,a).as_dict();self.assertNotIn('numeric_bucket',s);self.assertNotIn('BUY_AFTER_SEEING_FUTURE',str(s))

    def test_immutable_snapshot_and_deep_copy(self):
        s=self.packet();c=ResearchConsumer();c.ingest(s,received_at=s.published)
        with self.assertRaises(FrozenInstanceError):s.payload='mutated'
        v=c.as_of(s.symbol,s.published);v['snapshot']['state']='NORMAL';v['snapshot']['recovery_probabilities'][0]=1
        self.assertEqual(c.as_of(s.symbol,s.published)['snapshot']['recovery_probabilities'][0],.04)

    def test_mutating_input_cannot_rewrite_snapshot(self):
        e,a=fixture();s=build_snapshot(e,a);e['recovery_probabilities'][0]=1;a['delta_ratio']='99'
        self.assertEqual(s.as_dict()['delta_ratio'],.3);self.assertEqual(s.as_dict()['recovery_probabilities'][0],.04)

    def test_expired_latest_never_falls_back(self):
        c=ResearchConsumer();old=self.packet('CLOSE',end='2024-01-02T09:55:00+08:00');s=self.packet()
        c.ingest(old,received_at=old.published);c.ingest(s,received_at=s.published)
        self.assertEqual(c.as_of(s.symbol,s.expires)['reason'],'LATEST_EVENT_EXPIRED')

    def test_close_late_gap_and_historical_query(self):
        c=ResearchConsumer();s=self.packet();cl=self.packet('CLOSE');c.ingest(s,received_at=s.published)
        before=c.as_of(s.symbol,s.published);c.ingest(cl,received_at=cl.published+timedelta(seconds=2))
        self.assertEqual(c.as_of(s.symbol,s.expires)['reason'],'LATEST_EVENT_EXPIRED')
        self.assertEqual(c.as_of(s.symbol,s.published),before)
        self.assertEqual(c.as_of(s.symbol,cl.published+timedelta(seconds=2))['snapshot']['event_type'],'CLOSE')

    def test_out_of_order_receipt_rejected(self):
        c=ResearchConsumer();s=self.packet();cl=self.packet('CLOSE');c.ingest(s,received_at=cl.published+timedelta(seconds=2))
        with self.assertRaises(ValueError):c.ingest(cl,received_at=cl.published)

    def test_out_of_order_source_rejected(self):
        c=ResearchConsumer();s=self.packet();cl=self.packet('CLOSE');c.ingest(cl,received_at=cl.published)
        with self.assertRaises(ValueError):c.ingest(s,received_at=cl.published)

    def test_lunch_and_afternoon_context(self):
        s=self.packet('CLOSE',end='2024-01-02T11:30:00+08:00');c=ResearchConsumer();c.ingest(s,received_at=s.published)
        self.assertEqual(c.as_of(s.symbol,'2024-01-02T12:00:00+08:00')['reason'],'SESSION_CLOSED')
        self.assertEqual(c.as_of(s.symbol,'2024-01-02T13:00:00+08:00')['snapshot']['event_id'],s.event_id)

    def test_day_end_and_overnight(self):
        s=self.packet('CLOSE',end='2024-01-02T15:00:00+08:00');c=ResearchConsumer();c.ingest(s,received_at=s.published)
        self.assertEqual(c.as_of(s.symbol,s.published)['status'],'AVAILABLE')
        self.assertIsNone(c.as_of(s.symbol,s.expires)['snapshot']);self.assertIsNone(c.as_of(s.symbol,'2024-01-03T09:31:00+08:00')['snapshot'])

    def test_invalid_recovery_curve_rejected(self):
        e,a=fixture();e['recovery_probabilities']=[.8,.2,.9]
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_missing_probability_stays_none(self):
        e,a=fixture();e.update(recovery_probabilities=None,recovery_reason='fresh_partial_shock')
        self.assertIsNone(build_snapshot(e,a).as_dict()['recovery_probabilities'])

    def test_out_of_scope_and_no_production(self):
        e,a=fixture();e['production_authority']=True
        with self.assertRaises(ValueError):build_snapshot(e,a)
        e,a=fixture(end='2026-01-02T10:00:00+08:00')
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_wrong_event_key_rejected(self):
        e,a=fixture();e['event_id']+='OTHER'
        with self.assertRaises(ValueError):build_snapshot(e,a)

    def test_partial_normal_does_not_close_risk(self):
        e,a=fixture();e.update(partial_state='NORMAL',state='NORMAL',state_basis='E15_PROVISIONAL')
        with self.assertRaises(ValueError):build_snapshot(e,a)


if __name__ == '__main__':
    unittest.main()
