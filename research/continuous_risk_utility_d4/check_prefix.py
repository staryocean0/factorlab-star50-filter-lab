"""Twenty fixed market-history prefix checks; not a new raw-3s replay."""
import argparse
import json
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
from run_d4 import history


def run(transport, out):
    with zipfile.ZipFile(transport) as z:
        receipt=json.loads(z.read('TRANSPORT_RECEIPT.json'))
        raw=pd.concat([pd.read_csv(z.open(e['csv_file']),compression='gzip',float_precision='round_trip') for e in receipt['exports']],ignore_index=True)
    raw['bar_end']=pd.to_datetime(raw.bar_end)
    raw=raw.sort_values(['symbol','bar_end']).reset_index(drop=True)
    baseline=history(raw); rows=[]
    cols=['lag_std12','bg48','last_abs','rms3','rms6','rms12','rms48']
    for symbol in ('000688.SH','000852.SH'):
        for year in range(2021,2026):
            subset=raw[(raw.symbol==symbol)&raw.bar_end.dt.year.eq(year)]
            for day in (subset.trading_day.min(),subset.trading_day.max()):
                anchor=subset[(subset.trading_day==day)&subset.bar_end.dt.hour.eq(10)&subset.bar_end.dt.minute.eq(0)].iloc[0]
                j=int(anchor.name); modified=raw.copy()
                mask=(modified.symbol==symbol)&modified.bar_end.ge(anchor.bar_end)
                modified.loc[mask,'close']*=np.exp(.015*np.cos(np.arange(mask.sum())))
                changed=history(modified)
                earlier=(baseline.symbol==symbol)&baseline.bar_end.le(anchor.bar_end)
                np.testing.assert_array_equal(baseline.loc[earlier,cols].to_numpy(),changed.loc[earlier,cols].to_numpy())
                rows.append({'symbol':symbol,'year':year,'anchor':anchor.bar_end.isoformat(),'prefix_rows':int(earlier.sum()),'passed':True})
    result={'schema':'d4_history_prefix_checks_v1','checks':rows,'passed':len(rows),'scope':'new historical L attributes and shared history only; D2 current attributes unchanged, no raw3s recomputation'}
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':len(rows)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--transport',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.transport,a.out)
