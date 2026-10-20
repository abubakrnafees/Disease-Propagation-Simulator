"""Contact resolution and deterministic broad-phase candidate selection.

Cell width is the 16-pixel contact diameter. The grid tracks cell changes
caused by separation while yielding pairs in the same order as brute force.
"""
import math
from collections import deque

CONTACT_DISTANCE = 16


def brute_candidates(people):
    """Correct reference: every unordered pair, in population order."""
    for first in range(len(people)):
        for second in range(first + 1, len(people)):
            yield first, second


def grid_candidates(people):
    """Yield local pairs; update membership after the caller resolves each pair.

    Callers may move only the two yielded agents before resuming iteration.
    This makes the optimized engine match the sequential reference even when
    collision separation moves an agent into a different cell mid-update.
    """
    def cell(person):
        return math.floor(person.x / CONTACT_DISTANCE), math.floor(person.y / CONTACT_DISTANCE)

    cells = {}
    locations = []
    for index, person in enumerate(people):
        location = cell(person)
        locations.append(location)
        cells.setdefault(location, set()).add(index)

    def neighbors(index, after):
        x, y = locations[index]
        return deque(sorted(other for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      for other in cells.get((x + dx, y + dy), ()) if other > after))

    for first in range(len(people)):
        pending = neighbors(first, first)
        while pending:
            second = pending.popleft()
            yield first, second
            first_changed = False
            for index in (first, second):
                location = cell(people[index])
                if location != locations[index]:
                    cells[locations[index]].remove(index)
                    cells.setdefault(location, set()).add(index)
                    locations[index] = location
                    first_changed |= index == first
            if first_changed:
                pending = neighbors(first, second)


def contact_pairs(people, strategy="grid"):
    """Inspect a static population without resolving collisions (tests/analysis)."""
    candidates = grid_candidates if strategy == "grid" else brute_candidates
    return [(i, j) for i, j in candidates(people)
            if math.hypot(people[i].x - people[j].x, people[i].y - people[j].y) <= CONTACT_DISTANCE]


def resolve_contact(first, second):
    dx, dy = second.x - first.x, second.y - first.y
    separation = math.hypot(dx, dy)
    if separation > 16:
        return False
    nx, ny = (dx / separation, dy / separation) if separation else (1, 0)
    overlap = 16 - separation + 0.01
    moving = int(not first.stationary) + int(not second.stationary)
    if moving:
        if not first.stationary:
            first.x -= nx * overlap / moving
            first.y -= ny * overlap / moving
            if first.dx * nx + first.dy * ny > 0:
                first.dx *= -1
                first.dy *= -1
        if not second.stationary:
            second.x += nx * overlap / moving
            second.y += ny * overlap / moving
            if second.dx * nx + second.dy * ny < 0:
                second.dx *= -1
                second.dy *= -1
    for person in (first, second):
        person.x = min(776, max(24, person.x))
        person.y = min(576, max(104, person.y))
    return True

