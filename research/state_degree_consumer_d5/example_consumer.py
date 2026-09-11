"""Query the bounded research consumer; receipt delay is synthetic, never measured."""
import argparse
from datetime import timedelta
import gzip
import io
import json
import math
from pathlib import Path

from consumer import SYMBOLS, ResearchConsumer, aware, build_snapshot
from run_acceptance import D2_SHA, D4_SHA, load_attributes, verified_archive


def query(args):
    at=aware(args.as_of)
    if not math.isfinite(args.receipt_delay_seconds) or args.receipt_delay_seconds<0:
        raise ValueError('receipt delay must be a finite nonnegative synthetic delay')
    if not 2021<=at.year<=2025:
        raise ValueError('bounded historical query only')
    z2,_=verified_archive(Path(args.d2_zip),D2_SHA,'output_manifest.json')
    z4,_=verified_archive(Path(args.d4_zip),D4_SHA,'BUNDLE_MANIFEST.json')
    attrs=load_attributes(z4); c=ResearchConsumer(); n=0
    with gzip.GzipFile(fileobj=z2.open('causal_event_ledger.jsonl.gz')) as gz:
        for line in io.TextIOWrapper(gz,encoding='utf-8'):
            e=json.loads(line)
            received=aware(e['published_at'])+timedelta(seconds=args.receipt_delay_seconds)
            if received>at:break
            # Old-day snapshots have expired. This consumer does not initialize a price engine.
            if e['symbol']!=args.symbol or aware(e['bar_end']).date()!=at.date():continue
            a=attrs[(e['symbol'],e['bar_end'])] if e['event_type']=='E15' else None
            c.ingest(build_snapshot(e,a),received_at=received);n+=1
    result=c.as_of(args.symbol,at)
    result.update(example_events_ingested=n,synthetic_receipt_delay_seconds=args.receipt_delay_seconds,
                  actual_external_consumer_connected=False)
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--d2-zip',required=True);p.add_argument('--d4-zip',required=True)
    p.add_argument('--symbol',choices=SYMBOLS,required=True);p.add_argument('--as-of',required=True)
    p.add_argument('--receipt-delay-seconds',type=float,default=0.)
    query(p.parse_args())
