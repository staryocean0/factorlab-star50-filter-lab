import numpy as np
import pandas as pd

from star50_filter.bbo_bucket_account import Account, Book, veto_matrix


def book(t, bid, ask=None, code='588000'):
    n=len(t)
    return Book(np.array(t,dtype='int64'),np.array(bid,float),np.array(ask if ask is not None else bid,float),
                np.full(n,20000),np.full(n,20000),np.ones(n,bool),np.ones(n,bool),code=code)


def test_first_quote_is_after_order_and_respects_size_and_session():
    b=book([10,20,30],[1,1,1],[1.01,1.01,1.01])
    b.aq[1]=1;b.executable[2]=False
    assert b.first(11,31,'buy',10000) is None
    assert b.first(10,20,'buy',10000)==0


def test_spot_t1_and_exact_two_sided_fee_accounting():
    b=book([10,20,30,40],[1,1.02,1.03,1.04],[1.01,1.03,1.04,1.05]);a=Account('baseline','spot','588000')
    a.step({b.code:b},b,1,10,20,'2025-01-02','09:35',9)
    assert a.quantity==10000
    a.step({b.code:b},b,0,20,30,'2025-01-02','09:40',19)
    assert a.quantity==10000 and a.blocked_T1==1
    a.step({b.code:b},b,0,30,40,'2025-01-03','09:35',29)
    assert a.quantity==0 and abs(a.cash-100195.92)<1e-8
    assert abs(a.trades[0]['net_pnl']-195.92)<1e-8


def test_intra_interval_drawdown_is_not_hidden_by_recovery():
    b=book([1,2,3,4],[1.,2.,.5,1.5]);a=Account('baseline','spot','588000',cash=90000.,holding=b.code,quantity=10000,last_bid=1,last_time=0)
    a.mark_to({b.code:b},4)
    assert np.isclose(a.mdd,15000/110000)
    assert a.mdd_at==3


def test_option_cannot_select_future_listed_quote_and_charges_per_contract():
    spot=book([10,30],[1.,1.],[1.,1.])
    b=book([1,11,31],[.049,.049,.052],[.05,.05,.053],code='CALL')
    b.multiplier=10000;b.strike=1;b.expiry='2025-02-26';b.option_type='C'
    future=book([15,20],[.03,.03],code='FUTURE');future.multiplier=10000;future.strike=1;future.expiry='2025-01-22';future.option_type='C'
    a=Account('baseline','option','588000')
    a.step({'CALL':b,'FUTURE':future},spot,1,10,20,'2025-01-02','09:35',9)
    assert a.holding=='CALL' and a.cash==99495.5
    a.step({'CALL':b,'FUTURE':future},spot,0,30,40,'2025-01-02','09:40',29)
    assert np.isclose(a.cash,100011.) and np.isclose(a.trades[0]['net_pnl'],11.)


def test_joint_condition_requires_both_mechanism_members():
    f=pd.DataFrame({'work_efficiency_48':[.1,.9], 'threshold_work_amplitude_48':[2.,2.],
      'slow_opposition_strength_48':[0.,0.], 'slow_directional_efficiency_48':[1.,1.],
      'fast_work_velocity_48':[1.,1.], 'work_travel_threshold_12':[2.,2.], 'reversal_count_48':[1,1]})
    v=veto_matrix(f,dict(eff_low=.2,threshold_high=1,slow_coherent=.8,fast_high=3,progress_low=1))
    assert v.small_work.tolist()==[True,False]
    assert v.baseline.tolist()==[False,False]


def test_dividend_receivable_does_not_make_stale_pre_ex_quote_a_new_peak():
    b=book([10,20],[.986,.986]);a=Account('baseline','spot','588000',cash=90000.,holding=b.code,
        quantity=10000,last_bid=1.,last_time=0,receivable=140.)
    a.mark_to({b.code:b},1)
    assert a.peak==100000.
    a.mark_to({b.code:b},20)
    assert np.isclose(a.nav,100000.) and a.peak==100000.


def test_missing_bid_is_not_a_zero_value_trade_or_nav():
    b=book([1,2,3],[1,0,1],[1.01,0,1.01]);b.bq[1]=0;b.aq[1]=0
    a=Account('baseline','option','588000',cash=90000,holding=b.code,quantity=10000,last_bid=1,last_time=0)
    a.mark_to({b.code:b},3)
    assert a.mdd==0 and a.nav==100000 and a.missing_bid_observations==1
    assert b.first(2,3,'sell',1) is None


def test_confirmed_otm_expiry_is_extinction_not_zero_quote_fill():
    spot=book([10],[1.029],[1.03]);b=book([1],[0],[0],code='EXP')
    b.option_type='C';b.expiry='2025-01-22';b.strike=1.05;b.multiplier=10000
    a=Account('baseline','option','588000',cash=99993.5,holding='EXP',direction=1,quantity=1,
        multiplier=10000,buy_price=.0002,buy_fee=4.5,buy_time=1,last_bid=.0001,last_time=1)
    a.end_day({'EXP':b},spot,'2025-01-22',11)
    assert a.holding is None and a.cash==99993.5 and a.expired_otm==1
    assert a.trades[0]['net_pnl']==-6.5 and a.orders[-1]['side']=='expiry'
