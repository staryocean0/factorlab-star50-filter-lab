from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss,brier_score_loss,roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from state_sufficiency import build_panel,SYMBOLS,state_band
CHECKPOINTS=(5,10,15,20);SEED=20260907
MODELS={'ratio_only':['log_ratio'],'plus_direction':['log_ratio','direction'],'plus_interaction':['log_ratio','direction','ratio_x_direction']}

def checkpoints(panel,year):
 rows=[]
 for (symbol,session),z0 in panel.groupby(['symbol','session'],sort=False):
  z=z0.sort_values('minute').reset_index(drop=True);r=z.return_bp.to_numpy(float);first=z['first'].to_numpy(float);mins=z.minute.to_numpy(int)
  for j in np.flatnonzero(first==1):
   if mins[j]<33:continue
   sig=float(z.loc[j,'sigma_pre']);ev=float(r[j])
   if not(np.isfinite(sig) and sig>0 and np.isfinite(ev) and ev!=0):continue
   d=1.0 if ev>0 else -1.0
   for cp in CHECKPOINTS:
    a=r[j+cp-4:j+cp+1];b=r[j+cp+1:j+cp+6]
    if len(a)!=5 or len(b)!=5 or not np.isfinite(a).all() or not np.isfinite(b).all():continue
    cur=float(np.sqrt(np.mean(a*a))/sig);nxt=float(np.sqrt(np.mean(b*b))/sig);lr=float(np.log(max(cur,1e-8)))
    rows.append({'key':f'{symbol}|{session}|{mins[j]}','symbol':symbol,'year':year,'checkpoint':cp,'event_return_bp':ev,'direction':d,'current_ratio':cur,'current_state':state_band(cur),'log_ratio':lr,'ratio_x_direction':lr*d,'next_unsafe':int(nxt>=1.5)})
 return pd.DataFrame(rows)

def fit(train):
 y=train.next_unsafe.to_numpy(int);out={}
 for n,c in MODELS.items():
  m=make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=2000,class_weight=None,solver='lbfgs',random_state=SEED));m.fit(train[c],y);out[n]=m
 return out

def metric(y,p):
 y=np.asarray(y,int);p=np.asarray(p,float);return {'n':len(y),'base_rate':float(y.mean()),'log_loss':float(log_loss(y,p,labels=[0,1])),'brier':float(brier_score_loss(y,p)),'auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None}

def boot(df,p0,p1,repeats=5000):
 eps=1e-15;y=df.next_unsafe.to_numpy(int)
 def l(p):p=np.clip(p,eps,1-eps);return -(y*np.log(p)+(1-y)*np.log(1-p))
 q=pd.DataFrame({'key':df.key,'d':l(p1)-l(p0)}).groupby('key').d.mean().to_numpy();rng=np.random.default_rng(SEED);v=[]
 for _ in range(repeats):v.append(float(q[rng.integers(0,len(q),len(q))].mean()))
 z=np.quantile(v,[.025,.5,.975]);return {'events':len(q),'point':float(q.mean()),'median':float(z[1]),'ci95':[float(z[0]),float(z[2])]}

def summarize(tr,ev,rep):
 packs=fit(tr);out={'fit':{'rows':len(tr),'events':int(tr.key.nunique()),'up_events':int(tr[tr.direction>0].key.nunique()),'down_events':int(tr[tr.direction<0].key.nunique())},'evaluation':{}}
 for label,df in [('2025',ev),('2026_replay',rep)]:
  ps={n:packs[n].predict_proba(df[c])[:,1] for n,c in MODELS.items()};s={'rows':len(df),'events':int(df.key.nunique()),'models':{n:metric(df.next_unsafe,p) for n,p in ps.items()}}
  if label=='2025':s['bootstrap']={n:boot(df,ps['ratio_only'],ps[n]) for n in ['plus_direction','plus_interaction']}
  strata=[]
  for d,z in df.groupby('direction'):
   for st,g in z.groupby('current_state'):strata.append({'direction':'up' if d>0 else 'down','state':st,'n':len(g),'events':int(g.key.nunique()),'next_unsafe':float(g.next_unsafe.mean())})
  s['strata']=strata;out['evaluation'][label]=s
 return out

def load(root,s,y):
 p=root/f'data/cross_index_risk_gate_v1/1m/{s}/{y}.parquet' if y<=2025 else root/f'data/cross_index_risk_gate_2026_v1/1m/{s}/2026.parquet';return pd.read_parquet(p)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo-root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();root=Path(a.repo_root);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 frames=[]
 for y in [2024,2025,2026]:
  for s in SYMBOLS:frames.append(checkpoints(build_panel(load(root,s,y),s),y))
 x=pd.concat(frames,ignore_index=True);res=summarize(x[x.year==2024],x[x.year==2025],x[x.year==2026]);res['guardrails']=['event direction fixed from shock minute','no state threshold/window change','2024 fit only','2026 replay descriptive']
 x.to_csv(out/'direction_checkpoints.csv',index=False);(out/'direction_summary.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res))
if __name__=='__main__':main()
