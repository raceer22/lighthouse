# Task 03: Bulk actions say when there is nothing to do

**Depends on:** task-02 (uses its `apply_preset` return shape)
**Type:** UX feedback (bulk operators) · **Source:** polish review, "Actions that do nothing still say they worked"

## Goal
Pressing Apply, an EV step or "Move selected here" with nothing in scope gives a clear warning and leaves no undo step, instead of reporting success on 0 lights.

## Scope
- `lighthouse/__init__.py`, in each bulk operator's `execute()`:
  - **Nothing in scope:** `report({'WARNING'}, ...)` and return `{'CANCELLED'}`, so no undo step is pushed. Messages:
    - `scale_lights` / `step_exposure`: `No lights selected` for scope SELECTED, `No lights in the view layer` for ALL.
    - `apply_preset` / `move_to_group`: `No lights selected`.
  - **Everything skipped** (0 changed, some read-only or incompatible): report the summary as a WARNING and return `{'CANCELLED'}`.
  - **No-op factor:** `scale_lights` with `factor == 1.0` returns `{'CANCELLED'}` silently, matching `step_exposure` with `steps == 0`.
- Keep the checks in `execute()`, not `poll()`. The scope is an operator property, which `poll()` can't read, and buttons that grey out without explaining why are worse than a message.
- `tests/blender_runner.py`: generalise `info_reports(output)` to `reports(output, level="Info")`, so tests can read `Warning:` lines. First check the exact prefix Blender prints for warnings in `--background`.

## Out of scope
Changing what the operators do when they do have lights to act on.

## Done when (testable)
- Test: with nothing selected, `scale_lights(scope='SELECTED')`, `step_exposure(scope='SELECTED')`, `apply_preset` and `move_to_group` each return `{'CANCELLED'}` and report the warning.
- Test: in an empty view layer, `scale_lights(scope='ALL')` warns `No lights in the view layer`.
- Test: `apply_preset('DAYLIGHT')` on only point lights returns `{'CANCELLED'}` and warns with the skipped count.
- Test: `scale_lights(factor=1.0)` returns `{'CANCELLED'}` and leaves power unchanged.
- `make test` passes. Update any test that relied on `FINISHED` for an empty scope.
- Manual (GUI): each warning shows in the status bar, and Ctrl+Z after a cancelled press undoes the previous real change.

## Afterwards
Append a `## v3 task 03: empty-scope feedback` entry to ARCHITECTURE.md, including the report prefix Blender uses in background mode.
