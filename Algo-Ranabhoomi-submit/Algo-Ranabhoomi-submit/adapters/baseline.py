"""Baseline: earliest due date, then adjacent-swap descent, with 3 restarts from
perturbed orders; the best order found is kept."""

from adapter import Solver, cost_of
from benchkit.rng import Rng, derive_seed

RESTARTS = 3
SAFETY_S = 0.2


def descend(instance, order):
    """Swap neighbours while any swap lowers the cost (first improvement)."""
    order = list(order)
    cost = cost_of(instance, order)
    improved = True
    while improved:
        improved = False
        for i in range(len(order) - 1):
            order[i], order[i + 1] = order[i + 1], order[i]
            c = cost_of(instance, order)
            if c < cost:
                cost, improved = c, True
            else:
                order[i], order[i + 1] = order[i + 1], order[i]
    return order, cost


class BaselineSolver(Solver):
    def solve(self, instance, submit_candidate):
        rng = Rng(derive_seed("autoclave-baseline", instance.digest))
        n = instance.size
        edd = sorted(range(n), key=lambda b: (instance.due[b], b))
        best, best_cost = descend(instance, edd)
        receipt = submit_candidate({"order": best})
        for _ in range(RESTARTS):
            if receipt["remaining_s"] < SAFETY_S:
                break
            start = list(best)
            for _ in range(max(2, n // 6)):  # a few random short-range swaps
                i = rng.below(n)
                j = min(n - 1, i + rng.between(1, 4))
                start[i], start[j] = start[j], start[i]
            order, cost = descend(instance, start)
            if cost < best_cost:
                best, best_cost = order, cost
                receipt = submit_candidate({"order": best})
        return {"order": best}
