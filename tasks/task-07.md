# Task 07: Tidy-up, and prove the Blender 4.2 minimum

**Depends on:** tasks 01–06, so it validates the finished code
**Type:** housekeeping + compatibility · **Source:** polish review, "Code and project tidiness"

## Goal
The suite runs against any Blender binary, passes on both 4.2 LTS and 5.2 LTS, and the manifest's `blender_version_min = "4.2.0"` is backed by a real run. A new contributor can set up the tests from the README alone.

## Scope
- **Test runner:** `tests/blender_runner.py` runs `os.environ.get("BLENDER", "blender")` instead of a hard-coded `blender`. `Makefile`'s `test` target passes `BLENDER` through, so `make test BLENDER=~/blender-4.2/blender` works.
- **4.2 run:**
  - Download the portable Blender 4.2 LTS tarball into a folder outside the repo.
  - Run `make test` and `tests/smoke_engines.py` with it. Fix any failures in the add-on, not by skipping tests, unless a test checks a 5.x-only property. Those must skip with the version in the reason.
  - Check the API calls newer than 4.2 that the code relies on: `invoke_props_dialog(title=...)`, `Light.exposure`, `anim_utils.action_get_channelbag_for_slot` / `action_slot`, and `use_temperature`.
- **Dead code:** remove `RowState.shared` (the info icon reads `light.users`) and its test `test_lights_sharing_one_datablock_are_both_shared_and_a_lone_light_is_not`. Keep `test_editing_power_on_one_shared_row_changes_the_other`.
- **Imports:** in `lighthouse/__init__.py`, put `pathlib` with the other standard imports and wrap the `.lights` and `.presets` imports in parenthesised, multi-line lists.
- **README:**
  - "Develop": set up with `python -m venv .venv && .venv/bin/pip install pytest`, and `BLENDER=/path/to/blender` for another binary.
  - "Tested on": list the 4.2 and 5.2 versions that actually passed.
- **Manifest:** bump `version` to `1.2.0` for the v3 polish release. Rebuild with `./build.sh` and validate.

## Out of scope
New features from `.notes/new-features.md`, and CI.

## Done when (testable)
- `make test` and `tests/smoke_engines.py` pass on 5.2.2, and on 4.2 LTS via `BLENDER=...`. Paste both result lines into `tests/acceptance.md`.
- `make validate` and `./build.sh` succeed, producing `dist/lighthouse-1.2.0.zip`.
- `grep -n "shared" lighthouse/lights.py` finds no `RowState` field.
- Manual (GUI, 4.2): install the zip, open the Lights tab, and click through one light row, one group header, a preset Apply and an EV step with no console errors.

## Afterwards
Append a `## v3 task 07: 4.2 verification` entry to ARCHITECTURE.md listing every 4.2-vs-5.2 difference found.
