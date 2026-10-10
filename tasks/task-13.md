# Task 13: v5 release

**Depends on:** task-01 to task-12
**Group:** Delivery · **Source:** `.notes/new-features-decisions.md` item 25

## Goal
All v5 features ship as one release, checked on both supported Blender versions under Cycles and EEVEE.

## Scope
- `lighthouse/blender_manifest.toml` and `__init__.py`: bump the version.
- README:
  - The group right-click menu and the single `+`.
  - The Color/Kelvin toggle and its Preferences default.
  - The World panel: what counts as simple, Add Rotation, and how mute and solo work.
  - Light linking, receivers only, with the engine table and any Outliner limit from task 09.
  - The new panel order.
- `tests/acceptance.md`: one manual check per v5 task, taken from each task's "Manual (GUI)" line.
- `tests/smoke_engines.py`: make sure every new operator from tasks 01–12 is called under both engines.
- Run the manual GUI checks listed in TASK_PROGRESS.md that are still open for v5 tasks.

## Open questions
Not decided: the version number. Default: `1.3.0`. Nothing breaks for existing files, and the only visible reshuffle is the header and the panel order.

## Done when (testable)
- `make test` passes on 5.2.2 and on 4.2.23 (with only the expected 5.0+ skips).
- The engine smoke run passes on both versions.
- `make validate` and `make build` succeed, and `dist/lighthouse-<version>.zip` installs into a clean profile with `make install`.
- Manual: the acceptance checklist is done on 5.2, and on 4.2 for everything that isn't 5.0+ only.

## Afterwards
Append a `## v5 release` entry to ARCHITECTURE.md listing known limits (Outliner collections, engines, Mute fallback if it was used).
