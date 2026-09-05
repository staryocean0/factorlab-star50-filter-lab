"""Next-open long/short account from a position series."""
from __future__ import annotations
import numpy as np

def execute_next_open(signal_pos: np.ndarray, open_px: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    exec_pos = np.zeros_like(signal_pos)
    exec_pos[2:] = signal_pos[:-2]
    fwd = np.zeros(len(open_px))
    fwd[1:] = np.log(open_px[1:] / np.clip(open_px[:-1], 1e-12, None))
    return exec_pos, exec_pos * fwd
