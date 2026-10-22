# Task 01: New lights match Shift+A, released as 1.3.1

**Depends on:** none
**Group:** New light defaults · **Source:** `.notes/v6-decisions.md` items 1, 27

## Goal
A light added through Lighthouse starts with the same values as one added with Shift+A in the 3D view. Today `bpy.data.lights.new()` gives a Sun of 10 W/m² and an Area of 0.25 × 0.25 m, which is why new Area lights looked too small. The fix ships on its own as the 1.3.1 patch.

## Scope
- `lighthouse/__init__.py`, `LIGHTHOUSE_OT_add_light`: after `bpy.data.lights.new()`, apply a small table of the values where Shift+A differs (checked in 5.2.2):
  - Sun: `energy` 1.0.
  - Area: `size` and `size_y` 1.0.
  - Point and Spot already match, so they get no entry.
- Keep it one table (one place to add a type if Blender's two code paths drift apart again). Apply it before the Kelvin step, so the two stay independent.
- Every way of adding a light goes through this operator (the `+` menu, the group right-click New Light), so all of them get the fix.
- Release 1.3.1: bump the version in `lighthouse/blender_manifest.toml` (and anywhere else it is stored), and add a README changelog line if the README has one.

## Done when (testable)
- Test: `add_light(type='SUN')` gives `energy == 1.0`. `add_light(type='AREA')` gives `size == 1.0` and `size_y == 1.0`.
- Test: Point and Spot keep `lights.new`'s values (power, radius, spot size), so they match Shift+A.
- Test: in Kelvin mode, a new Sun and Area also get the table's values, and the Kelvin settings still apply.
- `make test` passes on 5.2.2 and on 4.2.23 (with only the expected 5.0+ skips). `make validate` and `make build` succeed, giving `dist/lighthouse-1.3.1.zip`.
- Manual (GUI): add an Area and a Sun with Lighthouse and with Shift+A, and compare them in the Light properties.

## Afterwards
Append a `## v6 task 01: New light defaults` entry to ARCHITECTURE.md with the table and why it exists. Note the 1.3.1 release in TASK_PROGRESS.md.
