# Engineering report: Disease Propagation Simulator

## A. Changes implemented

The working simulator was refactored incrementally into a headless engine, agent movement, collision selection/resolution, validated configuration/persistence, Pygame interface, and Agg chart rendering. The entry point remains `python main.py`. Existing interface appearance, controls, population layout, saved disease files, fixed-step timing, and disease rules were retained for this pass.

Collision selection now uses a 16-pixel uniform grid with neighboring-cell checks and stable pair ordering. Grid membership follows agents displaced during contact resolution. A correct all-pairs implementation remains selectable as the reference. Existing original and pre-refactor source snapshots, SHA-256 manifest, and the original recursive functions preserve the comparison.

Added 39 automated tests, benchmark and capture scripts, actual application screenshots/GIF, setup instructions, technical documentation, and a .gitignore. No new runtime frameworks were introduced. Standard-library unittest avoids requiring pytest. Pillow is explicitly listed for regenerating media; Pygame and Matplotlib remain runtime dependencies.

## B. Repository structure

```text
main.py                        Simple entry point
simulator/
  app.py                       Screens, controls, Pygame rendering
  engine.py                    Fixed updates, disease state, statistics, clock
  person.py                    Agent movement and properties
  collision.py                 Grid and pairwise candidates; separation
  config.py                    Strict settings and compatible saved.txt I/O
  reporting.py                 Chart surface without Tkinter
benchmarks/
  run.py                       Repeated full-engine and historical measurements
  legacy_collision.py          Verbatim Grade 12 collision functions
scripts/capture_demo.py         Reproducible application captures
tests/test_baselines.py         Snapshot hashes and historical-source integrity
tests/test_config.py            Validation and persistence
tests/test_engine.py            Disease rules, collisions, timing, invariants
tests/test_interface.py         Headless integration and pre-refactor comparison
docs/baselines/                 Source snapshots and SHA-256 manifest
docs/benchmark_results.json     Samples, environment, settings, correctness checks
docs/BENCHMARKS.md              Comparison methodology and measured tables
docs/DECISIONS.md               Architecture, behavior, algorithm trade-offs
docs/ENGINEERING_REPORT.md      This report
assets/                        Actual menu/simulation/results PNGs and GIF
README.md                      Project overview, setup, usage, tests, performance
requirements.txt               Runtime dependencies
requirements-dev.txt           Runtime requirements plus Pillow for captures
.gitignore                     Virtual environments, caches, local editor state
saved.txt                      Existing scenarios, unchanged
```

## C. Verification results

- `python -m unittest discover -v`: **39 tests passed**, no failures or skips in the final run (5.629 seconds).
- `python -m pip check`: no broken requirements found.
- The grid and pairwise engines produced identical exact agent states, daily history, and RNG state in tested seeded trajectories and all timed benchmark trials.
- A regression test executes the frozen pre-refactor application with two controlled seeds and four seconds of simulated wall time. Positions, directions, disease states, infection dates, daily statistics, and RNG state matched the new engine.
- Additional tests cover contact distance, boundaries, stationary agents, coincident agents, dynamic relocation across grid cells, transmission extremes, recovery/mortality/immunity, population conservation, deterministic seeds, speed/frame-rate invariance, malformed/missing/unreadable saves, name validation, and source-snapshot integrity.
- Real Pygame headless tests initialize screens, retry invalid input, navigate empty and wrapped saved menus, launch simulations, exercise speed/result controls, render charts without Tkinter, and close every screen. An engine-only subprocess confirms neither graphical dependency is imported.
- Original shipped saved scenarios load without changes.
- The capture script ran successfully. Actual application draw methods generated the menu, day-eight simulation, day-45 results, and an 80-frame propagation GIF. The three PNGs were visually inspected. Capture settings and final counts are in assets/capture.json.
- Native desktop mouse/keyboard interaction, display scaling, and a clean download into a fresh virtual environment were not manually verified. Dependencies were verified in the existing environment; no Python installation was changed.

## D. Performance evidence

| Agents / layout | Pairwise us/update | Grid us/update | Time reduction |
|---|---:|---:|---:|
| 30 / uniform | 100.5 | 64.8 | 35.6% |
| 60 / uniform | 389.8 | 130.9 | 66.4% |
| 90 / uniform | 781.3 | 175.6 | 77.5% |
| 300 / uniform | 7591.5 | 619.7 | 91.8% |
| 90 / dense | 751.5 | 328.9 | 56.2% |


