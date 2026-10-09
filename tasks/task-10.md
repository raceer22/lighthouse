# Task 10: Save user presets to the user config folder

**Depends on:** task-09

## Goal
Users can capture a light's current settings as a preset that persists across .blend files and sessions.

## Scope
- "Save as preset" operator: takes the active light, prompts for a name, and writes power, color, radius and type compatibility to a JSON file under `bpy.utils.extension_path_user(__package__, create=True)`.
- Preset dropdown merges built-in and user presets (user presets marked). Invalid or corrupt user files are skipped with a warning.
- Optional: delete user preset operator. Built-ins cannot be overwritten or deleted. Name collisions with built-ins are rejected.

## Out of scope
Import/export UI, preset sharing.

## Done when (testable)
- Saving "My Key" from a light in file A, then opening a different .blend file B, shows "My Key" in the dropdown and it applies correctly (AC 12).
- The preset survives restarting Blender.
- A corrupt JSON file in the folder does not break the panel or registration.
- Saving with a built-in name is refused with a clear message.
