"""Physical-cutoff sampling diagnostics; no economic policy backtest."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd
from scipy import signal

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from reproduce_historical_baseline import load_bars
from star50_filter.filters import butter_lowpass

OUT=ROOT/'artifacts/sampling_ratio_v1'
DATA=ROOT/'artifacts/drawdown_material'


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def run_stats(direction,minutes):
    d=np.asarray(direction,int)
    changes=np.flatnonzero(d[1:]!=d[:-1])+1
    lengths=np.diff(changes)*minutes
    return {'observations':len(d),'direction_changes':len(changes),
        'zero_direction_observations':int((d==0).sum()),
        'closed_direction_runs':len(lengths),
        'short_runs_le10min':int((lengths<=10).sum()),
        'short_run_fraction':float((lengths<=10).mean()) if len(lengths) else None,
        'median_closed_run_trading_minutes':float(np.median(lengths)) if len(lengths) else None}


def main():
    OUT.mkdir(exist_ok=True)
    material=json.loads((DATA/'receipt.json').read_text())['views']
    hashes={x['view_id']:x['export_sha256'] for x in material}
    for view in ['1m_official','5m_offset_0']:
        assert sha(DATA/(view+'.parquet'))==hashes[view]
    save('data_usage.json',{'2020-2024':'price_only_warmup_and_state','2025':'consumed_signal_diagnostics',
        '2026':'excluded','no_economic_backtest':True,'physical_cutoff_minutes':120,
        'input_hashes':{v:hashes[v] for v in ['1m_official','5m_offset_0']},
        'dependency_hashes':{n:sha(ROOT/n) for n in ['src/star50_filter/filters.py','scripts/reproduce_historical_baseline.py']},
        'source_sha256':sha(Path(__file__)),
        'method_sha256':sha(ROOT/'docs/research/sampling_ratio_v1/method.md')})
    mathematical=[]
    for step in [30.,15.,5.,1.,.25,.05,1/60]:
        ratio=120/step;k=np.tan(np.pi/ratio)
        sos=signal.butter(1,1/120,fs=1/step,output='sos')
        _,response=signal.sosfreqz(sos,worN=[1/120],fs=1/step)
        low_frequency_delay=step/(2*k)
        mathematical.append({'sample_minutes':step,'ratio':ratio,'cutoff_gain':float(abs(response[0])),
            'cutoff_phase_delay_minutes':float(-np.angle(response[0])*120/(2*np.pi)),
            'low_frequency_delay_minutes':float(low_frequency_delay),
            'low_frequency_delay_relative_error':float(1-low_frequency_delay/(120/(2*np.pi))),
            'single_sample_impulse_first_weight':float(sos[0,0])})
        assert abs(abs(response[0])-2**-.5)<1e-10
        assert abs(-np.angle(response[0])*120/(2*np.pi)-15)<1e-9
    pd.DataFrame(mathematical).to_csv(OUT/'response.csv',index=False)
    m1,m5=load_bars(DATA,'1m_official'),load_bars(DATA,'5m_offset_0')
    x1,x5=np.log(m1.close.to_numpy()),np.log(m5.close.to_numpy())
    norm1=butter_lowpass(x1,120,1);norm5=butter_lowpass(x5,24,1)
    y1=norm1+x1[0];y5=norm5+x5[0]
    identities=[]
    for ratio,x,norm in [(120,x1,norm1),(24,x5,norm5)]:
        coefficient=np.tan(np.pi/ratio)/(1+np.tan(np.pi/ratio))
        slope=np.diff(norm)
        algebra=coefficient*((x[1:]-x[0])+(x[:-1]-x[0])-2*norm[:-1])
        valid=np.isfinite(slope)&np.isfinite(algebra)
        error=float(np.max(abs(slope[valid]-algebra[valid])))
        strong=valid&(abs(slope)>1e-12)
        assert error<1e-12
        assert np.array_equal(np.sign(slope[strong]),np.sign(algebra[strong]))
        identities.append({'ratio':ratio,'identity_max_abs_error':error,
                           'non_near_zero_signs_identical':True})
    save('slope_identity.json',identities)
    positions=pd.Index(m1.timestamp).get_indexer(m5.timestamp)
    assert (positions>=0).all(),'Some original 5m decision timestamps are not observed by 1m input'
    y1at5=y1[positions]
    s5=np.nan_to_num(np.sign(np.r_[np.nan,np.diff(norm5)])).astype(int)
    s1d5=np.nan_to_num(np.sign(np.r_[np.nan,np.diff(norm1[positions])])).astype(int)
    s1h5=np.nan_to_num(np.sign(pd.Series(norm1).diff(5).to_numpy())).astype(int)
    s1h1=np.nan_to_num(np.sign(np.r_[np.nan,np.diff(norm1)])).astype(int)
    for n in [1000,len(x1)//2]:
        assert np.allclose(butter_lowpass(x1[:n],120,1)+x1[0],y1[:n],equal_nan=True,atol=0,rtol=0)
    p=pd.DataFrame({'timestamp':m5.timestamp,'day':m5.trading_day,'close_5m':m5.close,
        'close_1m_same_time':m1.close.to_numpy()[positions],'lowpass_5m_log':y5,
        'lowpass_1m_at5m_log':y1at5,'M5':s5,'M1_D5':s1d5})
    p=p.loc[p.day>='2025-01-01'].reset_index(drop=True)
    p.to_parquet(OUT/'common_5m_grid.parquet',index=False)
    rows=[];agreements=[]
    regions=[('2025','2025-01-01','2025-12-31'),('2025_apr_sep','2025-04-01','2025-09-30')]
    regions += [(f'2025_{m:02d}',f'2025-{m:02d}-01',str((pd.Timestamp(2025,m,1)+pd.offsets.MonthEnd()).date())) for m in range(1,13)]
    for region,start,end in regions:
        ix1=m1.trading_day.between(start,end).to_numpy();ix5=m5.trading_day.between(start,end).to_numpy()
        for name,d,keep,minutes in [('M5',s5,ix5,5),('M1_D5',s1d5,ix5,5),
                                   ('M1_H5_D1',s1h5,ix1,1),('M1_H1_D1',s1h1,ix1,1)]:
            rows.append({'region':region,'method':name,**run_stats(d[keep],minutes)})
        difference=(y1at5-y5)[ix5]*10000
        price_difference=(m1.close.to_numpy()[positions]-m5.close.to_numpy())[ix5]
        agreements.append({'region':region,'observations':int(ix5.sum()),
            'input_close_equal_fraction':float((price_difference==0).mean()),
            'input_close_max_difference':float(abs(price_difference).max()),
            'same_5min_slope_direction_agreement':float((s5[ix5]==s1d5[ix5]).mean()),
            'median_abs_filter_difference_log_bp':float(np.median(abs(difference))),
            'p95_abs_filter_difference_log_bp':float(np.quantile(abs(difference),.95))})
    pd.DataFrame(rows).to_csv(OUT/'signal_diagnostics.csv',index=False)
    pd.DataFrame(agreements).to_csv(OUT/'alignment.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    periods=np.geomspace(.2,1200,1200);omega=2*np.pi/periods;tau=120/(2*np.pi)
    h=1/(1+1j*omega*tau)
    axes[0].semilogx(periods,abs(h),label='one-pole lowpass amplitude')
    axes[0].semilogx(periods,abs(1j*omega*h)*tau,label='lowpass + derivative (normalized)')
    axes[0].semilogx(periods,abs((1-np.exp(-1j*omega*5))/5*h)*tau,label='lowpass + fixed 5min difference')
    axes[0].axvline(120,color='grey',ls='--');axes[0].set_xlabel('Input period (trading minutes)')
    axes[0].set_title('Continuous-time limit: lowpass value vs slope');axes[0].legend(fontsize=7)
    q=p.loc[p.day.between('2025-09-01','2025-09-05')].reset_index(drop=True)
    axes[1].plot(np.exp(q.lowpass_5m_log),label='5m input / LP24')
    axes[1].plot(np.exp(q.lowpass_1m_at5m_log),label='1m input / LP120, same 5m points',alpha=.8)
    axes[1].set_title('Same 120-minute cutoff, common decision grid')
    axes[1].set_xlabel('Existing 5m observations: 2025-09-01 to 09-05');axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(alpha=.2)
    fig.savefig(OUT/'comparison.png',dpi=150);plt.close(fig)
    save('validation.json',{'native_views_only':True,'prefix_invariance_passed':True,
        'fixed_cutoff_gain_and_delay_passed':True,'actual_seconds_data_tested':False,
        'new_strategy_or_profit_claim':False,
        'files':{q.name:sha(q) for q in OUT.iterdir() if q.is_file() and q.name!='validation.json'}})
    print(pd.DataFrame(mathematical).to_string(index=False))
    print(pd.DataFrame(rows).loc[lambda z:z.region.isin(['2025','2025_apr_sep'])].to_string(index=False))
    print(pd.DataFrame(agreements).head(2).to_string(index=False))


if __name__=='__main__':main()
