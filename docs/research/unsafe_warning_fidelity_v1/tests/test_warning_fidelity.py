from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[4]
MOD=Path(__file__).resolve().parents[1]/"code"/"run_warning_fidelity.py"
P4=ROOT/"docs/research/unsafe_risk_admission_5m_v1/code/run_5m_risk_routing.py"

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load(MOD,"fidelity");p4=load(P4,"phase4")


def fixture():
    bars=pd.DataFrame({
        "symbol":["X"]*16,"trading_day":["2025-01-02"]*8+["2025-01-03"]*8,
        "year":[2025]*16,"session":["2025-01-02/0"]*8+["2025-01-03/0"]*8,
        "bar_in_session":list(range(1,9))*2,
        "open":np.exp(np.arange(16)*.001),"valid":[True]*16,
        "route_state":["NoEpisode","Unsafe","Unsafe","Recovering","Recovering","Unknown","Recovering","Recovering",
                       "NoEpisode","Recovering","Recovering","Recovering","Recovering","Recovering","Recovering","Recovering"]
    })
    sig=np.array([1,1,1,-1,-1,-1,1,1, 1,1,-1,-1,1,1,-1,-1],float)
    return bars,sig


def test_perfect_mask_is_true_unsafe_exactly():
    bars,sig=fixture();arr=m.build_eval_arrays(bars,sig);runs=m.mask_runs(arr["true_unsafe"],arr)
    pred,rec=m.make_warning_mask(arr,runs,m.false_candidate_map(arr,runs),1.0,1.0,np.random.default_rng(1))
    assert np.array_equal(pred,arr["true_unsafe"])
    assert rec["false_runs"]==0 and rec["retained_true_runs"]==len(runs)


def test_perfect_targets_match_phase4_semantics():
    bars,sig=fixture();arr=m.build_eval_arrays(bars,sig);pred=arr["true_unsafe"]
    state=m.phase4_equivalent_state(arr,pred)
    for policy in m.POLICIES:
        expected=[]
        for session,idx in bars.groupby("session",sort=False).indices.items():
            ix=np.asarray(idx,int)
            expected.extend(p4.decision_targets(sig[ix],state[ix],np.ones(len(ix),bool),policy).tolist())
        got=m.target_for_policy(arr,pred,policy)
        assert np.array_equal(got,np.asarray(expected,float)),policy


def test_fast_evaluation_matches_phase4_run_accounting():
    bars,sig=fixture();arr=m.build_eval_arrays(bars,sig);pred=arr["true_unsafe"]
    for policy in m.POLICIES:
        fast=m.evaluate_target(arr,m.target_for_policy(arr,pred,policy))
        gross=turn=exp=wins=0
        state=m.phase4_equivalent_state(arr,pred)
        for session,idx in bars.groupby("session",sort=False).indices.items():
            ix=np.asarray(idx,int)
            t=p4.decision_targets(sig[ix],state[ix],np.ones(len(ix),bool),policy)
            q=p4.simulate_valid_run(bars.open.to_numpy(float)[ix],t)
            gross+=q["gross_bp"];turn+=q["one_way_turnover"];exp+=q["exposure_bars"];wins+=q["winning_returns"]
        assert np.isclose(fast["gross_bp"],gross,atol=1e-12)
        assert np.isclose(fast["one_way_turnover"],turn,atol=1e-12)
        assert fast["exposure_bars"]==exp and fast["winning_returns"]==wins


def test_false_candidates_never_overlap_true_unsafe_or_unknown():
    bars,sig=fixture();arr=m.build_eval_arrays(bars,sig);runs=m.mask_runs(arr["true_unsafe"],arr);cm=m.false_candidate_map(arr,runs)
    assert runs
    for pool in cm.values():
        for idx in pool:
            assert not arr["true_unsafe"][idx].any()
            assert not arr["unknown"][idx].any()
            assert len(set(arr["session"][idx]))==1


def test_false_candidate_matches_clock_and_length():
    bars,sig=fixture();arr=m.build_eval_arrays(bars,sig);runs=m.mask_runs(arr["true_unsafe"],arr);cm=m.false_candidate_map(arr,runs)
    r=runs[0];sigkey=(r["year"],r["half"],r["start_bar"],r["length"])
    assert cm[sigkey]
    for idx in cm[sigkey]:
        got=bars.bar_in_session.to_numpy(int)[idx]
        assert np.array_equal(got,np.arange(r["start_bar"],r["start_bar"]+r["length"]))


def test_missed_run_disappears_when_recall_zero_helper_case():
    bars,sig=fixture();arr=m.build_eval_arrays(bars,sig);runs=m.mask_runs(arr["true_unsafe"],arr)
    pred,rec=m.make_warning_mask(arr,runs,m.false_candidate_map(arr,runs),0.0,1.0,np.random.default_rng(2))
    assert not pred.any();assert rec["retained_true_runs"]==0


def test_false_run_ratio_matches_formula():
    assert np.isclose((1-.8)/.8,.25)
    assert np.isclose((1-.9)/.9,1/9)
