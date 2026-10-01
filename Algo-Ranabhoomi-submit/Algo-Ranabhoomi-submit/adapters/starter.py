"""Starter: earliest due date first."""

from adapter import Solver


class StarterSolver(Solver):
    def solve(self, instance, submit_candidate):
        return {"order": sorted(range(instance.size), key=lambda b: (instance.due[b], b))}
