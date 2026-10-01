"""Feasibility and canonical cost for Autoclave Queue.

cost = 4 * makespan + sum of weight * max(0, finish - due), on the evaluator's
schedule (data.cost_of): start = max(previous finish + setup, release).
"""

from data import cost_of


def validate(instance, candidate):
    if not isinstance(candidate, dict):
        return None, "candidate must be a dict"
    order = candidate.get("order")
    if not isinstance(order, list):
        return None, "'order' must be a list of batch ids"
    n = instance.size
    if len(order) != n:  # size check before any per-batch work
        return None, f"'order' must list all {n} batches exactly once, got {len(order)} ids"
    seen = bytearray(n)
    for b in order:
        if type(b) is not int or not 0 <= b < n:
            return None, f"batch id {b!r} is not an integer in 0..{n - 1}"
        if seen[b]:
            return None, f"batch {b} appears twice"
        seen[b] = 1
    return cost_of(instance, order), None
