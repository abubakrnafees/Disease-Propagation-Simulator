# Technical decisions

## Preserve the working application

The baseline for this pass is the working 800×600 application after the earlier crash fixes. Its interface, population layout, controls, colors, saved-file format, fixed updates, and disease rules are preserved. The older Grade 12 version used a different window, population layout, terminal input, and collision rules. Those earlier changes are not presented as behavior-preserving optimizations.

The current source was frozen before extraction. A regression test runs that application under a controlled clock and compares its daily history, exact surviving-agent state, and random-generator state against the new engine. The historical recursive detector is preserved separately, with its defects intact for comparison.

## Small modules with a headless core

`Simulation` owns agents, disease configuration, a private random generator, elapsed simulation time, and statistics. `Person` owns movement and agent properties. Collision selection and separation are independent functions. The interface draws engine state and handles input. Chart rendering is isolated behind `chart_surface`.

No dependency-injection framework or new runtime framework is required. Configuration uses a frozen dataclass with strict integer validation. Persistence continues to use the existing text format. Tests use standard-library `unittest` to keep setup simple; pytest is not required.

## Dynamic grid and deterministic ordering

The contact diameter is 16 pixels. Any pair within that distance must occupy the same grid cell or neighboring cells when cell width is 16. Candidate checks inspect these nine cells and use the existing Euclidean contact test.

The pairwise reference resolves contacts sequentially, changing coordinates as it goes. A grid built once and never updated can miss a later pair created by that separation. The candidate iterator therefore updates membership after each yielded pair and refreshes the first agent's remaining neighbors when it crosses a cell boundary. Candidate indices increase monotonically, matching the pairwise ordering without duplicate processing. This preserves random draw order and trajectories.

At bounded local density, grid construction is O(n), with additional local candidate sorting and refresh costs. Every unordered pair can still become a candidate in a crowded scene: O(n²) candidate checks. Sorting and repeated neighborhood refreshes can exceed that bound in pathological layouts; a conservative bound for repeated full neighborhoods is O(n³ log n). Grid performance is measured rather than claimed to be universally linear. Memory includes agents, occupied cells, candidate queues, and contacts; dense contact storage can be O(n²).

The historical recursive detector sorts at each recursion level. A comparison-sort upper bound for its recurrence is O(n log² n), with Python's adaptive sorting able to exploit already-sorted subdivisions. It is not logarithmic overall and does not enumerate all valid contacts.

## Disease and time rules

The refactor preserves independent random selections for initial infection and distancing. A selected distancing agent remains stationary. The disease's infection chance is evaluated per processed eligible contact, not per day. A start-of-update state snapshot prevents instantaneous multi-agent transmission chains. Recovery and mortality are evaluated at daily boundaries; dead agents leave the living population and remain in the total count.

The engine uses 120 fixed movement/contact updates per day. A shared clock scales all updates, keeping contacts and disease progression synchronized at different speeds and rendering rates. Large catch-up workloads can still reduce UI responsiveness; dropping updates would change model outcomes, so this refactor does not silently skip them.

## Results without Tkinter

Matplotlib's Agg backend renders directly into a Pygame surface. This avoids the missing Tcl/Tk installation error and a separate blocking GUI event loop. Day zero is valid chart input. Results use daily snapshots, so ending between boundaries shows the latest recorded day.

## Evidence and limitations

Grid and pairwise engines are checked for exact seeded trajectories, not just similar counts. The original detector is assessed separately for accuracy. Benchmark results exclude drawing and are specific to the recorded environment. Captures use real application drawing functions with SDL software rendering; native desktop interaction and display scaling were not manually verified during this pass.

Existing editor configuration and saved scenarios were retained. `.gitignore` excludes future local environments, caches, and editor files; already-tracked `.idea` files are not deleted. The remote repository and its historical spelling were not changed.
