"""The interface every Autoclave Queue solver implements, plus helpers.

A plan is {"order": [b, b, ...]}: a permutation of all batch ids.
"""

from abc import ABC, abstractmethod

import data


class Solver(ABC):
    @abstractmethod
    def solve(self, instance, submit_candidate):
        """Call submit_candidate(plan) any number of times; each call returns a receipt
        (accepted, reason, cost, best, elapsed_s, remaining_s). The return value is one
        more candidate."""


def simulate(instance, order):
    """(starts, finishes), each a list indexed by batch id, exactly as the evaluator schedules."""
    return data.simulate(instance, order)


def cost_of(instance, order) -> int:
    """The evaluator's cost of an order: 4 * makespan + weighted tardiness."""
    return data.cost_of(instance, order)
