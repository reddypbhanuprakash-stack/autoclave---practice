"""Puts this bench and the nearest benchkit/ on sys.path."""

import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
ROOT = next(p for p in (BENCH_DIR, *BENCH_DIR.parents) if (p / "benchkit").is_dir())

for _p in (str(ROOT), str(BENCH_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
