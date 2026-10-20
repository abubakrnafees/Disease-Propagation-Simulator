"""Deterministic simulation, independent of Pygame and Matplotlib."""
import random

from .collision import brute_candidates, grid_candidates, resolve_contact
from .config import DiseaseConfig
from .person import Person

STEPS_PER_DAY = 120
STEP_MS = 1000 / 60
MAX_DAYS = 365


class Simulation:
    """Advance one fixed physics step with update(), or wall time with advance().

    State snapshots prevent newly infected agents transmitting in the same step.
    Daily records include day zero and retain deaths for population accounting.
    """

    def __init__(self, config, *, seed=None, strategy="grid", centers=None):
        self.config = (config if isinstance(config, DiseaseConfig)
                       else DiseaseConfig.from_list(config))
        if strategy not in ("grid", "brute"):
            raise ValueError("Collision strategy must be grid or brute.")
        self.strategy = strategy
        self.rng = random.Random(seed)
        if centers is None:
            centers = [(x, y) for x in range(50, 760, self.config.population_size * 75)
                       for y in range(125, 560, 50)]
        self.people = [Person(center, self.config.to_list(), self.rng) for center in centers]
        self.initial_population = len(self.people)
        self.dead = self.day = self.steps = self.last_candidates = 0
        self.accumulator = 0.0
        self.history = [self.counts()]

    @property
    def finished(self):
        return self.day >= MAX_DAYS

    def counts(self):
        """Healthy, sick, recovered, dead, in chart-series order."""
        totals = {"healthy": 0, "sick": 0, "recovered": 0}
        for person in self.people:
            totals[person.state] += 1
        return totals["healthy"], totals["sick"], totals["recovered"], self.dead

    def _progress_disease(self):
        survivors = []
        config = self.config
        for person in self.people:
            if person.state == "sick" and self.day - person.start_day >= config.recovery_days:
                if self.rng.randrange(100) < config.mortality:
                    self.dead += 1
                    continue
                person.state = "recovered" if config.recovered_immunity == 1 else "healthy"
            survivors.append(person)
        self.people = survivors

    def update(self):
        """Move, resolve contacts, transmit, then progress disease at day boundaries."""
        if self.finished:
            return
        for person in self.people:
            person.move()
        states = [person.state for person in self.people]
        contacts = []
        candidates = grid_candidates if self.strategy == "grid" else brute_candidates
        self.last_candidates = 0
        for i, j in candidates(self.people):
            self.last_candidates += 1
            if resolve_contact(self.people[i], self.people[j]):
                contacts.append((i, j))
        for i, j in contacts:
            for target, source in ((i, j), (j, i)):
                person = self.people[target]
                if (states[target] == "healthy" and states[source] == "sick"
                        and person.state == "healthy"
                        and self.rng.randrange(100) < self.config.contagiousness):
                    person.state, person.start_day = "sick", self.day
        self.steps += 1
        if self.steps % STEPS_PER_DAY == 0:
            self.day += 1
            self._progress_disease()
            self.history.append(self.counts())

    def advance(self, elapsed_ms, speed=1.0):
        """Scale all physics and disease progression by the same positive speed."""
        if elapsed_ms < 0 or speed <= 0:
            raise ValueError("Elapsed time must be nonnegative and speed positive.")
        self.accumulator += elapsed_ms * speed
        while self.accumulator + 1e-9 >= STEP_MS and not self.finished:
            self.accumulator = max(0.0, self.accumulator - STEP_MS)
            self.update()
