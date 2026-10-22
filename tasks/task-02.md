# Task 02: `make bench` for the Lights panel

**Depends on:** none
**Group:** Speed with many lights · **Source:** `.notes/v6-decisions.md` item 2

## Goal
There is a number for how long the Lights panel takes to draw in a large scene. It is taken before the Active Light panel (task 03) adds a second set of details to draw, and is compared by hand before a release.

## Scope
- A benchmark script, outside the pytest suite, run headless through `$BLENDER` like the tests:
  - Builds a scene with about 500 lights spread over nested collections (a few levels deep, some collections with sub-collections and their own lights), with grouped mode on and a few rows expanded.
  - Times one `LIGHTHOUSE_PT_lights.draw()` pass (repeat it a few times and report the median, so one slow pass doesn't skew it) and prints the result in ms.
  - Draw calls need a layout headless. Use the same stub-layout approach as the earlier draw checks (see TASK_PROGRESS, v4 task 04), or whatever the suite already has.
- `Makefile`: a `bench` target (`BLENDER=` works as for `test`).
- No timing budget and no failing threshold: the script only prints.
- No caching. Caching (by depsgraph update) is only added later if the number calls for it. Under about 10 ms, it's done.

## Done when (testable)
- `make bench` runs on 5.2.2 and prints a draw time for about 500 lights.
- `make test` is unchanged: it doesn't collect or run the benchmark.
- The baseline number (with the machine and Blender version) is recorded in TASK_PROGRESS.md.

## Afterwards
Append a `## v6 task 02: Benchmark` entry to ARCHITECTURE.md (what it measures, how to run it, the baseline). Mention `make bench` in the README's development section.
