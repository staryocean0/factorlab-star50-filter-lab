"""Produce a deterministic synthetic prototype receipt without market access."""

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from star50_filter.slope_union import (  # noqa: E402
    SlopeUnionConfig,
    build_signals,
    slope_covariance,
    threshold_table,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_bars() -> pd.DataFrame:
    times = []
    for day in pd.bdate_range("2021-01-04", periods=12):
        for start, end in [("09:31", "11:30"), ("13:01", "15:00")]:
            times.extend(pd.date_range(f"{day.date()} {start}", f"{day.date()} {end}", freq="min", tz="Asia/Shanghai"))
    t = np.arange(len(times))
    rng = np.random.default_rng(7101)
    x = 0.008 * np.sin(2 * np.pi * t / 360) + np.cumsum(rng.normal(0, 0.0003, len(t)))
    return pd.DataFrame({"timestamp": times, "trading_minute": t, "close": 1000 * np.exp(x)})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new output directory")
    args = parser.parse_args()
    contract = json.loads((ROOT / "docs/research/half_day_slope_union_v1/contract.json").read_text())
    config = SlopeUnionConfig(**contract["config"])
    assert contract["sample_minutes"] == 1 and contract["lookbacks"] == [1, 2, 3, 4, 5]
    assert contract["production_authority"] is False
    bars = synthetic_bars()
    output = build_signals(bars, config)
    pd.testing.assert_frame_equal(output, build_signals(bars, config))
    pd.testing.assert_frame_equal(output.iloc[:1000], build_signals(bars.iloc[:1000], config))
    mirrored = bars.copy()
    mirrored["close"] = 1e6 / bars.close
    np.testing.assert_array_equal(output.target_at_close, -build_signals(mirrored, config).target_at_close)
    table = threshold_table(config)
    covariance = slope_covariance(config)
    rng = np.random.default_rng(98241)
    draws = rng.multivariate_normal(np.zeros(5), covariance, size=100_000)
    null_rates = {}
    for name, alpha in [("entry", config.entry_alpha), ("exit", config.exit_alpha)]:
        rate = float((abs(draws) > table[name + "_per_sigma"].to_numpy()).any(axis=1).mean())
        assert rate <= alpha + 5 * np.sqrt(alpha * (1 - alpha) / len(draws))
        null_rates[name] = rate
    args.output.mkdir(parents=True, exist_ok=False)
    table.to_csv(args.output / "thresholds.csv", index=False)
    output.to_parquet(args.output / "synthetic_signals.parquet", index=False)
    sources = [
        "src/star50_filter/slope_union.py",
        "scripts/run_half_day_slope_union_v1.py",
        "tests/test_slope_union.py",
        "docs/research/half_day_slope_union_v1/whitepaper.md",
        "docs/research/half_day_slope_union_v1/contract.json",
        "docs/research/half_day_slope_union_v1/workflow.md",
    ]
    receipt = {
        "status": "synthetic_prototype_verified_economics_not_evaluated",
        "config": asdict(config),
        "config_sha256": config.fingerprint,
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__},
        "checks": {"prefix": True, "deterministic_repeat": True, "mirror": True, "known_sigma_gaussian_single_time_union_bound": True},
        "known_sigma_null_draws": len(draws),
        "known_sigma_null_rates": null_rates,
        "synthetic_rows": len(output),
        "ready_rows": int(output.ready.sum()),
        "target_changes": int(output.target_at_close.ne(output.prior_target).sum()),
        "market_rows_read": 0,
        "account_execution": False,
        "production_authority": False,
        "source_sha256": {p: sha(ROOT / p) for p in sources},
        "artifacts": {p.name: sha(p) for p in sorted(args.output.iterdir())},
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(table.to_string(index=False))
    print(json.dumps({k: v for k, v in receipt.items() if k not in {"source_sha256", "artifacts"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
