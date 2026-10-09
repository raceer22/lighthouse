# Task 01: Installable extension with a Lights tab listing light names (tracer bullet)

**Depends on:** none

## Goal
The thinnest end-to-end flow: a valid extension that installs in Blender, enables cleanly, and shows a "Lights" tab in the 3D Viewport N-panel listing the name of every light in the current view layer.

## Scope
- `lighthouse/blender_manifest.toml` (id `lighthouse`, GPL-3.0-or-later, `blender_version_min = "4.2.0"`, no dependencies).
- `lighthouse/__init__.py` with `register()` / `unregister()`.
- One `Panel` (`VIEW_3D`, region `UI`, category "Lights") that draws one plain label per light object in `context.view_layer.objects` with `type == 'LIGHT'`.
- A repeatable way to build/install: `blender --command extension build` into a zip, then install it.

## Out of scope
Controls, filters, sorting, hidden/library handling.

## Done when (testable)
- `blender --command extension validate` passes and `extension build` produces a zip (AC 14, first pass).
- Installing the zip in Blender 5.2.2 enables with no console errors (AC 1).
- With 3 lights in a scene, the "Lights" tab shows 3 names; adding or deleting a light updates the list on redraw (AC 2).
- Disabling then re-enabling the extension raises no errors.
