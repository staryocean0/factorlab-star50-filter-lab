from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

LOOKBACKS = (1, 2, 3, 5, 10, 15, 30)
RULES = ("continuation", "reversal")
GATES = ("Unsafe", "Recovering")
COSTS = (0.5, 1.0, 2.0, 3.0, 5.0)
SYMBOLS = ("000688.SH", "000852.SH")
YEARS = (2021, 2022, 2023, 2024, 2025, 2026)
SEED = 20260908


def load_state_module(repo_root: Path):
    path = repo_root / "docs/research/post_shock_recovery_v1/code/state_sufficiency.py"
    spec = importlib.util.spec_from_file_location("state_sufficiency_frozen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen state builder")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_year(root: Path, symbol: str, year: int) -> pd.DataFrame:
    if year <= 2025:
        p = root / f"data/cross_index_risk_gate_v1/1m/{symbol}/{year}.parquet"
    elif year == 2026:
        p = root / f"data/cross_index_risk_gate_2026_v1/1m/{symbol}/2026.parquet"
    else:
        raise ValueError(year)
    return pd.read_parquet(p)


def state_at_lag(r: np.ndarray, event_idx: int, lag: int, sigma_pre: float) -> tuple[str, float | None]:
    if lag < 0:
        return "Unknown", None
    if lag < 5:
        return "Unsafe", None
    i = event_idx + lag
    a = r[i - 4 : i + 1]
    if len(a) != 5 or not np.isfinite(a).all() or not np.isfinite(sigma_pre) or sigma_pre <= 0:
        return "Unknown", None
    ratio = float(np.sqrt(np.mean(a * a)) / sigma_pre)
    return ("Unsafe" if ratio >= 1.5 else "Recovering"), ratio


def signed_signal(r: np.ndarray, decision_idx: int, lookback: int, rule: str) -> int:
    a = r[decision_idx - lookback + 1 : decision_idx + 1]
    if len(a) != lookback or not np.isfinite(a).all():
        return 0
    s = float(np.sum(a))
    if s > 0:
        pos = 1
    elif s < 0:
        pos = -1
    else:
        pos = 0
    if rule == "continuation":
        return pos
    if rule == "reversal":
        return -pos
    raise ValueError(rule)


def build_episode_decisions(panel: pd.DataFrame, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict] = []
    events: list[dict] = []
    for (symbol, session), z0 in panel.groupby(["symbol", "session"], sort=False):
        z = z0.sort_values("minute").reset_index(drop=True)
        r = z.return_bp.to_numpy(float)
        first = z["first"].to_numpy(float)
        mins = z.minute.to_numpy(int)
        for j in np.flatnonzero(first == 1):
            if mins[j] < 33:
                continue
            sig = float(z.loc[j, "sigma_pre"])
            if not (np.isfinite(sig) and sig > 0):
                continue
            key = f"{symbol}|{session}|{mins[j]}"
            events.append(
                {
                    "key": key,
                    "symbol": symbol,
                    "year": year,
                    "session": session,
                    "day": z.loc[j, "day"],
                    "event_minute": int(mins[j]),
                    "sigma_pre": sig,
                }
            )
            # decision at event close (lag=0) can only earn the following minute.
            for i in range(j, len(z) - 1):
                lag = i - j
                state, ratio = state_at_lag(r, j, lag, sig)
                nxt = r[i + 1]
                row = {
                    "key": key,
                    "symbol": symbol,
                    "year": year,
                    "session": session,
                    "day": z.loc[j, "day"],
                    "event_minute": int(mins[j]),
                    "lag": int(lag),
                    "decision_minute": int(mins[i]),
                    "state": state,
                    "recovery_ratio": ratio,
                    "next_return_bp": float(nxt) if np.isfinite(nxt) else np.nan,
                }
                for h in LOOKBACKS:
                    row[f"sig_cont_{h}"] = signed_signal(r, i, h, "continuation")
                rows.append(row)
    return pd.DataFrame(rows), pd.DataFrame(events).drop_duplicates("key")


def simulate_event(z: pd.DataFrame, lookback: int, rule: str, gate: str) -> dict:
    z = z.sort_values("lag")
    prev = 0
    gross = 0.0
    turnover = 0.0
    exposure = 0
    wins = 0
    active_returns = 0
    sign_col = f"sig_cont_{lookback}"
    multiplier = 1 if rule == "continuation" else -1
    for row in z.itertuples(index=False):
        nxt = float(row.next_return_bp) if np.isfinite(row.next_return_bp) else np.nan
        raw = int(getattr(row, sign_col))
        desired = multiplier * raw if row.state == gate and np.isfinite(nxt) else 0
        turnover += abs(desired - prev)
        if desired != 0:
            pnl = desired * nxt
            gross += pnl
            exposure += 1
            active_returns += 1
            wins += int(pnl > 0)
        prev = desired
    turnover += abs(prev)  # forced flat at episode/session end
    return {
        "gross_bp": gross,
        "one_way_turnover": turnover,
        "exposure_minutes": exposure,
        "active_returns": active_returns,
        "winning_minutes": wins,
    }


