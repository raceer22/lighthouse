# Task 12: Light linking engine note

**Depends on:** task-09
**Group:** Light linking · **Source:** `.notes/new-features-decisions.md` item 24

## Goal
Under a render engine that doesn't render light linking, the Light Linking section stays visible and editable, with a note such as "Not rendered in EEVEE, Cycles only". The links are saved and take effect when you switch engines.

## Verify first
Which engines and versions render light linking? Render a tiny image of a plane under one light linked to exclude it, on 4.2 and 5.2, in Cycles, EEVEE and Workbench, and check whether the plane goes dark. Record the result as a table in ARCHITECTURE.md. If the check runs in a few seconds, keep it as a test.

## Scope
- `lighthouse/lights.py`: `light_linking_note(engine)` returns the note for engines that the verify step shows don't render light linking (with the engine's display name), or `None` for engines that do. Version differences, if any, use `blender_version`-style checks in the add-on (`bpy.app.version`).
- `lighthouse/__init__.py`: `draw_details()` draws the note with an `INFO` icon at the top of the Light Linking section. Buttons and rows stay enabled.

## Open questions
Not decided: third-party engines. Default: show "Not rendered in <engine>, Cycles only" for any engine not known to render light linking.

## Done when (testable)
- Test: `light_linking_note()` for `CYCLES`, the EEVEE id (`EEVEE` from the prelude), `BLENDER_WORKBENCH` and an unknown id matches the verified table.
- Test (Recorder): the note is drawn under an engine without light linking and not under Cycles. Link Selected is still enabled in both.
- `make test` passes on 5.2 and on 4.2.
- Manual (GUI): switch the engine with the details open, and the note appears and disappears while the links stay.

## Afterwards
Append a `## v5 task 12: engine note` entry to ARCHITECTURE.md with the verify table. Add the engine support to the README's requirements line.
