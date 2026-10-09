# Task 12: Packaging, publishing readiness and full acceptance pass

**Depends on:** tasks 01-11

## Goal
Close out packaging and verify every PRD acceptance criterion in Blender 5.2.2.

## Scope
- Finalise `blender_manifest.toml`: name, tagline, version, maintainer, `tags` (e.g. "Lighting"), `license = ["SPDX:GPL-3.0-or-later"]`, `blender_version_min = "4.2.0"`, `permissions` for file access if user presets need it (`files` with reason).
- Add a `LICENSE`/`COPYING` file, a short README, and a `.gitignore` or `build_ignore` rules for the zip.
- Add a repeatable `build.sh` (validate + build).
- Write `tests/acceptance.md` (or a headless `blender -b --python` smoke script) walking AC 1-14.
- Fix any defects found.

## Out of scope
Submitting to extensions.blender.org.

## Done when (testable)
- `blender --command extension validate` passes and `extension build` creates a zip that installs on a clean Blender 5.2.2 profile (AC 1, 14).
- Every AC 1-13 is checked off in the acceptance doc with a pass result.
- No warnings or errors in the console while exercising all features under Cycles and EEVEE.
