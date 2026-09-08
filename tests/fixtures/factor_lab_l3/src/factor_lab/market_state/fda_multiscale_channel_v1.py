"""Hermetic L3 multiscale-channel fixture used only by loader tests."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FDAMultiscaleChannelSpec:
    mode: str
    windows: tuple[int, ...]


def build_fda_multiscale_channel(close, spec: FDAMultiscaleChannelSpec) -> pd.DataFrame:
    """Small causal stand-in for testing loader isolation and prefix invariance.

    Every output row depends only on the close prefix ending at that row.  The
    fixture is deliberately not a copy of production factor_lab logic.
    """
    s = pd.Series(close, copy=True, dtype=float)
    if spec.mode != "opposite_rail":
        raise ValueError(spec.mode)
    if not spec.windows:
        raise ValueError("windows required")
    r = np.log(s).diff()
    out = pd.DataFrame(index=s.index)
    for window in spec.windows:
        w = int(window)
        if w <= 1:
            raise ValueError(window)
        out[f"mean_{w}"] = r.rolling(w, min_periods=w).mean()
        out[f"sigma_{w}"] = r.rolling(w, min_periods=w).std(ddof=0)
    fast = out[f"mean_{int(spec.windows[0])}"]
    slow = out[f"mean_{int(spec.windows[-1])}"]
    out["decision_position_for_next_bar"] = np.sign(fast - slow).fillna(0).astype(np.int8)
    return out
