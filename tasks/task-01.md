# Task 01: Three panels and finer intensity steps

**Depends on:** v1 as shipped (commit 25a7d54)
**PRD-v2 sections:** Panel layout, Intensity · **AC:** 1, 2

## Goal
Split the single Lights panel into three top-level panels (**Intensity**, **Presets**, **Lights**) and make intensity changes finer. This is the smallest end-to-end change in v2: it ships on its own, and every later task draws into the new Lights panel.

## Scope
- `lighthouse/__init__.py`: replace `LIGHTHOUSE_PT_lights.draw_intensity/draw_presets` with three panels, all `VIEW_3D` / `UI` / `bl_category = "Lights"`:
  - `LIGHTHOUSE_PT_intensity`, `LIGHTHOUSE_PT_presets`, `LIGHTHOUSE_PT_lights` (keep this idname for the list).
  - Register them in that order so it is the default order. No `bl_parent_id`: they are top-level, so Blender stores their open/closed state and drag order itself.
- **Presets panel:** `draw_header()` draws the preset dropdown and **Apply**, so both work while the panel is collapsed. The body holds save (`+`) and delete (`-`). Delete still shows only for user presets.
- **Intensity panel:**
  - Draw the factor as a plain number field: drop `slider=True` and the `soft_max`, so dragging isn't capped at 10. Default stays 1.0.
  - The EV row gets six buttons: **−1, −½, −¼, +¼, +½, +1**.
  - `LIGHTHOUSE_OT_step_exposure.steps` becomes a `FloatProperty`, and power is multiplied by `2 ** steps` through `scale_lights()`, so keyframes still scale. Update the docstring (tooltip) to match.
  - EV and factor change `energy` only. They never touch `Light.exposure`.
- **Lights panel:** search, type filter and the v1 flat list, unchanged.

## Out of scope
Anything about list rows, groups or details (tasks 02–06).

## Done when (testable)
- Test: `LIGHTHOUSE_PT_intensity`, `LIGHTHOUSE_PT_presets` and `LIGHTHOUSE_PT_lights` are registered in category "Lights", and the presets panel defines `draw_header` (AC 1).
- Test: `step_exposure(steps=0.25)` turns 100 W into ≈118.92 W. −1, −0.5, −0.25, +0.5 and +1 each give `100 * 2 ** steps` (AC 2).
- Test: a keyframed light's power keyframes scale by `2 ** 0.25` too.
- Test: the factor property defaults to 1.0 and has no `soft_max` cap below `max`.
- `make test` passes, with the existing EV tests updated to the float `steps`.
- Manual (GUI): collapse each panel and drag it to a new position, then save and reopen the file, and both are kept. With Presets collapsed, picking a preset and pressing Apply in the header works. The factor field has no slider bar.

## Afterwards
Append a `## v2 task 01: three panels and finer intensity steps` entry to ARCHITECTURE.md with (1) new components, (2) how data flows between them, (3) Blender API quirks encountered.
