# Benchmark methodology and original comparison

## Which original?

1. **Grade 12 original**, commit `bd8d01a`: recursive coordinate-based detection. Full source is `baselines/grade12_main.py.txt`. The collision functions in `benchmarks/legacy_collision.py` are verbatim and tested against that snapshot.
2. **Corrected app before this refactor**: pairwise contact resolution, fixed time steps, and in-app results. Exact source is `baselines/pre_refactor_main.py.txt`. SHA-256 values and the full original commit ID are in `baselines/manifest.json`. Regression tests execute the frozen app under controlled time.
3. **Modular engine**: selectable `brute` reference and `grid` implementation. Only candidate selection differs. Movement, separation, transmission, random draws, and daily progression are the same in both timed paths.

The original remains in Git history. Snapshots are reference material, not production code. Existing history was not rewritten; the new files remain uncommitted until the owner commits them.

## Full-update comparison

| Agents / layout | Pairwise µs/update | Grid µs/update | Time reduction | Grid updates/s | Pairwise / grid candidate checks |
|---|---:|---:|---:|---:|---:|
| 30 / uniform | 100.5 | 64.8 | 35.6% | 15,443 | 435 / 1.6 |
| 60 / uniform | 389.8 | 130.9 | 66.4% | 7,642 | 1,770 / 7.7 |
| 90 / uniform | 781.3 | 175.6 | 77.5% | 5,695 | 4,005 / 18.3 |
| 300 / uniform | 7591.5 | 619.7 | 91.8% | 1,614 | 44,850 / 216.9 |
| 90 / dense | 751.5 | 328.9 | 56.2% | 3,040 | 4,005 / 167.3 |


Negative time reduction would mean a regression. Formula: `100 * (pairwise_mean - grid_mean) / pairwise_mean`. Updates/s is `1,000,000 / mean_microseconds`; it is not display FPS.

Uniform layouts use the current 752×472 center-coordinate arena. The dense case starts 90 agents in a 100×100 square and is measured after warm-up. Stress populations are passed directly to the engine; normal UI limits are unchanged.

Seven independent trials use seeds 100–106. Each creates fresh agents, performs 120 warm-up updates, then times 480 updates using `perf_counter_ns`. Initialization, drawing, and charting are outside timing. Both paths include the same candidate-count instrumentation. Garbage collection is disabled only during timing and restored afterward. Strategy ordering alternates. Background OS activity and CPU frequency are not controlled; raw JSON includes batch samples and sample standard deviations. This is local engineering evidence, not a universal speed guarantee or a confidence interval.

Every trial asserts identical positions, directions, disease states, infection dates, deaths, daily history, and RNG state. The grid receives no credit for skipping valid interactions.

## Historical detector: accuracy and detection-only timing

| Agents | True contacts | Original misses | Original duplicate pairs | Original / pairwise / grid detector µs |
|---|---:|---:|---:|---:|
| 30 | 2 | 0 | 1 | 63.1 / 84.2 / 98.0 |
| 60 | 4 | 2 | 3 | 91.5 / 230.8 / 97.4 |
| 90 | 7 | 4 | 4 | 171.6 / 451.8 / 130.8 |
| 300 | 116 | 101 | 27 | 538.6 / 5046.7 / 700.5 |


These are static uniform layouts using seed 42. The point list is copied before the legacy function sorts it. The correct pairwise contact set is the oracle. Detection-only timings average 50 calls per strategy and include normal setup. They exclude movement, disease progression, and drawing. Do not mix them with the full-update table; these are diagnostic microbenchmarks, not repeated-trial engine claims.

The original compares adjacent points in a narrow split strip, missing cross-split pairs. It can also append the same pair in a parent strip and a recursive leaf. Coordinate-keyed lookup loses agent identity for coincident coordinates in the historical app. Tests retain minimal missed/duplicate examples.

An incomplete detector can look fast while doing incorrect work. The defensible resume number is therefore grid-versus-corrected-pairwise full-update reduction, qualified with population and machine, not a percentage against the Grade 12 detector.

## Reproduction

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m benchmarks.run --repeats 7 --updates 480 --warmup 120
```

Use `--sizes 30 60 90 300` to choose populations or `--output other-run.json` to retain another run. The benchmark also includes a dense 90-agent case. Environment, configuration, samples, and baseline identifiers are stored in `benchmark_results.json`.
