# Task 13: 1.4.0 release, with Alt+drag docs

**Depends on:** task-01 to task-12
**Group:** Delivery · **Source:** `.notes/v6-decisions.md` items 26, 28

## Goal
All v6 features ship as 1.4.0, checked on both supported Blender versions under Cycles and EEVEE. The README also documents Alt+drag on the row's power, color and Kelvin fields, which already works.

## Scope
- `lighthouse/blender_manifest.toml` (and anywhere else the version is stored): bump to 1.4.0.
- README:
  - The Active Light panel and the new panel order (Presets starts closed).
  - The light right-click menu, and its rule for what the entries act on.
  - Additive solo (Shift+click, mixing lights and groups, the World stays exclusive).
  - Load HDRI and which world setups get it.
  - Alt+drag on power, color and Kelvin edits every selected light. This goes in the README only: those fields are Blender's own properties, whose tooltips can't be changed from `layout.prop`.
  - `make bench` in the development section, if task 02 didn't already add it.
- `tests/acceptance.md`: one manual check per v6 task, taken from each task's "Manual (GUI)" line, plus an Alt+drag check.
- `tests/smoke_engines.py`: make sure every new operator from tasks 03–12 is called under both engines.
- Run `make bench` and compare it with the task 02 baseline. If it is well over about 10 ms, note it in TASK_PROGRESS.md as a candidate for caching (not part of this release).
- Run the manual GUI checks listed in TASK_PROGRESS.md that are still open for v6 tasks.

## Done when (testable)
- `make test` passes on 5.2.2 and on 4.2.23 (with only the expected 5.0+ skips).
- The engine smoke run passes on both versions.
- `make validate` and `make build` succeed, and `dist/lighthouse-1.4.0.zip` installs into a clean profile with `make install`.
- Manual: the acceptance checklist is done on 5.2, and on 4.2 for everything that isn't 5.0+ only.

## Afterwards
Append a `## v6 release` entry to ARCHITECTURE.md listing known limits (the `bl_order` result from task 04, the old mid-solo file behavior from task 08, the bench number).
