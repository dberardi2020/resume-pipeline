"""Search over the layout design space.

Browsing 5,040 layouts at random is not exploration, it is a slot machine — you see
eighteen unrelated points and learn nothing that improves the next eighteen. What
makes it exploration is *steering*: express a preference, and have the next batch
respond to it.

That requires two things a flat list does not have — a notion of how far apart two
layouts are, and a sampler that uses it. Both live here, kept free of rendering and
IO so they can be reasoned about and tested on their own.

The space is a product of independent categorical axes, so distance is Hamming:
the number of axes on which two specs disagree, 0-6. Crude, but it matches how the
choices actually behave — swapping a palette changes one thing about a layout, and
the metric should say exactly that.
"""
from __future__ import annotations

import random
from dataclasses import replace

from .compose import DENSITIES, HEADERS, PALETTES, PROMOS, SKILLS, TYPEFACES, Spec

# Every axis, as (attribute, values). Order is stable so `axis_values` and
# distance stay consistent across runs.
AXES: list[tuple[str, list]] = [
    ("palette", list(range(len(PALETTES)))),
    ("typeface", list(range(len(TYPEFACES)))),
    ("header", list(HEADERS)),
    ("skills", list(SKILLS)),
    ("promo", list(PROMOS)),
    ("density", list(range(len(DENSITIES)))),
]

TOTAL = 1
for _, _values in AXES:
    TOTAL *= len(_values)


def distance(a: Spec, b: Spec) -> int:
    """Number of axes on which two specs differ (0 = identical, 6 = nothing shared)."""
    return sum(1 for attr, _ in AXES if getattr(a, attr) != getattr(b, attr))


def neighbours(spec: Spec, radius: int = 1) -> list[Spec]:
    """Every spec within `radius` axis-changes of `spec`, excluding itself."""
    out: set[Spec] = set()
    frontier = {spec}
    for _ in range(max(1, radius)):
        nxt: set[Spec] = set()
        for current in frontier:
            for attr, values in AXES:
                for value in values:
                    if value == getattr(current, attr):
                        continue
                    nxt.add(replace(current, **{attr: value}))
        out |= nxt
        frontier = nxt
    out.discard(spec)
    return sorted(out, key=lambda s: s.name)


def diverse(count: int, seed: int = 0, exclude: set[str] | None = None) -> list[Spec]:
    """A spread-out sample, via greedy farthest-point selection.

    A uniform random draw clusters — with six axes and a small sample you routinely
    get three layouts that differ only by palette, which wastes the batch. Greedy
    farthest-point picks each next spec to maximise its minimum distance to those
    already chosen, so a batch of twelve actually covers the space.
    """
    exclude = exclude or set()
    rng = random.Random(seed)
    pool = [s for s in _all() if s.name not in exclude]
    if not pool:
        return []
    rng.shuffle(pool)
    # A candidate window keeps this near-linear; scoring all 5,040 each round is
    # needless when the pool is already shuffled.
    window = min(len(pool), max(240, count * 40))
    pool = pool[:window]

    chosen = [pool.pop(0)]
    while pool and len(chosen) < count:
        best_i, best_score = 0, -1
        for i, cand in enumerate(pool):
            score = min(distance(cand, c) for c in chosen)
            if score > best_score:
                best_i, best_score = i, score
                if score == len(AXES):
                    break
        chosen.append(pool.pop(best_i))
    return chosen


def steer(favourites: list[Spec], rejects: list[Spec], count: int,
          seed: int = 0, exclude: set[str] | None = None) -> list[Spec]:
    """Sample near what was liked and away from what was not.

    With no signal yet, fall back to a diverse sweep. Otherwise draw from the
    union of the favourites' neighbourhoods, scoring each candidate by how close
    it sits to a favourite and how far from a reject, then take a spread across
    the winners so the batch does not collapse onto one favourite's variations.
    """
    exclude = set(exclude or set())
    exclude |= {s.name for s in favourites} | {s.name for s in rejects}

    if not favourites:
        return diverse(count, seed=seed, exclude=exclude)

    rng = random.Random(seed)
    pool: dict[str, Spec] = {}
    for fav in favourites:
        for cand in neighbours(fav, radius=2):
            if cand.name not in exclude:
                pool[cand.name] = cand
    if not pool:
        return diverse(count, seed=seed, exclude=exclude)

    def score(spec: Spec) -> float:
        near = min(distance(spec, f) for f in favourites)
        away = min((distance(spec, r) for r in rejects), default=len(AXES))
        # Close to a favourite is good; close to a reject is bad but weighted
        # lower, since a reject usually means one bad axis rather than a bad region.
        return -near + 0.5 * min(away, 3) + rng.random() * 0.4

    ranked = sorted(pool.values(), key=score, reverse=True)
    # Take a diverse slice of the top candidates rather than the top N, which
    # would be near-duplicates of one another.
    head = ranked[: max(count * 4, count)]
    out = [head[0]]
    for cand in head[1:]:
        if len(out) >= count:
            break
        if min(distance(cand, c) for c in out) >= 1:
            out.append(cand)
    return out[:count]


def _all() -> list[Spec]:
    from .compose import all_specs
    return all_specs()


def parse(name: str) -> Spec | None:
    """Recover a Spec from its stable name. Returns None if it does not parse."""
    for spec in _all():
        if spec.name == name:
            return spec
    return None
