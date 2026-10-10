# Task 09: Intensity scope starts as Selected

**Depends on:** none
**Group:** Intensity · **Source:** `.notes/new-features-decisions.md` item 13

## Goal
The Intensity panel's scope starts as Selected, so Apply and the EV buttons don't scale every light in the scene by accident.

## Scope
- `LIGHTHOUSE_PG_settings.scale_scope`: `default='SELECTED'`. `SCOPE_ITEMS` keeps its order, so the toggle still reads All | Selected.
- It stays on the WindowManager, so every session starts at Selected.
- The `scope` property of the `scale_lights` and `step_exposure` operators is unchanged. The panel always passes the chosen scope.

## Done when (testable)
- Test: in a fresh session, `window_manager.lighthouse.scale_scope == 'SELECTED'`.
- Test: a `.blend` saved with the scope set to All opens with Selected in a new session (`open_mainfile` in a second run).
- `make test` passes.
- Manual (GUI): the panel opens with Selected pressed.

## Afterwards
Append a one-line `## v4 task 09` entry to ARCHITECTURE.md.
