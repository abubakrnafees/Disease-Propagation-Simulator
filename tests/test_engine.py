import random
from pathlib import Path
import subprocess
import sys
import unittest

from simulator.collision import contact_pairs, resolve_contact
from simulator.engine import Simulation, STEPS_PER_DAY, MAX_DAYS
from simulator.person import Person
from benchmarks.legacy_collision import collisions

FACTORS = [40, 1, 25, 14, 5, 2, 5]


def snapshot(sim):
    return (sim.day, sim.dead, sim.history, sim.rng.getstate(),
            [(p.x, p.y, p.dx, p.dy, p.state, p.start_day) for p in sim.people])


class EngineTests(unittest.TestCase):
    def make(self, chance=100, mortality=0, immunity=1, recovery=2, initial=0,
             centers=((200, 200), (216, 200))):
        return Simulation([chance, 1, 100, recovery, mortality, immunity, initial],
                          centers=centers, seed=42)

    def test_probability_extremes(self):
        for chance, expected in [(0, 'healthy'), (100, 'sick')]:
            sim = self.make(chance=chance)
            sim.people[0].state = 'sick'
            sim.update()
            self.assertEqual(sim.people[1].state, expected)

    def test_no_transmission_outside_range(self):
        sim = self.make(centers=((200, 200), (217, 200)))
        sim.people[0].state = 'sick'
        sim.update()
        self.assertEqual(sim.people[1].state, 'healthy')

    def test_no_same_step_transmission_chain(self):
        sim = self.make(centers=((200, 200), (216, 200), (232, 200)))
        sim.people[0].state = 'sick'
        sim.update()
        self.assertEqual([p.state for p in sim.people], ['sick', 'sick', 'healthy'])

    def test_initial_state_extremes(self):
        for percent, state in [(0, 'healthy'), (100, 'sick')]:
            self.assertTrue(all(p.state == state for p in self.make(initial=percent).people))

    def test_recovery_timing_and_immunity(self):
        for immunity, state in [(1, 'recovered'), (2, 'healthy')]:
            sim = self.make(initial=100, immunity=immunity)
            for _ in range(2 * STEPS_PER_DAY - 1):
                sim.update()
            self.assertTrue(all(p.state == 'sick' for p in sim.people))
            sim.update()
            self.assertTrue(all(p.state == state for p in sim.people))

    def test_recovered_not_reinfected(self):
        sim = self.make()
        sim.people[0].state, sim.people[1].state = 'sick', 'recovered'
        sim.update()
        self.assertEqual(sim.people[1].state, 'recovered')

    def test_deaths_do_not_skip_agents_or_transmit(self):
        sim = self.make(initial=100, mortality=100, recovery=1)
        for _ in range(STEPS_PER_DAY):
            sim.update()
        self.assertEqual(sim.people, [])
        self.assertEqual(sim.counts(), (0, 0, 0, 2))
        sim.update()
        self.assertEqual(sim.counts(), (0, 0, 0, 2))

    def test_population_conservation_and_states(self):
        sim = Simulation(FACTORS, seed=11)
        for _ in range(1800):
            sim.update()
            self.assertEqual(sum(sim.counts()), sim.initial_population)
            self.assertTrue(all(p.state in {'healthy', 'sick', 'recovered'} for p in sim.people))
        self.assertTrue(all(sum(row) == sim.initial_population for row in sim.history))

    def test_reproducible_seed(self):
        first, second = Simulation(FACTORS, seed=21), Simulation(FACTORS, seed=21)
        for _ in range(600):
            first.update()
            second.update()
        self.assertEqual(snapshot(first), snapshot(second))

    def test_grid_matches_brute_trajectories(self):
        for seed in range(8):
            rng = random.Random(seed)
            centers = [(rng.uniform(24, 776), rng.uniform(104, 576)) for _ in range(60)]
            centers += [(32, 112), (32, 112), (47.9, 112), (24, 104), (776, 576)]
            for distancing in (0, 100):
                config = [40, 1, distancing, 2, 40, 2, 30]
                grid = Simulation(config, seed=seed, centers=centers)
                brute = Simulation(config, seed=seed, centers=centers, strategy='brute')
                for _ in range(260):
                    grid.update()
                    brute.update()
                self.assertEqual(snapshot(grid), snapshot(brute))

    def test_speed_and_frame_rate_invariance(self):
        runs = []
        for elapsed, speed, repeats in [(20, 1, 100), (20, 2, 50), (20, .5, 200), (40, 1, 50)]:
            sim = Simulation(FACTORS, seed=42)
            for _ in range(repeats):
                sim.advance(elapsed, speed)
            runs.append(snapshot(sim))
        self.assertTrue(all(run == runs[0] for run in runs))
        self.assertEqual(runs[0][0], 1)

    def test_completion_and_no_updates_after_finish(self):
        sim = self.make(initial=100, recovery=1, mortality=100)
        for _ in range(MAX_DAYS * STEPS_PER_DAY):
            sim.update()
        self.assertTrue(sim.finished)
        self.assertEqual(len(sim.history), MAX_DAYS + 1)
        previous = snapshot(sim)
        sim.update()
        self.assertEqual(previous, snapshot(sim))

    def test_engine_imports_without_graphics(self):
        code = ("import sys; from simulator.engine import Simulation; "
                "s=Simulation([40,1,25,14,5,2,5], seed=1); s.update(); "
                "assert 'pygame' not in sys.modules; assert 'matplotlib' not in sys.modules")
        subprocess.run([sys.executable, '-c', code], check=True, capture_output=True,
                       cwd=Path(__file__).resolve().parent.parent)

    def test_invalid_strategy_and_time(self):
        with self.assertRaises(ValueError):
            Simulation(FACTORS, strategy='unknown')
        for elapsed, speed in [(-1, 1), (1, 0), (1, -2)]:
            with self.assertRaises(ValueError):
                self.make().advance(elapsed, speed)


