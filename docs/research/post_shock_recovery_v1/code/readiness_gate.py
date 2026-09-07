from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
FORBIDDEN_OUTCOME_COLUMNS = {
    "current_ratio","next_ratio","next_unsafe","current_state",
    "unsafe_blocks_15m","any_unsafe_15m","mean_ratio_15m",
    "stable_next10","release_probability"
}

def assess_readiness(events: pd.DataFrame) -> dict:
    cols=set(events.columns)
    leaked=sorted(cols & FORBIDDEN_OUTCOME_COLUMNS)
    if leaked:
        raise ValueError(f"post-shock outcome columns are forbidden in readiness gate: {leaked}")
    required={"symbol","event_id"}
    missing=required-cols
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    x=events.copy()
    if "eligible" in x.columns:
        x=x[x["eligible"].astype(bool)]
    x=x[["symbol","event_id"]].drop_duplicates()
    unknown=sorted(set(x["symbol"])-set(SYMBOLS))
    if unknown:
        raise ValueError(f"unexpected symbols: {unknown}")
    counts={s:int((x.symbol==s).sum()) for s in SYMBOLS}
    pooled=sum(counts.values())
    min_idx=min(counts.values())
    if pooled < 10:
        tier="descriptive_only"
    elif pooled < 20:
        tier="limited_validation"
    elif min_idx < 6:
        tier="formal_pooled_only"
    elif pooled >= 30 and min_idx >= 10:
        tier="preferred_formal"
    else:
        tier="minimum_formal"
    return {
        "schema":"post_shock_recovery_readiness@1",
        "pooled_eligible_first_shocks":pooled,
        "by_symbol":counts,
        "tier":tier,
        "formal_core_validation_allowed": bool(pooled>=20 and min_idx>=6),
        "preferred_snapshot_reached": bool(pooled>=30 and min_idx>=10),
        "guardrail":"No post-shock outcome/state columns were inspected."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--events", required=True)
    p.add_argument("--out")
    a=p.parse_args()
    d=pd.read_csv(a.events)
    result=assess_readiness(d)
    text=json.dumps(result, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text+"\n", encoding="utf-8")
    print(text)

if __name__=="__main__":
    main()
