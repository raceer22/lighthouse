# Task 07: Kelvin and exposure in rows and presets, v2 acceptance pass

**Depends on:** task-06
**PRD-v2 sections:** Kelvin and exposure, Constraints · **AC:** 18, 19, 21 (and the sign-off of 1–21)

## Goal
Lights that use color temperature show and keep it everywhere. Rows show a Kelvin field, and presets store and apply exposure and temperature, with the built-ins using Kelvin. Then sign off the whole of PRD v2 on Blender 5.2.2 under both engines.

## Scope
- **Row:**
  - When `use_temperature` exists and is on, the fixed color slot shows `prop(light, "temperature", text="")` instead of the swatch.
  - Put the choice in a pure helper (for example `color_control(light)` returning `"temperature"` or `"color"`) so it can be tested.
  - Widen the slot slightly only if the Kelvin value doesn't fit.
- **`Preset`** (`lighthouse/presets.py`): add `exposure=0.0`, `use_temperature=False` and `temperature=6500.0`, with defaults.
  - `user_presets()` reads them with `data.get()`, so pre-v2 files load with exposure 0 and temperature off.
  - `save_user_preset()` writes them.
- **`preset_from_light()`:** records `exposure` if the light has it, and `use_temperature` / `temperature` if it has them, so whichever color mode the light uses is saved.
- **`apply_preset()`:**
  - Always sets power, RGB color and radius.
  - Sets `exposure` where the light has it.
  - Sets `use_temperature` and `temperature` where the light has them.
  - On versions without `use_temperature`, only the RGB color is set.
  - Check in 5.2 whether `color` tints the temperature. If it does, set the color to white when applying a Kelvin preset, and note this in ARCHITECTURE.md.
  - Use the version-safe lookup from task 06.
- **Built-ins:** Candle 1850 K, 60W Bulb 2700 K and Daylight 5500 K, all with `use_temperature=True`. Each keeps its current RGB as the fallback.
- Update the Apply and Save operator docstrings to mention exposure and temperature.
- **Acceptance pass:**
  - Bump `blender_manifest.toml` to 0.2.0.
  - Update README.md for the v2 features.
  - Rewrite `tests/acceptance.md` for PRD-v2 AC 1–21: automated evidence per criterion, plus a GUI checklist for panel drawing, click modifiers and undo.
  - Extend `tests/smoke_engines.py` so it runs every new operator on every light type under Cycles and then EEVEE: `add_light`, `select_light` actions, `toggle_group`, `collapse_all_groups`, `select_group`, `move_to_group`, `hide_group`, `solo_group`, `toggle_details`, and fractional EV.

## Out of scope
Shape parameters, deleting lights, and everything listed under Out of Scope in PRD-v2.

## Done when (testable)
- Test: `color_control()` returns `"temperature"` for a light with `use_temperature` on and `"color"` otherwise, including for a stub with no `use_temperature` property (AC 18).
- Test: on 5.2, each built-in sets `use_temperature` and the listed Kelvin value on a compatible light. Against a stub without the temperature properties, only RGB is set and nothing raises (AC 19).
- Test (installed, as in `tests/test_user_presets.py`): a preset saved from a 3000 K light with exposure 1.5 restores 3000 K and exposure 1.5 after a restart. A hand-written pre-v2 JSON (no new keys) loads with exposure 0 and temperature off (AC 19).
- `make test`, `make validate` and `make build` pass. The smoke script reports OK for both engines with no Lighthouse warnings or errors (AC 21). If a Blender 4.2 binary is available, run the smoke with `BLENDER=` pointing at it and record the result.
- Manual (GUI): every item in the new `tests/acceptance.md` checklist is ticked on 5.2.2, and a Kelvin light's row shows the Kelvin field with Exposure and Temperature in its details (AC 18).

## Afterwards
Append a `## v2 task 07: Kelvin, exposure and acceptance pass` entry to ARCHITECTURE.md with (1) new components, (2) how data flows between them, (3) Blender API quirks encountered.
