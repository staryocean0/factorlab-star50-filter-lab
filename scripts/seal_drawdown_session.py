"""Seal one manually authored review; never generate a scientific verdict."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--year',type=int,required=True);args=ap.parse_args()
p=ROOT/'artifacts/drawdown_conditions/sessions'/str(args.year)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
assert not (p/'sealed_receipt.json').exists(),'Already sealed'
review=p/'analysis_ledger.json';ledger=json.loads(review.read_text())
assert ledger['year']==args.year and ledger['reviewer']=='main_agent'
assert ledger['observations'] and ledger['verdict']
ev=p/'evidence_receipt.json';data=json.loads(ev.read_text())
for name,d in data['evidence_files'].items():assert sha(p/name)==d
for name,d in data['source_digests'].items():assert sha(ROOT/name)==d
prior=ROOT/'artifacts/drawdown_conditions/sessions'/str(args.year-1)/'sealed_receipt.json'
assert data['prior_receipt_sha256']==(sha(prior) if args.year>2021 else None)
res={'schema':'star50_fixed_experiment_review@1','year':args.year,
 'evidence_receipt_sha256':sha(ev),'analysis_ledger_sha256':sha(review),
 'prior_receipt_sha256':data['prior_receipt_sha256'],
 'frozen_policy_sha256':data['risk_protocol_sha256'],'parameter_updates':0,
 'fresh_oos':False,'production_authority':False}
(p/'sealed_receipt.json').write_text(json.dumps(res,indent=2)+'\n')
print('sealed',args.year,sha(p/'sealed_receipt.json'))
