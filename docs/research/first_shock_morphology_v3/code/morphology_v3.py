"""V3 event taxonomy audit. No refit, no trading, no 2026 reads.

Separates the original minute first-tail family into quiet/active/intermediate
pre-onset morphologies and adds a distinct high-range low-net round-trip family.
Existing V2 B1/B2 alarms are only diagnosed by subgroup; they are never refit.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
RESEARCH = HERE.parents[2]
sys.path.insert(0, str(RESEARCH / "first_shock_seconds_v2/code"))
sys.path.insert(0, str(RESEARCH / "first_shock_gate_v1/code"))
import seconds_v2 as v2
import first_shock_gate as g

SYMBOLS = ("000688.SH", "000852.SH")
YEARS = range(2021, 2026)


def _known(x):
    return np.isfinite(np.asarray(x, float)).all()


def minute_morphology(sample, minute: int):
    """Return hindsight morphology for one minute on a 15s endpoint grid.

    Precondition uses the five physical minutes strictly before event onset.
    Unknown support remains unknown. This classification is outcome-side only.
    """
    if minute < 6 or minute > 120:
        return {"support": False}
    r = np.asarray(sample["return_bp"], float)
    p = np.asarray(sample["price"], float)
    sidx = (minute - 1) * 4
    eidx = minute * 4
    pre_r = r[sidx - 19:sidx + 1]
    pre_p = p[sidx - 20:sidx + 1]
    cur_r = r[sidx + 1:eidx + 1]
    cur_p = p[sidx:eidx + 1]
    pre_ok = len(pre_r) == 20 and len(pre_p) == 21 and _known(pre_r) and _known(pre_p)
    cur_ok = len(cur_r) == 4 and len(cur_p) == 5 and _known(cur_r) and _known(cur_p)
    out = {"support": bool(pre_ok and cur_ok), "pre_support": bool(pre_ok), "minute_support": bool(cur_ok)}
    if not pre_ok:
        out.update({"pre5_abs_net_bp": None, "pre5_range_bp": None, "pre5_max_abs15_bp": None,
                    "quiet_pre": None, "active_pre": None})
    else:
        pre_net = abs(np.log(pre_p[-1] / pre_p[0]) * 1e4)
        pre_range = np.log(np.max(pre_p) / np.min(pre_p)) * 1e4
        pre_max = np.max(np.abs(pre_r))
        quiet = pre_net < 15 and pre_range < 30 and pre_max < 15
        active = pre_net >= 30 or pre_range >= 45 or pre_max >= 15
        out.update({"pre5_abs_net_bp": float(pre_net), "pre5_range_bp": float(pre_range),
                    "pre5_max_abs15_bp": float(pre_max), "quiet_pre": bool(quiet),
                    "active_pre": bool(active)})
    if not cur_ok:
        out.update({"minute_abs_net_bp": None, "minute_range_bp": None,
                    "minute_efficiency": None, "roundtrip": None})
    else:
        net = np.log(cur_p[-1] / cur_p[0]) * 1e4
        rng = np.log(np.max(cur_p) / np.min(cur_p)) * 1e4
        tv = np.sum(np.abs(cur_r))
        eff = abs(net) / tv if tv > 0 else 0.0
        roundtrip = rng >= 30 and abs(net) <= 10 and eff <= .25
        out.update({"minute_abs_net_bp": float(abs(net)), "minute_range_bp": float(rng),
                    "minute_efficiency": float(eff), "roundtrip": bool(roundtrip)})
    return out


def first_roundtrip(flags):
    """30 known prior minutes without a roundtrip; unknown never means quiet."""
    x = np.asarray(flags, object)
    out = np.full(len(x), np.nan)
    for j in range(30, len(x)):
        before = x[j-30:j]
        now = x[j]
        if now is None or any(v is None for v in before):
            continue
        out[j] = float(bool(now) and not any(bool(v) for v in before))
    return out


def taxonomy_symbol(root: Path, symbol: str, gap_limit: int):
    sys.path.insert(0, str(root / "src"))
    from star50_filter.cloud_market_data import load_market_data

    native = load_market_data(symbol, "1m", "2021-01-01", "2025-12-31", root=root)
    minute = g.minute_panel(native, symbol)
    feat = g.make_features(minute).reset_index(drop=True)
    records = []
    support_audit = []
    for year in YEARS:
        seconds, audit = v2.read_seconds(root, symbol, year)
        groups = {s: z for s, z in seconds.groupby("session", sort=False)}
        yr = feat[feat.year == year]
        for session, ix in yr.groupby("session", sort=False).groups.items():
            ix = np.asarray(ix)
            raw = groups.get(session)
            if raw is None:
                t = np.array([]); p = np.array([]); rr = np.array([], dtype=int)
            else:
                t = raw.second.to_numpy(float); p = raw.price.to_numpy(float); rr = raw.row_index.to_numpy()
            sample = v2.sample_session(t, p, rr, 15, gap_limit)
            round_flags = []
            morphs = []
            for minute_no in range(1, 121):
                m = minute_morphology(sample, minute_no)
                morphs.append(m)
                round_flags.append(m.get("roundtrip") if m.get("minute_support") else None)
            round_first = first_roundtrip(round_flags)
            for local, row_ix in enumerate(ix):
                row = feat.loc[row_ix]
                m = morphs[local]
                tail = bool(row["first"] == 1) if np.isfinite(row["first"]) else False
                if tail:
                    if m.get("quiet_pre") is True: tail_class = "quiet_first_tail"
                    elif m.get("active_pre") is True: tail_class = "active_continuation_tail"
                    elif m.get("pre_support") is True: tail_class = "intermediate_tail"
                    else: tail_class = "unknown_tail"
                else:
                    tail_class = None
                rf = bool(round_first[local] == 1) if np.isfinite(round_first[local]) else False
                if rf:
                    round_class = "quiet_roundtrip" if m.get("quiet_pre") is True else (
                        "active_roundtrip" if m.get("active_pre") is True else (
                        "intermediate_roundtrip" if m.get("pre_support") is True else "unknown_roundtrip"))
                else:
                    round_class = None
                if tail or rf:
                    records.append({"symbol": symbol, "year": year, "day": row.day,
                        "session": row.session, "minute": int(row.minute),
                        "tail_first": tail, "tail_class": tail_class,
                        "roundtrip_first": rf, "roundtrip_class": round_class,
                        "official_minute_return_bp": float(row.return_bp) if np.isfinite(row.return_bp) else None,
                        **m})
        audit["gap_limit_seconds"] = gap_limit
        support_audit.append(audit)
    return pd.DataFrame(records), support_audit


def alarm_hits(event_table: pd.DataFrame, replay_dir: Path):
    rows = []
    for symbol in SYMBOLS:
        for year in (2024, 2025):
            path = replay_dir / f"{symbol}_primary_joint_gap15_{year}_decisions.csv.gz"
            if not path.exists():
                continue
            d = pd.read_csv(path)
            events = event_table[(event_table.symbol == symbol) & (event_table.year == year)].copy()
            for family, class_col, select in [
                ("tail", "tail_class", events.tail_first.astype(bool)),
                ("roundtrip", "roundtrip_class", events.roundtrip_first.astype(bool)),
            ]:
                z = events.loc[select]
                for cls, zz in z.groupby(class_col, dropna=False):
                    for model in ("B1", "B2"):
                        for mode in ("quota", "frozen"):
                            warned = []
                            earliest = []
                            for _, e in zz.iterrows():
                                q = d[(d.session == e.session) & d.minute.between(max(1, e.minute-15), e.minute-2)]
                                alarm = q[f"{model}_{mode}"].astype(bool)
                                hit = bool(alarm.any())
                                warned.append(hit)
                                if hit:
                                    am = q.loc[alarm, "minute"].to_numpy(int)
                                    earliest.append(float(e.minute - 1 - am.min()))
                            rows.append({"symbol": symbol, "year": year, "family": family,
                                "event_class": cls, "model": model, "mode": mode,
                                "event_count": len(zz), "warned_count": int(sum(warned)),
                                "recall": float(np.mean(warned)) if warned else None,
                                "median_earliest_lead": float(np.median(earliest)) if earliest else None})
    return pd.DataFrame(rows)


def summarize(events: pd.DataFrame, hit_table: pd.DataFrame):
    taxonomy = []
    for symbol in SYMBOLS:
        e = events[events.symbol == symbol]
        for year in YEARS:
            y = e[e.year == year]
            tail = y[y.tail_first.astype(bool)]
            rnd = y[y.roundtrip_first.astype(bool)]
            taxonomy.append({"symbol": symbol, "year": year,
                "tail_events": len(tail),
                "quiet_first_tail": int((tail.tail_class == "quiet_first_tail").sum()),
                "active_continuation_tail": int((tail.tail_class == "active_continuation_tail").sum()),
                "intermediate_tail": int((tail.tail_class == "intermediate_tail").sum()),
                "unknown_tail": int((tail.tail_class == "unknown_tail").sum()),
                "roundtrip_first": len(rnd),
                "quiet_roundtrip": int((rnd.roundtrip_class == "quiet_roundtrip").sum()),
                "active_roundtrip": int((rnd.roundtrip_class == "active_roundtrip").sum()),
                "intermediate_roundtrip": int((rnd.roundtrip_class == "intermediate_roundtrip").sum()),
                "unknown_roundtrip": int((rnd.roundtrip_class == "unknown_roundtrip").sum())})
    tax = pd.DataFrame(taxonomy)
    train = tax[tax.year <= 2023].groupby("symbol").sum(numeric_only=True).reset_index()
    readiness = []
    for _, row in train.iterrows():
        for cls in ("quiet_first_tail", "roundtrip_first", "quiet_roundtrip"):
            n = int(row[cls])
            readiness.append({"symbol": row.symbol, "event_family": cls,
                              "independent_anchor_count_2021_2023": n,
                              "future_model_minimum": 20, "ready": n >= 20})
    return tax, pd.DataFrame(readiness), hit_table


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--v2-replay-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.repo_root.resolve(); out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("immutable nonempty output")
    out.mkdir(parents=True, exist_ok=True)

    all_primary = []; audits = {}; all_strict = []
    for symbol in SYMBOLS:
        p, a = taxonomy_symbol(root, symbol, 15); p["support_mode"] = "gap15"; all_primary.append(p); audits[symbol] = a
        s, _ = taxonomy_symbol(root, symbol, 3); s["support_mode"] = "gap3"; all_strict.append(s)
        print("MEASURED", symbol, "primary", len(p), "strict", len(s))
    primary = pd.concat(all_primary, ignore_index=True)
    strict = pd.concat(all_strict, ignore_index=True)
    hits = alarm_hits(primary, args.v2_replay_dir.resolve())
    tax, ready, hits = summarize(primary, hits)

    primary.to_csv(out / "event_taxonomy_gap15.csv", index=False)
    strict.to_csv(out / "event_taxonomy_gap3.csv", index=False)
    tax.to_csv(out / "taxonomy_counts.csv", index=False)
    ready.to_csv(out / "future_model_readiness.csv", index=False)
    hits.to_csv(out / "v2_alarm_hits_by_taxonomy.csv", index=False)
    g.write_json(out / "source_audit.json", audits)
    g.write_json(out / "summary.json", {
        "status": "completed descriptive taxonomy; no model refit",
        "taxonomy_counts": tax.to_dict("records"),
        "future_model_readiness": ready.to_dict("records"),
        "v2_alarm_diagnostic_rows": len(hits),
        "fresh_oos": False, "production_authority": False})
    print(tax.to_string(index=False))
    print(ready.to_string(index=False))


if __name__ == "__main__":
    main()
