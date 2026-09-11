import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta
from engine import Kernel, Ledger, Snapshot, TZ, RISK, STATES, transition, next_bar, bucket

T = datetime(2024,1,2,10,0,tzinfo=TZ)
SURFACE={(s,b):(.1,.3,.8) for s in RISK for b in ('LT15','M15_25','M30_40','GE45')}

def kernel():
    k=Kernel('000688.SH',SURFACE)
    k.day=T.date(); k.prev_close=100.; k.previous_end=T-timedelta(minutes=5)
    k.previous_known=k.previous_end; k.position=4
    k.returns.extend([.001,-.001]*24)
    return k

def preview(k=None, **kw):
    k=k or kernel()
    d=dict(bar_end=T,price=100.,observation_time=T-timedelta(seconds=15));d.update(kw)
    return k.e15(**d)

class Tests(unittest.TestCase):
    def test_frozen_transition_table(self):
        for p in STATES:
            for r in (.9,1.2,1.6):
                with self.subTest(prev=p,ratio=r):
                    exp='NORMAL' if p=='NORMAL' or r<=1.1 else 'UNSAFE' if r>=1.5 else 'RECOVERING'
                    self.assertEqual(transition(p,r,False),exp)
                    self.assertEqual(transition(p,r,True),'UNSAFE')
    def test_all_nine_delivery_state_combinations(self):
        for prev in STATES:
            for partial in STATES:
                k=kernel();k.state=prev
                if partial=='UNSAFE': k.measures=lambda p:(1.,4.,True)
                elif partial=='RECOVERING':
                    if prev=='NORMAL': continue  # Not reachable under frozen V9.
                    k.measures=lambda p:(1.2,1.,False)
                else:k.measures=lambda p:(.9,1.,False)
                e=preview(k)
                self.assertEqual(e.state,partial if partial in RISK else prev if prev in RISK else 'NORMAL')
    def test_confirmed_exit(self):
        k=kernel();k.state='UNSAFE';k.last_shock=0
        k.measures=lambda p:(.9,.2,False)
        e=preview(k);c=k.close(bar_end=T,price=100.)
        self.assertTrue(e.exit_pending);self.assertEqual(e.state,'UNSAFE')
        self.assertIsNone(e.recovery_probabilities);self.assertEqual(c.state,'NORMAL')
    def test_recovery_and_reescalation(self):
        k=kernel();k.state='UNSAFE';k.last_shock=0;k.measures=lambda p:(1.2,1.,False)
        self.assertEqual(preview(k).partial_state,'RECOVERING')
        k.state='RECOVERING';k.measures=lambda p:(1.6,1.,False)
        self.assertEqual(preview(k).transition,'REESCALATE')
    def test_probabilities_frozen_gates(self):
        k=kernel();k.state='UNSAFE';k.last_shock=0;k.measures=lambda p:(1.6,1.,False)
        e=preview(k);self.assertEqual(e.recovery_probabilities,(.1,.3,.8));self.assertEqual(e.recent_shock_age_bars,5)
        k.last_shock=None;self.assertEqual(preview(k).recovery_reason,'no_prior_finalized_shock')
    def test_partial_shock_does_not_reset_confirmed_clock(self):
        k=kernel();k.last_shock=0;k.measures=lambda p:(1.5,4.,True)
        e=preview(k);self.assertEqual(e.recovery_reason,'fresh_partial_shock');self.assertEqual(k.last_shock,0)
        c=k.close(bar_end=T,price=101.);self.assertEqual(c.recent_shock_age_bars,0)
        self.assertEqual(c.recovery_reason,'fresh_final_shock')
    def test_missing_checkpoint(self):
        e=preview(price=None,observation_time=None);self.assertIsNone(e.state);self.assertIsNone(e.previous_confirmed_state)
    def test_missing_reference(self):
        k=kernel();k.prev_close=None;self.assertIsNone(preview(k).state)
    def test_zero_background(self):
        k=kernel();k.returns.clear();k.returns.extend([0.]*48);self.assertIsNone(preview(k).state)
    def test_late_input(self):
        e=preview(observation_known_at=T-timedelta(seconds=14));self.assertIsNone(e.state)
        self.assertEqual(e.availability_reason,'INPUT_NOT_KNOWN_BY_DECISION')
    def test_future_observation(self):self.assertIsNone(preview(observation_time=T).state)
    def test_bad_observation_clock(self):
        with self.assertRaises(ValueError):preview(observation_known_at=T-timedelta(seconds=16))
    def test_inclusive_start_matches_v9(self):self.assertIsNotNone(preview(observation_time=T-timedelta(minutes=5)).state)
    def test_before_start(self):self.assertIsNone(preview(observation_time=T-timedelta(minutes=5,seconds=1)).state)
    def test_reject_e15_final_label(self):
        with self.assertRaises(TypeError):preview(final_state='UNSAFE')
    def test_reject_future_path(self):
        with self.assertRaises(TypeError):preview(future_return=1.)
    def test_naive_clock(self):
        with self.assertRaises(ValueError):preview(bar_end=T.replace(tzinfo=None))
    def test_backdated_publication(self):
        with self.assertRaises(ValueError):preview(published_at=T-timedelta(seconds=16))
    def test_future_scope(self):
        with self.assertRaises(ValueError):preview(bar_end=T.replace(year=2026))
    def test_bad_price(self):
        for p in (0.,-1.,float('nan'),float('inf')):
            with self.assertRaises(ValueError):preview(price=p)
    def test_bad_symbol(self):
        with self.assertRaises(ValueError):Kernel('BAD',SURFACE)
    def test_snapshot_immutable(self):
        e=preview()
        with self.assertRaises(FrozenInstanceError):e.state='UNSAFE'
    def test_asof_and_expiry(self):
        e=preview();l=Ledger();l.append(e)
        self.assertIsNone(l.as_of(e.symbol,e.published_at-timedelta(microseconds=1)))
        self.assertEqual(l.as_of(e.symbol,e.published_at),e);self.assertIsNone(l.as_of(e.symbol,T))
    def test_close_visibility(self):
        k=kernel();e=preview(k);c=k.close(bar_end=T,price=100.);l=Ledger();l.append(e);l.append(c)
        self.assertEqual(l.as_of(e.symbol,T-timedelta(microseconds=1)),e);self.assertEqual(l.as_of(e.symbol,T),c)
    def test_delayed_close_no_backfill(self):
        k=kernel();e=preview(k);c=k.close(bar_end=T,price=100.,known_at=T+timedelta(seconds=2))
        l=Ledger();l.append(e);l.append(c)
        self.assertIsNone(l.as_of(e.symbol,T+timedelta(seconds=1)));self.assertEqual(l.as_of(e.symbol,c.published_at),c)
    def test_late_e15_at_close_never_visible(self):
        e=preview(published_at=T);l=Ledger();l.append(e);self.assertIsNone(l.as_of(e.symbol,T))
    def test_duplicate_idempotent(self):
        l=Ledger();e=preview();l.append(e);d=l.digest;self.assertFalse(l.append(e));self.assertEqual(d,l.digest)
    def test_conflicting_duplicate(self):
        l=Ledger();e=preview();l.append(e)
        with self.assertRaises(ValueError):l.append(replace(e,state='UNSAFE'))
    def test_out_of_order(self):
        l=Ledger();e=preview();l.append(e)
        with self.assertRaises(ValueError):l.append(replace(e,event_type='CLOSE',published_at=e.published_at-timedelta(seconds=1)))
    def test_gap_fail_closed(self):
        with self.assertRaises(ValueError):preview(bar_end=T+timedelta(minutes=5))
    def test_lunch_context_not_new_observation(self):
        k=kernel();k.previous_end=T.replace(hour=11,minute=30);k.previous_known=k.previous_end
        k.position=23;k.last_shock=10;k.state='UNSAFE';k.measures=lambda p:(1.6,1.,False)
        end=T.replace(hour=13,minute=5)
        e=preview(k,bar_end=end,observation_time=end-timedelta(seconds=15));self.assertEqual(e.recent_shock_age_bars,14)
    def test_break_asof_unavailable(self):
        l=Ledger();e=preview();l.append(replace(e,valid_until=T.replace(hour=14)))
        self.assertIsNone(l.as_of(e.symbol,T.replace(hour=12)))
    def test_day_reset_and_no_overnight(self):
        k=kernel();k.state='UNSAFE';k.last_shock=0
        end=T.replace(day=3,hour=9,minute=35)
        e=preview(k,bar_end=end,observation_time=end-timedelta(seconds=15));self.assertIsNone(e.state)
        self.assertIsNone(k.last_shock);self.assertEqual(k.state,'NORMAL');self.assertEqual(len(k.returns),48)
    def test_late_prior_reference_not_visible(self):
        k=kernel();k.previous_known=T;self.assertEqual(preview(k).availability_reason,'REFERENCE_NOT_KNOWN')
    def test_close_cannot_precede_close(self):
        with self.assertRaises(ValueError):kernel().close(bar_end=T,price=100.,known_at=T-timedelta(seconds=1))
    def test_future_close_changes_do_not_revise_prefix(self):
        a=kernel();b=kernel();ea=preview(a);eb=preview(b)
        a.close(bar_end=T,price=99.);b.close(bar_end=T,price=110.)
        self.assertEqual(ea,eb);self.assertEqual(ea,preview(kernel()))
    def test_no_strategy_or_hindsight_fields(self):
        d=preview().record()
        for f in ('final_state','future_return','episode_end','trade_allowed','direction','position','pnl'):
            self.assertNotIn(f,d)
        self.assertFalse(d['production_authority'])
    def test_age_bucket_boundaries(self):
        self.assertEqual([bucket(x) for x in (1,2,3,5,6,8,9)],['LT15','LT15','M15_25','M15_25','M30_40','M30_40','GE45'])

if __name__=='__main__':unittest.main()
