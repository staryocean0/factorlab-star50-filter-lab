from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve()
BASE = HERE.with_name("run_frequency_economics.py")
spec = importlib.util.spec_from_file_location("freq_base", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load frozen base runner")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def bootstrap_be_delta_fast(events, symbol: str, rule: str, h: int, repeats: int = 2000) -> dict:
    x = events[(events.year <= 2025) & (events.symbol == symbol) & (events.rule == rule) & (events.lookback_min == h)]
    keys = np.asarray(sorted(x.key.unique()))
    n = len(keys)
    if n < 5:
        return {"events": int(n), "ci95": [None, None], "median": None}
    by = x.groupby(["key", "state"])[["gross_bp", "one_way_turnover"]].sum()
    idx = {k: i for i, k in enumerate(keys)}
    gross = {gate: np.zeros(n, float) for gate in m.GATES}
    turn = {gate: np.zeros(n, float) for gate in m.GATES}
    for (key, gate), q in by.iterrows():
        i = idx[key]
        gross[gate][i] = float(q.gross_bp)
        turn[gate][i] = float(q.one_way_turnover)
    seed = m.SEED + h + (0 if rule == "continuation" else 100) + (0 if symbol == m.SYMBOLS[0] else 1000)
    rng = np.random.default_rng(seed)
    # Exactly the same episode bootstrap law as drawing n keys with replacement:
    # each row is the corresponding multinomial count vector.
    counts = rng.multinomial(n, np.full(n, 1.0 / n), size=repeats)
    g_u = counts @ gross["Unsafe"]
    t_u = counts @ turn["Unsafe"]
    g_r = counts @ gross["Recovering"]
    t_r = counts @ turn["Recovering"]
    valid = (t_u > 0) & (t_r > 0)
    vals = g_u[valid] / t_u[valid] - g_r[valid] / t_r[valid]
    if not len(vals):
        return {"events": int(n), "ci95": [None, None], "median": None}
    q = np.quantile(vals, [0.025, 0.5, 0.975])
    return {"events": int(n), "median": float(q[1]), "ci95": [float(q[0]), float(q[2])], "draws": int(len(vals))}


m.bootstrap_be_delta = bootstrap_be_delta_fast


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    summary = m.run(Path(args.repo_root).resolve(), Path(args.out))
    import json
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
