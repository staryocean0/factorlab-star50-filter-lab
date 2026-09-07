"""Post-result measurement diagnostics. All results are synthetic and exploratory."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import first_shock_gate as g


def add_components(f: pd.DataFrame) -> pd.DataFrame:
    f=f.copy()
    for length in (2,4):
        f[f"log_e{length}"]=np.nan
        for _,ix in f.groupby("session",sort=False).groups.items():
            energy=g.haar_energy(f.loc[ix,"return_bp"].to_numpy(float),length)
            f.loc[ix,f"log_e{length}"]=np.log(np.maximum(energy,1e-8))
    return f


class SplitPair(g.PairModels):
    def scores(self,f):
        b=f[g.BASE].to_numpy(float)
        logs=f[["log_e2","log_e4"]].to_numpy(float)
        d=(logs-self.residualizer.predict(b))/self.residual_scale
        return (self.baseline.predict_proba(b)[:,1],
                self.enhanced.predict_proba(np.c_[b,d])[:,1],d[:,0]-d[:,1])


def fit_split(f):
    a=f.loc[f.year.isin([2021,2022])&f.metric_ok]
    c=f.loc[(f.year==2023)&f.metric_ok]
    old=g.fit_pair(a,c)
    b=a[g.BASE].to_numpy(float);y=a.target.to_numpy(int)
    z=a[["log_e2","log_e4"]].to_numpy(float)
    residualizer=make_pipeline(StandardScaler(),Ridge(alpha=1.))
    residualizer.fit(b,z)
    d=z-residualizer.predict(b)
    scale=np.maximum(d.std(axis=0),1e-8)
    model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,class_weight=None,
                  max_iter=2000,solver="lbfgs",random_state=g.SEED))
    model.fit(np.c_[b,d/scale],y)
    pair=SplitPair(residualizer,scale,old.baseline,model,{})
    pb,pe,_=pair.scores(c)
    pair.thresholds={n:{str(q):float(np.quantile(s,1-q)) for q in (.1,.2,.3)}
                     for n,s in (("baseline",pb),("enhanced",pe))}
    return pair


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--resume",action="store_true",help="reuse already sealed per-case JSON after interruption")
    args=parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()) and not args.resume:raise FileExistsError("immutable outputs")
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    alternating=np.tile([-1.,1.],5000)
    white=np.random.default_rng(g.SEED).normal(size=10000)
    power={}
    for name,r in (("alternating_unit_returns",alternating),("unit_variance_white_noise",white)):
        e={str(k):float(np.nanmean(g.haar_energy(r,k))) for k in (2,4,8,16)}
        e["aggregate_fast"]=(e["2"]+e["4"])/2
        power[name]=e
    for seed in (20260907,20260908,20260909):
        for kind in ("null","precursor"):
            name=f"split_{kind}_{seed}"
            path=args.out/f"{name}.json"
            points=None
            if path.exists() and args.resume:
                result=json.loads(path.read_text())
            else:
                f=add_components(g.make_features(g.synthetic_panel(kind,seed=seed)))
                pair=fit_split(f)
                result,points,events=g.evaluate(pair,f[f.year==2024])
                g.write_json(path,result)
            # Record all tested seeds, not just the best one.
            row={"kind":kind,"seed":seed}
            for m in ("baseline","enhanced"):
                z=result["models"][m]
                row[m+"_clean_risk"]=z["dense_windows_matched_quota"]["risk_inside_clean"]
                row[m+"_recall"]=z["strict_events_matched_quota"]["recall_all_known_events"]
                row[m+"_episode_precision"]=z["strict_events_matched_quota"]["episode_precision_one_to_one"]
            row["clean_risk_delta_ci95"]=result["matched_quota_clean_risk_bootstrap"]["delta_enhanced_minus_baseline_ci95"]
            row["recall_delta_ci95"]=result["matched_quota_event_recall_bootstrap"]["delta_enhanced_minus_baseline_ci95"]
            if kind=="null" and seed==20260907:
                if points is None:
                    points=g.make_features(g.synthetic_panel(kind,seed=seed))
                    points=points[points.year==2024].reset_index(drop=True)
                rng=np.random.default_rng(20261000)
                ok=points.decision_ok.to_numpy(bool)
                alarm=np.zeros(len(points),bool)
                alarm[ok]=g.budget_alarm(rng.random(ok.sum()),.2)
                random_summary,_=g.match_events(points,alarm)
                row["fragmented_random_alarm"]=random_summary
            rows.append(row)
    g.write_json(args.out/"diagnostic_summary.json",{
        "status":"post-result exploratory synthetic diagnostic; no market evidence",
        "scale_cancellation":power,
        "independent_20pct_alarm_hit_probability_14_opportunities":1-.8**14,
        "all_results":rows})
    print(pd.DataFrame([{k:v for k,v in r.items() if k!='fragmented_random_alarm'} for r in rows]).to_string(index=False))


if __name__=="__main__":main()
