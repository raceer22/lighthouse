# Task 03: Active Light panel

**Depends on:** task-02
**Group:** Active Light panel · **Source:** `.notes/v6-decisions.md` items 3–6, 9

## Goal
A new **Active Light** panel always shows the active light's controls and details, so you don't have to find its row in a long list. Rows still expand as before, so several lights can still be compared side by side.

## Scope
- Prefactor first (no behavior change): pull a light row's controls and `draw_details()` out of `LIGHTHOUSE_PT_lights` into functions that take a layout, so both panels draw the same thing. The existing tests must still pass unchanged.
- `lighthouse/__init__.py`, new `LIGHTHOUSE_PT_active_light` (`bl_label = "Active Light"`, same space, region and category as the others):
  - Active object is a light: its name, type, power, color or Kelvin, mute and solo, then the same details and light linking as an expanded row.
  - Active object isn't a light, or nothing is active: a short *"Select a light"* label. The panel is not hidden through `poll`, so panels below don't jump as you click between meshes and lights.
  - Read-only lights (library or system override) are greyed out with the same `state.read_only` rule as rows. A muted or hidden light is dimmed as its row is.
  - Mute and solo use the same operators as the row, so solo state and snapshots stay shared.
- Following the viewport selection in the list is not built (item 9). The Reveal button stays as it is.
- Panel order is task 04. Register the panel so it draws, without changing the order yet.

## Done when (testable)
- Test: with a light active, the panel's draw goes through the shared row and details functions for that light (stub layout or whatever the suite uses for draw checks).
- Test: with a mesh active, and with nothing active, the panel draws the "Select a light" label and `poll` is not defined or returns True.
- Test: a library light that is active is drawn with its controls disabled.
- `make test` passes, and the existing row and details tests still pass unchanged.
- `make bench` still runs. Record the new number next to the baseline in TASK_PROGRESS.md.
- Manual (GUI): click between a mesh and a few lights. The panel follows the active light, and the panels below don't move. Edit power in the panel and see the row change.

## Afterwards
Append a `## v6 task 03: Active Light panel` entry to ARCHITECTURE.md (the shared draw functions, why the panel never hides). Add a draw of the panel to `tests/smoke_engines.py` if the smoke run covers drawing.
