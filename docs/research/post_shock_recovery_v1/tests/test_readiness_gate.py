import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from readiness_gate import assess_readiness


def frame(n1,n2):
    rows=[]
    for s,n in [("000688.SH",n1),("000852.SH",n2)]:
        for i in range(n):
            rows.append({"symbol":s,"event_id":f"{s}-{i}","eligible":True})
    return pd.DataFrame(rows)


def test_descriptive():
    assert assess_readiness(frame(4,5))["tier"]=="descriptive_only"


def test_limited():
    assert assess_readiness(frame(7,8))["tier"]=="limited_validation"


def test_minimum_formal():
    r=assess_readiness(frame(12,8))
    assert r["tier"]=="minimum_formal" and r["formal_core_validation_allowed"]


def test_pooled_only_when_one_index_underrepresented():
    r=assess_readiness(frame(17,4))
    assert r["tier"]=="formal_pooled_only"
    assert not r["formal_core_validation_allowed"]


def test_preferred():
    r=assess_readiness(frame(18,12))
    assert r["tier"]=="preferred_formal" and r["preferred_snapshot_reached"]


def test_deduplicates_events():
    d=frame(6,6)
    d=pd.concat([d,d.iloc[[0]]],ignore_index=True)
    assert assess_readiness(d)["pooled_eligible_first_shocks"]==12


def test_rejects_outcome_columns():
    d=frame(6,6)
    d["next_unsafe"]=0
    with pytest.raises(ValueError):
        assess_readiness(d)
