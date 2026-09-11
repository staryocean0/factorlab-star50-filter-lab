import unittest
import numpy as np
import pandas as pd
from run_d3 import history, causal_table, labels, design, fit_probe, predict, block_stats, uncertainty, SLOTS, STATES, HORIZONS


def fixture():
    rows=[]; events=[]
    for symbol in ('000688.SH','000852.SH'):
        for day in pd.bdate_range('2021-01-04',periods=5):
            for i,m in enumerate(SLOTS):
                e=day+pd.Timedelta(minutes=m)
                value=100*np.exp(.001*np.sin(len(rows)*.4)+.00002*len(rows))
                rows.append({'symbol':symbol,'bar_end':e,'trading_day':str(day.date()),'close':value})
                d={'symbol':symbol,'bar_end':e,'event_type':'E15','decision_time':e-pd.Timedelta(seconds=15),'published_at':e-pd.Timedelta(seconds=15),
                   'valid_until':e,'observation_time':e-pd.Timedelta(seconds=18),'state':'NORMAL','previous_confirmed_state':'NORMAL',
                   'availability_reason':'AVAILABLE','shock_intensity':.7,'vol_ratio':1.0,'exit_pending':False,'recent_shock_age_bars':4,
                   'recovery_probabilities':None,'transition':'HOLD_NORMAL'}
                events.append(d)
                c=dict(d); c['event_type']='CLOSE'; c['decision_time']=e; c['published_at']=e
                events.append(c)
    p=history(pd.DataFrame(rows)); ev=pd.DataFrame(events); q=causal_table(p,ev,(2021,))
    return p,ev,q