def build_strategy_events(decisions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, z in decisions.groupby("key", sort=False):
        meta = z.iloc[0]
        for gate in GATES:
            for rule in RULES:
                for h in LOOKBACKS:
                    s = simulate_event(z, h, rule, gate)
                    rows.append(
                        {
                            "key": key,
                            "symbol": meta.symbol,
                            "year": int(meta.year),
                            "state": gate,
                            "rule": rule,
                            "lookback_min": h,
                            **s,
                        }
                    )
    return pd.DataFrame(rows)


def summarize_strategy(events: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    agg = (
        events.groupby(group_cols, dropna=False)[
            ["gross_bp", "one_way_turnover", "exposure_minutes", "active_returns", "winning_minutes"]
        ]
        .sum()
        .reset_index()
    )
    counts = events.groupby(group_cols, dropna=False).key.nunique().rename("events").reset_index()
    out = agg.merge(counts, on=group_cols, how="left")
    out["gross_bp_per_exposure_min"] = out.gross_bp / out.exposure_minutes.replace(0, np.nan)
    out["break_even_one_way_cost_bp"] = out.gross_bp / out.one_way_turnover.replace(0, np.nan)
    out["minute_hit_rate"] = out.winning_minutes / out.active_returns.replace(0, np.nan)
    for c in COSTS:
        out[f"net_bp_cost_{c:g}"] = out.gross_bp - c * out.one_way_turnover
        out[f"net_bp_per_exposure_min_cost_{c:g}"] = out[f"net_bp_cost_{c:g}"] / out.exposure_minutes.replace(0, np.nan)
    return out


def build_opportunity_events(decisions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, z0 in decisions.groupby("key", sort=False):
        z = z0.sort_values("lag").reset_index(drop=True)
        # next_return_bp at decision lag L is the return for L -> L+1.
        nxt = z.next_return_bp.to_numpy(float)
        states = z.state.to_numpy(object)
        meta = z.iloc[0]
        for h in LOOKBACKS:
            for gate in GATES:
                gross_abs = 0.0
                trades = 0
                exposure = 0
                # event-relative non-overlap grid: 0,h,2h,...
                for start in range(0, len(z), h):
                    if start + h > len(z):
                        break
                    if states[start] != gate:
                        continue
                    a = nxt[start : start + h]
                    if len(a) != h or not np.isfinite(a).all():
                        continue
                    gross_abs += abs(float(np.sum(a)))
                    trades += 1
                    exposure += h
                rows.append(
                    {
                        "key": key,
                        "symbol": meta.symbol,
                        "year": int(meta.year),
                        "state": gate,
                        "horizon_min": h,
                        "oracle_abs_gross_bp": gross_abs,
                        "trades": trades,
                        "exposure_minutes": exposure,
                    }
                )
    return pd.DataFrame(rows)


def summarize_opportunity(events: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    agg = events.groupby(group_cols)[["oracle_abs_gross_bp", "trades", "exposure_minutes"]].sum().reset_index()
    counts = events.groupby(group_cols).key.nunique().rename("events").reset_index()
    out = agg.merge(counts, on=group_cols, how="left")
    out["oracle_break_even_one_way_cost_bp"] = out.oracle_abs_gross_bp / (2 * out.trades.replace(0, np.nan))
    out["oracle_gross_bp_per_minute"] = out.oracle_abs_gross_bp / out.exposure_minutes.replace(0, np.nan)
    for c in COSTS:
        out[f"oracle_net_bp_per_min_cost_{c:g}"] = (out.oracle_abs_gross_bp - 2 * c * out.trades) / out.exposure_minutes.replace(0, np.nan)
    return out


def state_movement_summary(decisions: pd.DataFrame) -> pd.DataFrame:
    x = decisions[np.isfinite(decisions.next_return_bp)].copy()
    x["abs_next_bp"] = x.next_return_bp.abs()
    g = x.groupby(["symbol", "year", "state"])
    return g.agg(
        minutes=("next_return_bp", "size"),
        mean_abs_next_bp=("abs_next_bp", "mean"),
        rms_next_bp=("next_return_bp", lambda s: float(np.sqrt(np.mean(np.asarray(s, float) ** 2)))),
    ).reset_index()


def bootstrap_be_delta(events: pd.DataFrame, symbol: str, rule: str, h: int, repeats: int = 2000) -> dict:
    x = events[(events.year <= 2025) & (events.symbol == symbol) & (events.rule == rule) & (events.lookback_min == h)]
    keys = np.asarray(sorted(x.key.unique()))
    if len(keys) < 5:
        return {"events": int(len(keys)), "ci95": [None, None], "median": None}
    by = x.groupby(["key", "state"])[["gross_bp", "one_way_turnover"]].sum()
    rng = np.random.default_rng(SEED + h + (0 if rule == "continuation" else 100) + (0 if symbol == SYMBOLS[0] else 1000))
    vals = []
    for _ in range(repeats):
        sample = keys[rng.integers(0, len(keys), size=len(keys))]
        sums = {g: [0.0, 0.0] for g in GATES}
        for k in sample:
            for gate in GATES:
                if (k, gate) in by.index:
                    q = by.loc[(k, gate)]
                    sums[gate][0] += float(q.gross_bp)
                    sums[gate][1] += float(q.one_way_turnover)
        bes = {}
        valid = True
        for gate in GATES:
            gross, turn = sums[gate]
            if turn <= 0:
                valid = False
                break
            bes[gate] = gross / turn
        if valid:
            vals.append(bes["Unsafe"] - bes["Recovering"])
    if not vals:
        return {"events": int(len(keys)), "ci95": [None, None], "median": None}
    q = np.quantile(vals, [0.025, 0.5, 0.975])
    return {"events": int(len(keys)), "median": float(q[1]), "ci95": [float(q[0]), float(q[2])], "draws": len(vals)}


def run(root: Path, out: Path) -> dict:
    state_mod = load_state_module(root)
    decision_frames = []
    event_frames = []
    for year in YEARS:
        for symbol in SYMBOLS:
            native = load_year(root, symbol, year)
            panel = state_mod.build_panel(native, symbol)
            d, e = build_episode_decisions(panel, year)
            if len(d): decision_frames.append(d)
            if len(e): event_frames.append(e)
    decisions = pd.concat(decision_frames, ignore_index=True)
    event_index = pd.concat(event_frames, ignore_index=True).drop_duplicates("key")

    strategy_events = build_strategy_events(decisions)
    opp_events = build_opportunity_events(decisions)

    strategy_year = summarize_strategy(strategy_events, ["symbol", "year", "state", "rule", "lookback_min"])
    strategy_pool = summarize_strategy(strategy_events[strategy_events.year <= 2025], ["symbol", "state", "rule", "lookback_min"])
    strategy_2026 = summarize_strategy(strategy_events[strategy_events.year == 2026], ["symbol", "state", "rule", "lookback_min"])

    opp_year = summarize_opportunity(opp_events, ["symbol", "year", "state", "horizon_min"])
    opp_pool = summarize_opportunity(opp_events[opp_events.year <= 2025], ["symbol", "state", "horizon_min"])
    opp_2026 = summarize_opportunity(opp_events[opp_events.year == 2026], ["symbol", "state", "horizon_min"])

    move = state_movement_summary(decisions)
    boot = []
    for symbol in SYMBOLS:
        for rule in RULES:
            for h in LOOKBACKS:
                q = bootstrap_be_delta(strategy_events, symbol, rule, h)
                boot.append({"symbol": symbol, "rule": rule, "lookback_min": h, **q})
    boot = pd.DataFrame(boot)

    out.mkdir(parents=True, exist_ok=True)
    decisions.to_csv(out / "decision_panel.csv.gz", index=False, compression="gzip")
    event_index.to_csv(out / "event_index.csv", index=False)
    strategy_events.to_csv(out / "strategy_event_aggregates.csv", index=False)
    strategy_year.to_csv(out / "strategy_by_year.csv", index=False)
    strategy_pool.to_csv(out / "strategy_pool_2021_2025.csv", index=False)
    strategy_2026.to_csv(out / "strategy_replay_2026.csv", index=False)
    opp_events.to_csv(out / "opportunity_event_aggregates.csv", index=False)
    opp_year.to_csv(out / "opportunity_by_year.csv", index=False)
    opp_pool.to_csv(out / "opportunity_pool_2021_2025.csv", index=False)
    opp_2026.to_csv(out / "opportunity_replay_2026.csv", index=False)
    move.to_csv(out / "state_next_minute_movement.csv", index=False)
    boot.to_csv(out / "bootstrap_unsafe_minus_recovering_be.csv", index=False)

    summary = {
        "schema": "state_conditioned_frequency_economics_v1",
        "events_by_year_symbol": event_index.groupby(["symbol", event_index.day.astype(str).str[:4]]).size().rename("events").reset_index().to_dict("records"),
        "decision_rows": int(len(decisions)),
        "event_count": int(event_index.key.nunique()),
        "lookbacks": list(LOOKBACKS),
        "rules": list(RULES),
        "friction_scenarios_one_way_bp": list(COSTS),
        "interpretation_guardrails": [
            "2021-2025 consumed exploratory history",
            "2026 already-opened consistency replay only",
            "index-log-return abstraction, not tradable-carrier fill simulation",
            "opportunity ceiling is perfect-direction non-tradable upper bound",
            "full frequency surface retained; no best-frequency selection",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    summary = run(Path(args.repo_root).resolve(), Path(args.out))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
