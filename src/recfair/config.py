"""Configuration helpers for local synthetic recommender experiments."""

from __future__ import annotations

from pathlib import Path
import random
import numpy as np


def set_seed(seed: int) -> None:
    """Set deterministic random seeds."""
    random.seed(seed)
    np.random.seed(seed)


def ensure_output_dirs(base: str | Path = "outputs") -> dict[str, Path]:
    """Create and return standard output directories."""
    root = Path(base)
    dirs = {
        "root": root,
        "results": root / "results",
        "reports": root / "reports",
        "figures": root / "figures",
        "audit": root / "audit",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs
