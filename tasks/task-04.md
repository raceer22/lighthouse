# Task 04: Color/Kelvin default in Preferences

**Depends on:** task-03
**Group:** Color/Kelvin · **Source:** `.notes/new-features-decisions.md` items 8, 11 (Preferences)

## Goal
Add-on Preferences hold a default, Color or Kelvin, that applies to every file. A file that has never been toggled follows the default, including when it changes later. Flipping the header toggle pins the file to its own value, and flipping it back to match the default un-pins it again.

## Scope
- `lighthouse/__init__.py`:
  - `LIGHTHOUSE_AP_preferences.new_light_mode`: an EnumProperty with `COLOR` and `KELVIN`, default `COLOR`. It is drawn above Restore Default Presets with a label such as "New lights start in", expanded, and only when `supports_temperature()`.
  - `default_new_light_mode(context)` reads the preference when the add-on is installed (`context.preferences.addons.get(__package__)`). Otherwise it returns `'COLOR'`, which keeps `import lighthouse; lighthouse.register()` tests working.
  - The header toggle's `description()` says when the file follows the default, for example "New lights start in Kelvin (Preferences default)".
- No change to the scene property or `toggled_mode()`: task 03 already un-pins against whatever default it is given.
- These tests use `run_installed`, because add-on preferences need the `bl_ext` package.

## Done when (testable)
- Test (5.0+): with the default set to Kelvin, an untouched file's `add_light` makes a Kelvin light.
- Test (5.0+): with the default set to Kelvin, one toggle stores `COLOR` and a second toggle stores `FOLLOW`.
- Test (5.0+): a file pinned to `COLOR` still makes Color lights after the default changes to Kelvin. A `FOLLOW` file switches with it.
- Test: after `bpy.ops.wm.save_userpref()`, a second run with the same user dir reads Kelvin as the default.
- Test (Recorder): the preferences draw `new_light_mode` on 5.0+ and not on 4.2. Restore Default Presets is still drawn on both.
- `make test` passes on 5.2 and on 4.2.
- Manual (GUI): change the default in Preferences, and the header toggle of an untouched file flips with it. Toggle it, change the default again, and the pinned file keeps its value.

## Afterwards
Append a `## v5 task 04: Color/Kelvin default` entry to ARCHITECTURE.md describing the pin/un-pin rule. Mention the setting in the README.