class D3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.p,cls.ev,cls.q=fixture()
    def valid(self,h=15):
        x=labels(self.p,self.q,h,self.ev[self.ev.event_type=='CLOSE'])
        return x[x.available&x.label_ok].reset_index(drop=True)
    def test_future_price_cannot_change_history_prefix(self):
        raw=self.p[['symbol','bar_end','trading_day','close']].copy(); j=150
        raw.loc[j:,'close']*=1.12
        changed=history(raw)
        for c in ('bg48','rms3','rms6','rms12','rms48','last_abs'):
            np.testing.assert_array_equal(changed.loc[:j,c],self.p.loc[:j,c])
    def test_no_overnight_return(self):
        self.assertTrue(self.p.groupby(['symbol','trading_day']).head(1).r.isna().all())
    def test_bg_uses_only_predecision_returns(self):
        j=150; prev=self.p.loc[:j-1,'r'].dropna().tail(48)
        self.assertAlmostEqual(self.p.at[j,'bg48'],prev.std(ddof=0),places=14)
    def test_rms_uses_only_previous_returns(self):
        j=150
        for k in (3,6,12,48):
            x=self.p.loc[:j-1,'r'].dropna().tail(k)
            self.assertAlmostEqual(self.p.at[j,f'rms{k}'],np.sqrt(np.mean(x**2)),places=14)
    def test_complete_future_window(self):
        x=self.valid(); r=x.iloc[0]; j=int(r.price_idx)
        self.assertAlmostEqual(r.sigma,float(np.sqrt(np.mean(self.p.r.iloc[j+1:j+4]**2))),places=14)
        self.assertGreater(r.label_start,r.decision_time)
    def test_excludes_current_return(self):
        p=self.p.copy(); r=self.valid().iloc[0]; j=int(r.price_idx); p.loc[j,'r']=1000
        x=labels(p,self.q,15,self.ev[self.ev.event_type=='CLOSE'])
        self.assertEqual(x.loc[x.price_idx==j,'sigma'].iloc[0],r.sigma)
    def test_lunch_is_not_a_complete_window(self):
        x=labels(self.p,self.q,15,self.ev[self.ev.event_type=='CLOSE'])
        self.assertFalse(x[x.slot==685].label_ok.any())
    def test_day_end_not_zero_risk(self):
        x=labels(self.p,self.q,15,self.ev[self.ev.event_type=='CLOSE'])
        e=x[x.slot==900]
        self.assertFalse(e.label_ok.any()); self.assertTrue(e.future_tail.isna().all())
    def test_60m_future_horizon(self):
        x=self.valid(60)
        self.assertTrue((x.label_end-x.label_start==pd.Timedelta(minutes=60)).all())
    def test_design_ignores_current_close_and_evaluator(self):
        x=self.valid(); before=design(x,'B4')[0]; altered=x.copy()
        for c in ('close','r','future_tail','log_future_sigma','future_risk_fraction'): altered[c]=1e15
        np.testing.assert_array_equal(before,design(altered,'B4')[0])
    def test_design_schema_fixed_across_slices(self):
        x=self.valid()
        for m in ('B0','B1','B2','B3','B4'): self.assertEqual(design(x,m)[1],design(x.iloc[:1],m)[1])
    def test_nested_comparators(self):
        x=self.valid()
        self.assertTrue(set(design(x,'B1')[1])<set(design(x,'B2')[1]))
        self.assertTrue(set(design(x,'B3')[1])<set(design(x,'B4')[1]))
    def test_frozen_probabilities_are_features_with_mask(self):
        x=self.valid().iloc[:1].copy(); x.at[0,'recovery_probabilities']=[.1,.2,.6]
        a,n=design(x,'B2'); self.assertEqual(a[0,n.index('frozen_p30')],.2)
        self.assertEqual(a[0,n.index('recovery_available')],1)
    def test_missing_probability_not_claimed_scored(self):
        x=self.valid(); a,n=design(x,'B2')
        self.assertTrue((a[:,n.index('recovery_available')]==0).all())
    def test_nonfinite_input_refused(self):
        x=self.valid().copy(); x['bg48']=np.nan
        with self.assertRaises(ValueError): design(x,'B1')
    def test_fixed_ridge_is_deterministic(self):
        x=self.valid(); a,n=design(x,'B2'); y=x.log_future_sigma.to_numpy()
        self.assertEqual(fit_probe(a,y,n),fit_probe(a,y,n))
    def test_binary_prediction_is_bounded(self):
        x=self.valid(); a,n=design(x,'B2'); f=fit_probe(a,np.zeros(len(x)),n); f['intercept']=3
        p=predict(x,'B2',f,'future_tail'); self.assertTrue((p==1).all())
    def test_bootstrap_preserves_same_day_both_symbols(self):
        x=self.valid(); b=block_stats(x,np.ones(len(x)),5)
        self.assertEqual(int(b.n.sum()),len(x)); self.assertEqual(float(b.gain.sum()),len(x))
    def test_bootstrap_constant_gain(self):
        x=self.valid(); ci=uncertainty(block_stats(x,np.ones(len(x))*.03,5))
        self.assertAlmostEqual(ci['adjusted_low'],.03); self.assertAlmostEqual(ci['adjusted_high'],.03)
    def test_bootstrap_reproducible(self):
        x=self.valid(); b=block_stats(x,np.sin(np.arange(len(x))),5)
        self.assertEqual(uncertainty(b),uncertainty(b))
    def test_prepublication_not_usable(self):
        ev=self.ev.copy(); ev.loc[ev.event_type=='E15','published_at']+=pd.Timedelta(seconds=1)
        self.assertFalse(causal_table(self.p,ev,(2021,)).available.any())
    def test_future_observation_not_usable(self):
        ev=self.ev.copy(); ev.loc[ev.event_type=='E15','observation_time']+=pd.Timedelta(minutes=1)
        self.assertFalse(causal_table(self.p,ev,(2021,)).available.any())
    def test_role_filter_excludes_validation(self):
        x=causal_table(self.p,self.ev,(2024,2025)); self.assertEqual(len(x),0)
    def test_slot_and_horizon_contract(self):
        self.assertEqual(len(SLOTS),48); self.assertEqual(HORIZONS,(15,30,60)); self.assertEqual(len(STATES),3)

if __name__=='__main__': unittest.main()