These are full fixed simulation updates, excluding rendering and initialization. Seven seeded trials (100–106), each with 120 warm-up updates and 480 timed updates, used alternating strategy order and disabled garbage collection during timing. Candidate counting is included equally in both paths. Environment: Windows 11 build 26200, Intel Family 6 Model 197 processor, CPython 3.13.0rc3, Pygame 2.6.1, Matplotlib 3.11.2. Exact environment, samples, sample standard deviations, settings, and baseline identifiers are stored in docs/benchmark_results.json. Background OS activity and CPU frequency were not controlled.

The 90-agent uniform case reduced average candidate checks from 4,005 to approximately 18.3 per update. The measured 77.5% reduction is relative to the corrected pairwise reference in the same engine; it is not application FPS or a claimed percentage over the Grade 12 program.

The separate historical detector comparison found 4 missed valid contacts out of 7 in a seeded 90-agent snapshot, plus duplicate output. The original detector's apparent speed therefore cannot establish equivalent correct simulation work. At 30 agents, the static detection-only grid measurement was slower than the pairwise detector (98.0 versus 84.2 microseconds); grid overhead is real. Full-update and detection-only timings are separate workloads and should not be mixed.

## E. Technical decisions

Small modules separate calculations from graphics without introducing an application framework. Configuration uses a frozen dataclass and the existing text representation. A private RNG enables deterministic runs without disturbing other instances.

The dynamic grid was chosen because contact distance and arena geometry are fixed. Stable pair ordering and membership refresh preserve sequential resolution and probability draws. A static neighbor list would miss interactions introduced by earlier separations; the targeted relocation regression test protects this behavior.

Grid selection is approximately linear with bounded local density, plus local sorting and refresh work. Dense scenes can have quadratic candidates, and pathological refresh bookkeeping can cost more. The implementation does not claim guaranteed O(n) runtime. The historical recursive detector's whole-algorithm complexity is not logarithmic.

Matplotlib Agg renders directly into the existing Pygame window, preserving the earlier fix for missing Tcl/Tk and avoiding competing GUI event loops. The headless engine requires only the standard library.

## F. Remaining limitations

The model is educational and is not an epidemiological prediction tool. Fixed-step catch-up can reduce UI responsiveness at high requested speeds on slower hardware. Results contain daily snapshots; ending mid-day shows the latest completed record. Initial percentages are probabilistic rather than exact quotas. Dense overlaps remain a worst-case workload.

Performance results apply to the measured machine, settings, and seeded layouts, not every laptop. The original model has known defects and cannot be an exact behavioral oracle; comparisons distinguish it from the corrected pre-refactor app. Native desktop interaction and clean-environment installation remain manual verification steps.

At the time of the refactor, the remote URL and repository folder retained their historical spelling. The owner has since renamed the GitHub repository to [Disease-Propagation-Simulator](https://github.com/abubakrnafees/Disease-Propagation-Simulator); the README now uses that URL. Existing local folders may still have the original name. Historical source snapshots and checksums are unchanged. Existing tracked editor metadata was retained, while future local files are ignored. No commits, pushes, remote changes, or repository rename were performed by the refactoring or documentation updates.

Potential future work: data export, UI seed controls, accessibility, more benchmark hardware, and calibrated disease models. None is presented as completed.

## G. Resume-relevant accomplishments

Defensible examples based on this run:

- Refactored a Pygame disease simulator into a modular, graphics-independent engine and added 39 automated tests covering disease progression, persistence, collisions, timing, and interface flows.
- Implemented deterministic spatial-grid contact selection, reducing measured simulation-update time by 77.5% at 90 agents versus a pairwise reference across seven seeded trials, while preserving exact tested trajectories.
- Built reproducible benchmarks and retained historical implementations; identified missed contacts and duplicate processing in the original recursive detector.

When discussing the timing number, state that rendering was excluded, identify the pairwise reference, and keep population/machine qualifications. Do not claim a 77.5% application FPS improvement or guaranteed performance across workloads.

## Reproduction commands

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m benchmarks.run --repeats 7 --updates 480 --warmup 120
.\.venv\Scripts\python.exe -m scripts.capture_demo --headless
```
