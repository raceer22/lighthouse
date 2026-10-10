# Task 02: One `+` in the header

**Depends on:** task-01
**Group:** Group menu · **Source:** `.notes/new-features-decisions.md` item 6

## Goal
The header's `+ Light` and New Collection buttons become a single compact `+`. It opens a menu with New Light ▸ and New Collection that adds to the active collection. Adding still works in flat mode, while searching, and when a type filter hides every header, and the header has one free slot for task 03.

## Scope
- `lighthouse/__init__.py`:
  - `LIGHTHOUSE_MT_new`: New Light ▸ (`LIGHTHOUSE_MT_new_light` from task 01, given no target, so it uses the active collection) and New Collection (`use_active` on).
  - When the active collection is read-only, both entries are greyed out, as in the group menu (task 01).
  - `LIGHTHOUSE_PT_lights.draw()`: replace the `operator_menu_enum(add_light)` and `new_collection` buttons with `row.menu(LIGHTHOUSE_MT_new.bl_idname, text="", icon='ADD')`. It sits where `+` is now. The slot New Collection used stays free for task 03.

## Out of scope
The Color/Kelvin toggle that takes the freed slot (task 03).

## Done when (testable)
- Test (Recorder): the Lights panel header draws `LIGHTHOUSE_MT_new` with icon `ADD`. It draws no `lighthouse.add_light` enum menu and no `lighthouse.new_collection` button, whether grouped, flat or searching.
- Test (Recorder): `LIGHTHOUSE_MT_new` draws the New Light menu and New Collection, both on the active collection. With a linked collection active, they are on a disabled layout.
- Test: the header row has one button fewer than before. Count the Recorder entries, so that task 03 has a fixed baseline.
- `make test` passes.
- Manual (GUI): `+` ▸ New Light ▸ Point adds a light to the active collection. `+` ▸ New Collection opens the name dialog. Both work in flat mode, while searching, and with a type filter that hides everything. One Ctrl+Z undoes each.

## Afterwards
Append a `## v5 task 02: compact header +` entry to ARCHITECTURE.md. Update `tests/acceptance.md` where it mentions the two old buttons.
