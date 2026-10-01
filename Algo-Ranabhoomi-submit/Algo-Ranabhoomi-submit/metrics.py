"""Bench config for Autoclave Queue."""

import _paths  # noqa: F401

import data
import validator
from benchkit import BenchConfig

BENCH = BenchConfig(
    name="autoclave",
    bench_dir=_paths.BENCH_DIR,
    data=data,
    validate=validator.validate,
    probe="private.probes.textbook:TextbookProbe",
    shift_markers=lambda p: "tight due dates, heavy setups, staggered releases" if p["shifted"] else "",
)
