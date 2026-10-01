import _paths  # noqa: F401

from benchkit.cli import self_check_main

if __name__ == "__main__":
    import metrics
    raise SystemExit(self_check_main(metrics.BENCH))
