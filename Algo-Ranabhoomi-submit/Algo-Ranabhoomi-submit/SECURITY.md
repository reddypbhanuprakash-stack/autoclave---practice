# The evaluation boundary

This file describes what the harness guarantees and what it relies on. It
ships with every contestant bundle.

## What your code can and cannot do

- **Your solver runs in a child process.** The parent process owns the clock,
  the validator, the scores and the kill switch. Nothing your solver does
  inside `solve()` can change how a candidate is validated or timed.
- **The only channel back is `submit_candidate`.** Candidates travel as JSON
  bytes, capped at 4 MB per message, and are never unpickled. Anything that is
  not JSON (sets, NaN, custom objects) is rejected with a reason.
- **The cost is computed by `validator.py` in the parent**, from the parent's
  own copy of the instance. Mutating the instance you receive has no effect
  on your score; the parent re-checks its copy's digest after every run.
- **Time is measured after validation.** A candidate counts toward a
  checkpoint only if its validation finished by that checkpoint.
- **Budgets are enforced by killing the process group.** Candidates after
  `budget x 1.05` are rejected; at `budget x 1.05 + 2 s` your process and
  everything it started are killed and the run is marked `overrun`. Earlier
  valid candidates are kept.
- **Limits:** 20,000 submissions per instance; 2 GB of address space where
  the platform supports `RLIMIT_AS`.
- **The adapter loader** accepts only a concrete class defined in the module
  you name (`module:Class`). Abstract bases, re-exported names and anything
  under `private/` are refused.

## What is not in your bundle

- The reference solver, the private suite, private anchors and the redraw
  tooling live under `private/` in the organizer's tree and never ship.
  `package_public.py` refuses to build a bundle that contains them, that
  imports from `private/`, or whose `data.py` contains search code.
- `data.py` builds each instance from one stored draw. It holds no witness
  plan, no reference cost and no search that could beat the baseline.
- `public_reference.json` (public-suite anchors) ships so `self_check.py` and
  `run.py` can score you; private-suite anchors do not.

## Judging

The private suite is judged in a separate, network-less container per
submission, on an otherwise idle machine, with one run per instance at the
published budgets. Scores from your own machine are indicative only.

## Reporting a problem

If you find a way to influence your score other than by submitting better
plans, tell the organizers. Finding and reporting it is worth more than using
it, and using it is grounds for disqualification.