class CollisionTests(unittest.TestCase):
    def test_static_sets_no_misses_or_duplicates(self):
        for seed in range(30):
            rng = random.Random(seed)
            centers = [(rng.uniform(24, 776), rng.uniform(104, 576)) for _ in range(90)]
            centers += [(32, 112), (48, 112), (32, 112), (24, 104), (776, 576)]
            people = [Person(c, FACTORS, rng) for c in centers]
            grid, brute = contact_pairs(people), contact_pairs(people, 'brute')
            self.assertEqual(grid, brute)
            self.assertEqual(len(grid), len(set(grid)))

    def test_exact_contact_diameter(self):
        for distance, expected in [(16, [(0, 1)]), (16.001, [])]:
            people = [Person((32, 112), FACTORS), Person((32 + distance, 112), FACTORS)]
            self.assertEqual(contact_pairs(people), expected)

    def test_empty_singleton_overlap(self):
        self.assertEqual(contact_pairs([]), [])
        people = [Person((200, 200), FACTORS) for _ in range(2)]
        self.assertEqual(contact_pairs(people[:1]), [])
        self.assertTrue(resolve_contact(*people))
        for p in people:
            self.assertTrue(24 <= p.x <= 776 and 104 <= p.y <= 576)

    def test_boundary_reflection(self):
        p = Person((776, 576), FACTORS)
        p.stationary, p.dx, p.dy = False, 1, 1
        p.move()
        self.assertEqual((p.x, p.y, p.dx, p.dy), (776, 576, -1, -1))

    def test_original_misses_valid_pair(self):
        points = [(0, 0), (9, 100), (15, 0), (24, 100)]
        self.assertNotIn(((0, 0), (15, 0)), collisions(points.copy(), []))
        self.assertIn((0, 2), contact_pairs([Person(c, FACTORS) for c in points]))

    def test_original_duplicate(self):
        result = collisions([(0, 0), (1, 0), (2, 0)], [])
        self.assertGreater(len(result), len(set(result)))

    def test_collision_relocation_discovers_later_neighbor(self):
        config = [100, 1, 0, 2, 0, 1, 0]
        centers = [(31.9, 200), (24, 200), (55.9, 200)]
        sims = [Simulation(config, centers=centers, seed=1, strategy=strategy)
                for strategy in ('brute', 'grid')]
        for sim in sims:
            for index, person in enumerate(sim.people):
                person.dx = person.dy = 0
                person.stationary = index != 0
            sim.people[2].state = 'sick'
            sim.update()
        self.assertEqual(snapshot(sims[0]), snapshot(sims[1]))
        self.assertEqual(sims[1].people[0].state, 'sick')

    def test_dense_coincident_trajectories_match(self):
        config = [60, 1, 25, 2, 50, 2, 30]
        sims = [Simulation(config, centers=[(320, 240)] * 30, seed=9, strategy=strategy)
                for strategy in ('brute', 'grid')]
        for _ in range(260):
            for sim in sims:
                sim.update()
        self.assertEqual(snapshot(sims[0]), snapshot(sims[1]))
