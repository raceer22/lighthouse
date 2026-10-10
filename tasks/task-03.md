# Task 03: Color/Kelvin toggle for new lights

**Depends on:** task-02
**Group:** Color/Kelvin · **Source:** `.notes/new-features-decisions.md` items 7, 9, 10, 11 (header)

## Goal
An icon toggle in the header, in the slot task 02 freed, sets whether lights that Lighthouse creates start in Color or in Kelvin. In Kelvin mode a new light starts at Blender's default temperature with a white color. The setting is saved with the file. Flipping back to the default (Color for now; task 04 makes it a preference) stores nothing. Shift+A, duplicates and appends are left alone.

## Scope
- `lighthouse/lights.py`, as pure functions so they can be tested without the UI:
  - `new_light_mode(scene_value, default)`: the mode in effect, `'COLOR'` or `'KELVIN'`. `'FOLLOW'` means the default applies.
  - `toggled_mode(scene_value, default)`: the scene value after one flip. It flips the mode in effect and returns `'FOLLOW'` when the result matches the default, so a file only pins a value that differs from it.
  - `supports_temperature()`: `True` when `bpy.types.Light` has `use_temperature` (Blender 5.0+).
- `lighthouse/__init__.py`:
  - `Scene.lighthouse_new_lights`: an EnumProperty with `FOLLOW`, `COLOR` and `KELVIN`, default `FOLLOW`. It is registered and removed next to `lighthouse_solo`, and saved with the .blend.
  - `default_new_light_mode(context)` returns `'COLOR'` in this task. Task 04 makes it read the add-on preferences.
  - `lighthouse.toggle_new_light_mode` (`REGISTER`, `UNDO`). It needs `UNDO` because it changes file data: without an undo step, undoing something else would revert it. Its `description()` names the current mode and whether the file follows the default, for example "New lights start in Kelvin (this file)".
  - Header: when `supports_temperature()`, draw the operator in the freed slot, pressed in Kelvin mode, with an icon for each mode (for example `COLOR` and `LIGHT_SUN`). On 4.x, draw nothing in that slot.
  - `add_light`: after creating the light data, if `supports_temperature()` and the mode is `KELVIN`, set `use_temperature = True`, `temperature` to the RNA default (`bpy.types.Light.bl_rna.properties["temperature"].default`, not hardcoded) and `color` to white. Color mode changes nothing, so Blender's default color stays.

## Out of scope
The Preferences default (task 04). A configurable starting temperature.

## Done when (testable)
- Test: `toggled_mode()` and `new_light_mode()` truth table for both defaults: `FOLLOW` → pinned opposite → `FOLLOW`.
- Test (5.0+): in a fresh file the scene value is `FOLLOW`, and `add_light` makes a light with `use_temperature` off and the RNA default color.
- Test (5.0+): after one toggle the scene value is `KELVIN`, and `add_light` makes a light with `use_temperature` on, the RNA default temperature and color `(1, 1, 1)`. The group-menu path (`use_active=False`) does the same.
- Test (5.0+): a second toggle sets the scene value back to `FOLLOW`, not `COLOR`.
- Test (5.0+): with `KELVIN` pinned, `bpy.ops.object.light_add()` and `bpy.ops.object.duplicate()` of a Color light both give `use_temperature` off.
- Test: the scene value survives `save_as_mainfile` and `open_mainfile`.
- Test (4.2): with the scene value set to `KELVIN`, `add_light` still works and sets no temperature properties. The Recorder header draws no toggle.
- `make test` passes on 5.2 and on 4.2.
- Manual (GUI): the toggle fills the freed slot without shifting the header, its tooltip reads correctly in both modes, and a new light's row shows the Kelvin field in Kelvin mode.

## Afterwards
Append a `## v5 task 03: Color/Kelvin toggle` entry to ARCHITECTURE.md, including why there is no depsgraph handler (item 9). Add `toggle_new_light_mode` followed by `add_light` to `tests/smoke_engines.py`.
