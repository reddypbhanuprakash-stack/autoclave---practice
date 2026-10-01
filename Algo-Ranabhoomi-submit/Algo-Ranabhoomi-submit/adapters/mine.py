"""Competitive solver for the Autoclave Queue benchmark.

Strategy:
1. Submit an EDD order immediately so an early checkpoint is covered.
2. Improve it with adjacent-swap descent.
3. Explore insertion moves (the benchmark hint explicitly points to this).
4. Use a few deterministic alternative starts and randomized perturbations.
5. Keep submitting only genuine improvements and stop safely before the 5 s limit.
"""

import random
import time

from adapter import Solver, cost_of


SAFETY_S = 0.20
MAX_INSERTION_MOVES = 60


def edd_order(instance):
    return sorted(range(instance.size), key=lambda b: (instance.due[b], b))


def weighted_edd_order(instance, alpha):
    mean_p = sum(instance.proc) / instance.size
    return sorted(
        range(instance.size),
        key=lambda b: (instance.due[b] - alpha * instance.weight[b] * mean_p, b),
    )


def atc_order(instance, k=1.0):
    """Construct an ATC-like schedule, respecting the evaluator's no-skip rule."""
    n = instance.size
    p, r, d, w = instance.proc, instance.release, instance.due, instance.weight
    fam, setup = instance.fam, instance.setup
    avg_p = sum(p) / n

    remaining = set(range(n))
    order = []
    t = 0
    prev_family = None

    while remaining:
        available = [b for b in remaining if r[b] <= t]
        candidates = available if available else list(remaining)

        def priority(b):
            change = 0 if prev_family is None else setup[prev_family][fam[b]]
            effective = p[b] + change
            slack = d[b] - (t + change + p[b])
            urgency = max(slack, 0) / (k * avg_p)
            return (w[b] / effective) * pow(2.718281828, -urgency)

        b = max(candidates, key=priority)

        change = 0 if prev_family is None else setup[prev_family][fam[b]]
        t = max(t + change, r[b]) + p[b]
        order.append(b)
        remaining.remove(b)
        prev_family = fam[b]

    return order


def adjacent_descent(instance, order):
    """First-improvement adjacent-swap descent."""
    order = list(order)
    current = cost_of(instance, order)
    n = len(order)

    while True:
        improved = False
        for i in range(n - 1):
            order[i], order[i + 1] = order[i + 1], order[i]
            candidate = cost_of(instance, order)
            if candidate < current:
                current = candidate
                improved = True
            else:
                order[i], order[i + 1] = order[i + 1], order[i]
        if not improved:
            return order, current


def insertion_descent(instance, order, current_cost, deadline, max_moves=MAX_INSERTION_MOVES):
    """First-improvement insertion descent.

    One batch is removed and tried at every other position. The first improving
    move is kept, then the scan restarts. The order is restored if the time limit
    is reached while a batch is temporarily removed.
    """
    order = list(order)
    n = len(order)
    moves = 0

    while moves < max_moves and time.monotonic() < deadline:
        improved = False

        for i in range(n):
            if time.monotonic() >= deadline:
                return order, current_cost

            batch = order.pop(i)

            for j in range(n):
                if j == i:
                    continue

                order.insert(j, batch)
                candidate_cost = cost_of(instance, order)

                if candidate_cost < current_cost:
                    current_cost = candidate_cost
                    moves += 1
                    improved = True
                    break

                order.pop(j)

                if time.monotonic() >= deadline:
                    order.insert(i, batch)
                    return order, current_cost

            if improved:
                break

            order.insert(i, batch)

        if not improved:
            break

    return order, current_cost


class MySolver(Solver):
    def solve(self, instance, submit_candidate):
        # Deterministic per instance, but independent from the organizer's RNG.
        seed = int(instance.digest, 16)
        rng = random.Random(seed)

        # ---- Early checkpoint: submit something valid immediately. ----
        best = edd_order(instance)
        best_cost = cost_of(instance, best)
        receipt = submit_candidate({"order": best})

        # Keep a safety margin so the parent never kills us while validating.
        remaining = receipt.get("remaining_s", 5.0)
        deadline = time.monotonic() + max(0.0, remaining - SAFETY_S)

        if deadline <= time.monotonic():
            return {"order": best}

        # ---- Cheap improvement: reproduce the baseline's useful idea. ----
        candidate, candidate_cost = adjacent_descent(instance, best)
        if candidate_cost < best_cost:
            best, best_cost = candidate, candidate_cost
            receipt = submit_candidate({"order": best})
            deadline = time.monotonic() + max(
                0.0, receipt.get("remaining_s", 0.0) - SAFETY_S
            )

        if deadline <= time.monotonic():
            return {"order": best}

        # ---- Alternative starting points. ----
        starts = [
            weighted_edd_order(instance, 0.5),
            weighted_edd_order(instance, 1.0),
            atc_order(instance, 0.5),
            atc_order(instance, 1.0),
        ]

        for start in starts:
            if time.monotonic() >= deadline:
                break

            c = cost_of(instance, start)
            if c >= best_cost:
                continue

            start, c = adjacent_descent(instance, start)
            if c < best_cost:
                best, best_cost = start, c
                receipt = submit_candidate({"order": best})
                deadline = time.monotonic() + max(
                    0.0, receipt.get("remaining_s", 0.0) - SAFETY_S
                )

        # ---- Main search: direct insertion descent first, then perturb + insertion. ----
        n = instance.size

        best, best_cost = insertion_descent(
            instance, best, best_cost, deadline, max_moves=MAX_INSERTION_MOVES
        )
        if time.monotonic() < deadline:
            receipt = submit_candidate({"order": best})
            deadline = time.monotonic() + max(
                0.0, receipt.get("remaining_s", 0.0) - SAFETY_S
            )

        while time.monotonic() < deadline:
            candidate = list(best)

            # Mix short random swaps and remove/reinsert perturbations.
            if rng.random() < 0.55:
                for _ in range(rng.randint(2, max(2, n // 12))):
                    i = rng.randrange(n)
                    j = rng.randrange(n)
                    candidate[i], candidate[j] = candidate[j], candidate[i]
            else:
                for _ in range(rng.randint(2, max(2, n // 10))):
                    i = rng.randrange(n)
                    batch = candidate.pop(i)
                    j = rng.randrange(len(candidate) + 1)
                    candidate.insert(j, batch)

            candidate_cost = cost_of(instance, candidate)

            # Don't spend insertion-search time on an obviously poor start.
            if candidate_cost >= best_cost * 1.10:
                continue

            candidate, candidate_cost = insertion_descent(
                instance,
                candidate,
                candidate_cost,
                deadline,
            )

            if candidate_cost < best_cost:
                best, best_cost = candidate, candidate_cost

                # Send improvements as they appear. Earlier valid candidates
                # remain safe even if the final search reaches the time limit.
                if time.monotonic() < deadline:
                    receipt = submit_candidate({"order": best})
                    deadline = time.monotonic() + max(
                        0.0, receipt.get("remaining_s", 0.0) - SAFETY_S
                    )

        return {"order": best}
