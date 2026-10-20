"""Reproducible, rendering-free engine and historical detector benchmarks."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import gc
import json
import os
import platform
from pathlib import Path
import random
import statistics
import sys
import time

from simulator.collision import contact_pairs
from simulator.engine import Simulation
from . import legacy_collision

ROOT = Path(__file__).resolve().parent.parent
CONFIG = [40, 1, 25, 14, 5, 2, 5]


def centers_for(size, seed, dense=False):
    rng = random.Random(seed)
    bounds = (300, 400, 250, 350) if dense else (24, 776, 104, 576)
    return [(rng.uniform(*bounds[:2]), rng.uniform(*bounds[2:])) for _ in range(size)]


def state(sim):
    return (sim.history, sim.dead, sim.rng.getstate(),
            [(p.x, p.y, p.dx, p.dy, p.state, p.start_day) for p in sim.people])


def measure(size, repeats, updates, warmup, dense=False):
    samples = {strategy: [] for strategy in ('brute', 'grid')}
    comparisons = {strategy: [] for strategy in samples}
    for repeat in range(repeats):
        seed = 100 + repeat
        sims = {strategy: Simulation(CONFIG, seed=seed, strategy=strategy,
                                     centers=centers_for(size, seed, dense))
                for strategy in samples}
        for sim in sims.values():
            for _ in range(warmup):
                sim.update()
        for strategy in (('brute', 'grid') if repeat % 2 == 0 else ('grid', 'brute')):
            sim = sims[strategy]
            count = 0
            enabled = gc.isenabled()
            gc.disable()
            try:
                start = time.perf_counter_ns()
                for _ in range(updates):
                    sim.update()
                    count += sim.last_candidates
                duration = time.perf_counter_ns() - start
            finally:
                if enabled:
                    gc.enable()
            samples[strategy].append(duration / updates / 1000)
            comparisons[strategy].append(count / updates)
        if state(sims['brute']) != state(sims['grid']):
            raise AssertionError('Optimization changed simulation trajectory')
    result = {'population': size, 'layout': 'dense' if dense else 'uniform', 'strategies': {}}
    for strategy in samples:
        mean = statistics.mean(samples[strategy])
        result['strategies'][strategy] = {
            'mean_update_us': mean,
            'sample_stdev_us': statistics.stdev(samples[strategy]) if repeats > 1 else 0,
            'updates_per_second': 1_000_000 / mean,
            'mean_candidate_comparisons': statistics.mean(comparisons[strategy]),
            'samples_us': samples[strategy],
        }
    result['update_time_reduction_percent'] = (
        100 * (1 - result['strategies']['grid']['mean_update_us'] /
               result['strategies']['brute']['mean_update_us']))
    result['identical_trajectory'] = True
    return result


def detector_comparison(size, repeats=50):
    # The historical detector misses contacts; it is not a valid full-engine baseline.
    sim = Simulation(CONFIG, seed=42, centers=centers_for(size, 42))
    points = [(p.x, p.y) for p in sim.people]
    truth = set(contact_pairs(sim.people, 'brute'))
    lookup = {point: i for i, point in enumerate(points)}
    old = legacy_collision.collisions(points.copy(), [])
    pairs = [tuple(sorted((lookup[a], lookup[b]))) for a, b in old]
    timings = {}
    for strategy in ('legacy', 'brute', 'grid'):
        start = time.perf_counter_ns()
        for _ in range(repeats):
            if strategy == 'legacy':
                legacy_collision.collisions(points.copy(), [])
            else:
                contact_pairs(sim.people, strategy)
        timings[strategy] = (time.perf_counter_ns() - start) / repeats / 1000
    return {'population': size, 'true_contacts': len(truth),
            'original_unique_contacts': len(set(pairs)),
            'original_missed_contacts': len(truth - set(pairs)),
            'original_duplicate_contacts': len(pairs) - len(set(pairs)),
            'detection_only_mean_us': timings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--updates', type=int, default=240)
    parser.add_argument('--warmup', type=int, default=60)
    parser.add_argument('--sizes', type=int, nargs='+', default=[30, 60, 90, 300])
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/benchmark_results.json')
    args = parser.parse_args()
    if min(args.repeats, args.updates, *args.sizes) < 1 or args.warmup < 0:
        parser.error('Use positive sizes/repeats/updates and nonnegative warmup.')
    if args.updates + args.warmup > 365 * 120:
        parser.error('Benchmark must not exceed the 365-day simulation duration.')
    report = {'environment': {'python': sys.version, 'platform': platform.platform(),
              'processor': os.environ.get('PROCESSOR_IDENTIFIER', platform.processor()),
              'timer': 'perf_counter_ns', 'gc_during_timing': 'disabled', 'rendering': False,
              'run_utc': datetime.now(timezone.utc).isoformat(),
              'dependencies': {name: version(name) for name in ('pygame', 'matplotlib')},
              'baseline_manifest': json.loads((ROOT / 'docs/baselines/manifest.json').read_text())},
              'settings': {'repeats': args.repeats, 'updates': args.updates,
                           'warmup': args.warmup, 'seeds': list(range(100, 100 + args.repeats)),
                           'config': CONFIG, 'arena': [24, 776, 104, 576]},
              'engine': [], 'original_detector': []}
    for size in args.sizes:
        row = measure(size, args.repeats, args.updates, args.warmup)
        report['engine'].append(row)
        print(f"{size} uniform: {row['update_time_reduction_percent']:.1f}% less update time", flush=True)
        report['original_detector'].append(detector_comparison(size))
    report['engine'].append(measure(90, args.repeats, args.updates, args.warmup, dense=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Saved {args.output}')


if __name__ == '__main__':
    main()
