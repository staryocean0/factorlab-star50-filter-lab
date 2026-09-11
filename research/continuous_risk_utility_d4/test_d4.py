"""Synthetic D4 tests: causality, comparator parity, encodings and inference."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'causal_state_utility_d3'))
from test_d3 import fixture
from run_d4 import history, table, design, predict, quantile_fit, quantile_keys, interval, d3, MODELS, PROTOCOL_COMMIT


class D4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p, cls.ev, _ = fixture()
        cls.raw = p[['symbol','trading_day','bar_end','close']]
        cls.p = history(cls.raw)
        cls.q = table(cls.p, cls.ev, (2021,))
        rows = d3.labels(cls.p, cls.q, 15, cls.ev[cls.ev.event_type.eq('CLOSE')])
        cls.z = rows[rows.available & rows.label_ok].reset_index(drop=True)

    def test_lag_std_is_last_twelve_confirmed(self):
        r = self.z.iloc[20]
        v = self.p[(self.p.symbol==r.symbol)&(self.p.bar_end<r.bar_end)].r.dropna().tail(12)
        self.assertAlmostEqual(r.lag_ratio, v.std(ddof=0)/r.bg48, places=10)

    def test_lag_intensity_is_previous_confirmed(self):
        r = self.z.iloc[20]
        v = self.p[(self.p.symbol==r.symbol)&(self.p.bar_end<r.bar_end)].r.dropna().iloc[-1]
        self.assertAlmostEqual(r.lag_intensity, abs(v)/r.bg48, places=12)

    def test_future_close_perturbation_preserves_history_prefix(self):
        raw = self.raw.copy(); j=150
        raw.loc[j:, 'close'] *= 1.07
        changed = history(raw)
        for col in ('lag_std12','bg48','last_abs','rms3','rms6','rms12','rms48'):
            np.testing.assert_array_equal(self.p.loc[:j,col], changed.loc[:j,col])

    def test_no_overnight_return(self):
        self.assertTrue(self.p.groupby(['symbol','trading_day']).head(1).r.isna().all())

    def test_original_available_cohort_is_preserved(self):
        old = d3.causal_table(self.p, self.ev, (2021,))
        np.testing.assert_array_equal(old.available, self.q.available)

    def test_lag_ignores_current_numeric_observations(self):
        z = self.z.copy(); before = design(z,'L')[0]
        z['shock_intensity'] = 900.; z['vol_ratio'] = 900.
        np.testing.assert_array_equal(before,design(z,'L')[0])

    def test_current_probe_responds_to_partial_information(self):
        z=self.z.copy(); before=design(z,'C')[0]
        z['shock_intensity'] = 9.
        self.assertFalse(np.array_equal(before,design(z,'C')[0]))

    def test_history_probe_is_original_B1(self):
        np.testing.assert_array_equal(design(self.z,'H')[0],d3.design(self.z,'B1')[0])

    def test_current_probe_is_original_B3(self):
        np.testing.assert_array_equal(design(self.z,'C')[0],d3.design(self.z,'B3')[0])

    def test_equal_complexity_and_column_schema(self):
        self.assertEqual(design(self.z,'L')[1], design(self.z,'C')[1])
        self.assertEqual(design(self.z,'L')[0].shape, design(self.z,'C')[0].shape)

    def test_equal_values_equal_design(self):
        z=self.z.copy(); z['lag_intensity']=z.shock_intensity; z['lag_ratio']=z.vol_ratio
        np.testing.assert_array_equal(design(z,'L')[0],design(z,'C')[0])

    def test_all_designs_ignore_evaluation_columns(self):
        z=self.z.copy()
        for col in ('close','r','future_tail','log_future_sigma','future_risk_fraction','future_any_normal'):
            z[col]=1e9
        for m in MODELS:
            np.testing.assert_array_equal(design(self.z,m)[0],design(z,m)[0])

    def test_validation_cannot_fit_quantiles(self):
        z=self.z.copy(); z['year']=2024
        with self.assertRaises(ValueError): quantile_fit(z)

    def test_quantiles_ignore_future_outcomes(self):
        b=quantile_fit(self.q); z=self.q.copy(); z['future_tail']=1e7
        self.assertEqual(b,quantile_fit(z))

    def test_quantile_boundary_equality_uses_lower_bin(self):
        z=self.z.iloc[:2].copy(); s=z.symbol.iloc[0]
        z['shock_intensity']=[1.,2.]; z['vol_ratio']=[1.,2.]
        key=quantile_keys(z,{s:{'shock_intensity':[1.,2.],'vol_ratio':[1.,2.]}})
        self.assertEqual(list(key.I),['QLOW','QMID'])

    def test_unavailable_not_mapped_to_low_risk(self):
        k=quantile_keys(self.q,quantile_fit(self.q))
        self.assertTrue(k.loc[~self.q.available,'bucket'].eq('UNAVAILABLE').all())

    def test_lag_nonfinite_is_error_not_cohort_drop(self):
        p=self.p.copy(); p['lag_std12']=np.nan
        with self.assertRaises(RuntimeError): table(p,self.ev,(2021,))

    def test_binary_predictor_bounds(self):
        x,names=design(self.z,'L'); probe=d3.fit_probe(x,np.zeros(len(x)),names);probe['intercept']=9.
        self.assertTrue((predict(self.z,'L',probe,'future_tail')==1).all())

    def test_day_blocks_keep_joint_counts(self):
        b=d3.block_stats(self.z,np.ones(len(self.z)),5)
        self.assertEqual(int(b.n.sum()),len(self.z))

    def test_constant_block_gain_interval(self):
        b=d3.block_stats(self.z,np.full(len(self.z),.2),5); c=interval(b)
        self.assertAlmostEqual(c['low'],.2); self.assertAlmostEqual(c['high'],.2)

    def test_fixed_seed_is_reproducible(self):
        b=d3.block_stats(self.z,np.sin(np.arange(len(self.z))),5)
        self.assertEqual(interval(b),interval(b))

    def test_unknown_probe_rejected(self):
        with self.assertRaises(ValueError): design(self.z,'WINNER')

    def test_protocol_and_horizons_fixed(self):
        self.assertEqual(PROTOCOL_COMMIT,'ef865110aee6c1c3b300d27c38a578c2b8882a67')
        self.assertEqual(d3.HORIZONS,(15,30,60)); self.assertEqual(d3.LAMBDA,.01)

if __name__=='__main__': unittest.main()
