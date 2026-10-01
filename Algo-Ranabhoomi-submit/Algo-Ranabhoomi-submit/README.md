# Autoclave Queue

Sequence sterilisation batches on one autoclave with changeovers, release times and deadlines.

## The scenario

Ines Carvalho runs the sterile services room at São Brás General. One
autoclave serves every ward. Switching between instrument families (say,
orthopaedic trays to endoscopes) takes a changeover, trays arrive through the
day, and each ward needs its trays back by a certain time, some wards more
urgently than others.

## The problem, precisely

- **Batches:** `instance.size` batches, ids `0..n-1`, with processing time
  `instance.proc[b]`, release time `instance.release[b]`, due time
  `instance.due[b]`, weight `instance.weight[b]` (1..5) and family
  `instance.fam[b]`.
- **Setups:** `instance.setup[f][g]` is the changeover from family f to g
  (0 when f == g).
- **Plan:** `{"order": [b, b, ...]}`, a permutation of all batches.
- **Schedule (the evaluator's):** the first batch starts at its release;
  every later batch starts at `max(previous finish + setup, its release)`.
- **Cost:** `4 x makespan + sum of weight x max(0, finish - due)`.

## How you're scored

Your best valid cost is read at 5%, 20%, 50% and 100% of the 5-second budget
(weights 0.10, 0.20, 0.30, 0.40). At each checkpoint the cost is placed on a
curve through three anchors: the starter scores 0.25, the published baseline
0.50, the reference 1.00, linearly in between; beating the reference scores
1.00, no valid plan scores 0.

*Example:* baseline 7,363, reference 6,597 at a checkpoint. A cost of 6,980 is
halfway between them and scores 0.75 there.

Points: quality 70, robustness 20 (shifted instances, halved if one family is
strong and another weak), engineering 10.

## Your submission

```python
from adapter import Solver

class MySolver(Solver):
    def solve(self, instance, submit_candidate):
        receipt = submit_candidate({"order": [...]})
        return {"order": [...]}
```

Put it in `adapters/mine.py`, then:

```
python self_check.py --adapter adapters.mine:MySolver
python run.py --adapter adapters.mine:MySolver --out report.json
```

## The trap

Read this before you write anything: **the machine never skips ahead.** A
batch that is not yet released holds up everything behind it in your order,
even batches that were ready long ago.

## Baselines

| Anchor | Program | Score |
| --- | --- | --- |
| Starter | earliest due date first | 0.25 |
| Baseline | earliest due date, then neighbour swaps with 3 restarts | 0.50 |
| Reference | a stronger search, not published | 1.00 |

## Your head start

`adapters/starter.py` is a working solver. `adapter.py` gives you
`simulate(instance, order) -> (starts, finishes)` (lists indexed by batch id)
and `cost_of(instance, order)`, both exactly as the evaluator computes them.

## A hint

Swapping neighbours helps a little; try lifting one batch out and inserting it elsewhere.

## Instance families

| Family | Public | Private | What changes |
| --- | --- | --- | --- |
| standard | 4 | 4 | generous due dates, mild setups, early releases, 4 families |
| tight-heavy (shifted) | 2 | 4 | tight due dates, setups up to 30% of a mean batch, staggered releases, 6 families |

Sizes: 20 to 90 batches. The private suite uses unseen seeds.

## Files

`adapter.py`, `adapters/starter.py`, `adapters/baseline.py`, `data.py`,
`validator.py`, `self_check.py`, `run.py`, `public_reference.json`,
`benchkit/`, `SECURITY.md`.
