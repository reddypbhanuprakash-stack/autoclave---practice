"""Autoclave Queue: one machine, sequence-dependent family setups, releases,
weighted tardiness.

A sequence of family runs is scheduled first; releases are drawn at or before
its start times and due dates around its finish times, so that sequence is a
known plan and tardiness is controllable. Batch ids are then
shuffled. Integer-only and deterministic. Every permutation is feasible.
"""

from dataclasses import dataclass
from types import MappingProxyType

from benchkit import SuiteEntry, freeze_profile
from benchkit.rng import Rng, derive_seed, digest_ints

SCHEMA_VERSION = 1
MAKESPAN_WEIGHT = 4

# Setups and slack are in percent of the mean processing time.
STANDARD = {"family": "standard", "shifted": False, "families": 4,
            "setup_lo_pct": 6, "setup_hi_pct": 16, "release": "early",
            "slack_lo_pct": -400, "slack_hi_pct": 300, "run_lo": 3, "run_hi": 8}
TIGHT = {"family": "tight-heavy", "shifted": True, "families": 6,
         "setup_lo_pct": 12, "setup_hi_pct": 30, "release": "staggered",
         "slack_lo_pct": -400, "slack_hi_pct": 100, "run_lo": 2, "run_hi": 6}


@dataclass(frozen=True)
class Instance:
    name: str
    profile: MappingProxyType
    size: int          # number of batches
    digest: str
    proc: tuple        # processing time p
    release: tuple     # release time r
    due: tuple         # due time d
    weight: tuple      # tardiness weight w (1..5)
    fam: tuple         # family of each batch
    setup: tuple       # setup[f][g]: changeover from family f to g (0 on the diagonal)


def compute_digest(instance) -> str:
    return digest_ints((instance.size, len(instance.setup), *instance.proc, *instance.release,
                        *instance.due, *instance.weight, *instance.fam,
                        *(x for row in instance.setup for x in row)), instance.profile)


def simulate(instance, order):
    """(starts, finishes), each indexed by batch id. The machine never skips ahead:
    start = max(previous finish + setup, release); the first batch starts at its release."""
    p, r, f, S = instance.proc, instance.release, instance.fam, instance.setup
    starts, finishes = [0] * instance.size, [0] * instance.size
    t = prev = None
    for b in order:
        s = r[b] if prev is None else max(t + S[prev][f[b]], r[b])
        t = s + p[b]
        starts[b], finishes[b] = s, t
        prev = f[b]
    return starts, finishes


def cost_of(instance, order) -> int:
    """MAKESPAN_WEIGHT * makespan + sum of weight * lateness (the canonical cost)."""
    p, r, d, w, f, S = (instance.proc, instance.release, instance.due, instance.weight,
                        instance.fam, instance.setup)
    t = prev = None
    tardy = 0
    for b in order:
        t = (r[b] if prev is None else max(t + S[prev][f[b]], r[b])) + p[b]
        if t > d[b]:
            tardy += w[b] * (t - d[b])
        prev = f[b]
    return MAKESPAN_WEIGHT * t + tardy


def draw(seed, profile):
    """One draw: (instance fields, the family-run sequence it was scheduled from)."""
    profile = freeze_profile(profile)
    rng = Rng(derive_seed("autoclave", SCHEMA_VERSION, seed, profile["attempt"]))
    n, F = profile["n"], profile["families"]
    proc = [rng.between(10, 60) for _ in range(n)]
    weight = [rng.between(1, 5) for _ in range(n)]
    mean_p = sum(proc) // n
    lo, hi = mean_p * profile["setup_lo_pct"] // 100, mean_p * profile["setup_hi_pct"] // 100
    setup = tuple(tuple(0 if a == b else rng.between(lo, hi) for b in range(F)) for a in range(F))

    # The construction sequence: families in runs, never the same family twice in a row.
    fam, last = [], None
    while len(fam) < n:
        g = rng.below(F)
        if g == last:
            continue
        fam.extend([g] * min(rng.between(profile["run_lo"], profile["run_hi"]), n - len(fam)))
        last = g

    # Schedule that sequence with no releases, then draw releases at or before its starts,
    # so its schedule is unchanged by them.
    starts, finishes, t = [], [], None
    for i in range(n):
        s = 0 if i == 0 else t + setup[fam[i - 1]][fam[i]]
        t = s + proc[i]
        starts.append(s)
        finishes.append(t)
    if profile["release"] == "staggered":
        release = [max(0, s - rng.between(0, 4 * mean_p)) for s in starts]
    else:
        release = [min(s, rng.between(0, 3 * mean_p)) for s in starts]
    due = [max(proc[i], finishes[i] + mean_p * rng.between(profile["slack_lo_pct"],
                                                             profile["slack_hi_pct"]) // 100)
           for i in range(n)]

    ids = list(range(n))
    rng.shuffle(ids)  # sequence position ids[k] becomes batch k
    pos_of = {old: k for k, old in enumerate(ids)}
    sequence = [pos_of[i] for i in range(n)]
    pick = lambda xs: tuple(xs[old] for old in ids)  # noqa: E731
    fields = dict(profile=profile, size=n, proc=pick(proc), release=pick(release), due=pick(due),
                  weight=pick(weight), fam=pick(fam), setup=setup)
    return fields, sequence


def make_instance(seed, profile, name) -> Instance:
    fields, _ = draw(seed, profile)
    return Instance(name=name, digest=compute_digest(Instance(name=name, digest="", **fields)), **fields)


def _entry(name, seed, family, n, attempt):
    return SuiteEntry(name, seed, {**family, "n": n, "attempt": attempt})


PUBLIC_SUITE = (
    _entry("autoclave-01", 3101, STANDARD, 30, 9),
    _entry("autoclave-02", 3102, STANDARD, 50, 24),
    _entry("autoclave-03", 3103, STANDARD, 70, 9),
    _entry("autoclave-04", 3104, STANDARD, 90, 79),
    _entry("autoclave-05", 3105, TIGHT, 40, 0),
    _entry("autoclave-06", 3106, TIGHT, 80, 12),
)
SELF_CHECK_NAMES = ("autoclave-01", "autoclave-05")


def budget_for(instance) -> float:
    return 5.0
