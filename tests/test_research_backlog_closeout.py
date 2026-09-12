from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_research_backlog_closeout_authority() -> None:
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, str(root / "scripts" / "validate_research_backlog_closeout.py")],
        cwd=root,
        check=True,
    )
