import _paths  # noqa: F401

from benchkit.cli import run_main

if __name__ == "__main__":
    import metrics
    raise SystemExit(run_main(metrics.BENCH))
