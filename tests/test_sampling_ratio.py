import numpy as np
from scipy import signal

from star50_filter.filters import butter_lowpass


def test_same_physical_cutoff_keeps_cutoff_phase_delay():
    for step in [30.,15.,5.,1.,.25,.05,1/60]:
        sos=signal.butter(1,1/120,fs=1/step,output='sos')
        _,h=signal.sosfreqz(sos,worN=[1/120],fs=1/step)
        assert np.isclose(abs(h[0]),1/np.sqrt(2),atol=1e-11)
        assert np.isclose(-np.angle(h[0])*120/(2*np.pi),15,atol=1e-9)


def test_exact_one_pole_slope_identity():
    x=np.random.default_rng(918).normal(0,.001,2000).cumsum()
    for p in [24,120]:
        y=butter_lowpass(x,p,1);b=np.tan(np.pi/p)/(1+np.tan(np.pi/p))
        lhs=np.diff(y);rhs=b*((x[1:]-x[0])+(x[:-1]-x[0])-2*y[:-1])
        valid=np.isfinite(lhs)&np.isfinite(rhs)
        assert np.allclose(lhs[valid],rhs[valid],rtol=0,atol=1e-14)


def test_actual_filter_sine_phase_matches_frequency_response():
    for step in [5,1]:
        p=120//step;t=np.arange(60*p)*step;x=np.sin(2*np.pi*t/120)
        y=butter_lowpass(x,p,1)
        j=np.arange(20*p,len(t));design=np.c_[np.sin(2*np.pi*t[j]/120),np.cos(2*np.pi*t[j]/120)]
        fitted=np.linalg.lstsq(design,y[j],rcond=None)[0]
        assert np.allclose(fitted,[.5,-.5],rtol=0,atol=1e-11)


def test_single_bad_sample_weight_shrinks_but_phase_delay_does_not():
    weights=[]
    for p in [24,120,2400,7200]:
        b=np.tan(np.pi/p)/(1+np.tan(np.pi/p));weights.append(b)
    assert np.all(np.diff(weights)<0)
    assert weights[-1]<weights[0]/200
