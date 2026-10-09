# Task 05: Light rows: type, name clicks, highlight, compact layout, add light

**Depends on:** task-04
**PRD-v2 sections:** Light rows, Lights list header (`+` button) · **AC:** 15, 16, 17, 20

## Goal
Each row becomes the main place to work on a light. From the row you can switch the light's type, select it the way you would in the outliner (with a highlight showing the selection), rename it and frame it. Power and color sit side by side with no gap, and the list header can add a new light.

## Scope
- **Row order:**
  1. disclosure triangle
  2. type dropdown
  3. name button
  4. info icon
  5. power (takes the remaining width)
  6. unit label in a sub-row with `ui_units_x ≈ 1.5`
  7. color swatch in a sub-row with `ui_units_x ≈ 2`
  8. mute
  9. solo

  The unit and swatch widths are fixed, which removes the gap.
- **Type dropdown:** `prop(light, "type", icon_only=True)`, disabled when `row_state().read_only`. On shared data it changes every user, as the Properties editor does.
- **Name button:** `LIGHTHOUSE_OT_select_light` gains an `action` enum (`SELECT`, `TOGGLE`, `RENAME`, `FRAME`). `invoke()` sets it from the event modifiers, so `execute()` can be tested headless.
  - Click (`SELECT`): select only this light and make it active (v1 behaviour).
  - Shift (`TOGGLE`): add the light to the selection and make it active, or remove it if it is already selected.
  - Ctrl (`RENAME`): `invoke_props_dialog` with a `new_name` property pre-filled with the current name. An empty name is rejected.
  - Alt (`FRAME`): select only this light, then call `view3d.view_selected` in the 3D view. Use `context.temp_override` with the VIEW_3D area and its WINDOW region if needed.
  - The docstring (tooltip) lists all four. Keep `UNDO`.
- **Highlight:** selected rows are highlighted and the active light gets a stronger one, for example `depress=True` on selected name buttons and an embossed style for the active one. Pick what reads clearly in the default theme and record the choice.
- **`+` button** in the list header: `layout.operator_menu_enum("lighthouse.add_light", "type", text="", icon='ADD')` offers Point, Sun, Spot and Area. `lighthouse.add_light` (`UNDO`):
  - creates the light data and object at `scene.cursor.location`
  - links it to `view_layer.active_layer_collection.collection`, with an error if that collection is read-only
  - deselects everything else, then selects the new light and makes it active

## Out of scope
Range selection, double-click rename, drag and drop, deleting lights, shape parameters.

## Done when (testable)
- Test: `select_light(action='SELECT')` behaves as in v1, and the existing `test_clicking_a_name_…` still passes (AC 15).
- Test: `TOGGLE` adds an unselected light and makes it active, and removes a selected one. Other selected objects are kept (AC 15).
- Test: `RENAME` with `new_name="Key Light"` renames the object, and an empty name leaves it unchanged (AC 15).
- Test: `FRAME` in `--background` selects only that light and doesn't raise. Framing itself is checked by hand.
- Test: setting `light.type` on shared data changes every object using it (AC 16).
- Test: for each of the four types, `add_light` puts the light at the cursor location, in the active collection (set to a sub-collection), selected and active, with the old selection cleared (AC 20).
- `make test` passes.
- Manual (GUI):
  - All four click variants work from a row, and the tooltip lists them.
  - Selected and active rows are visibly different.
  - The type dropdown changes the type, one Ctrl+Z reverts it, and it is greyed out on a library light (AC 16).
  - There is no gap between power and color, and the unit is still readable at the default N-panel width (AC 17).

## Afterwards
Append a `## v2 task 05: light rows` entry to ARCHITECTURE.md with (1) new components, (2) how data flows between them, (3) Blender API quirks encountered (for example which modifier clicks Blender passes through to an operator button).
