# Task 05: Right-click a light's name: Rename, Frame, Solo

**Depends on:** none
**Group:** Right-click menu · **Source:** `.notes/v6-decisions.md` items 10, 11, 15

## Goal
Right-clicking a light's name in the list opens Blender's context menu with Lighthouse entries at the top, the same way as the group menu (v5 decision 1). This task adds the menu and its three single-light entries: **Rename**, **Frame** and **Solo**. Tasks 06, 07 and 09 add the rest.

## Scope
- `lighthouse/__init__.py`: a draw function prepended to `UI_MT_button_context_menu`, like `draw_group_menu()`. It only draws when `context.button_operator` is `LIGHTHOUSE_OT_select_light`, finds the light by `name` and `library`, and ends with a separator. It is registered and removed alongside the group menu.
- Entries in their final positions, so later tasks fill the gaps: **Rename, Frame**, (Duplicate, Duplicate Linked, Delete, Apply Preset ▸, Mute — later tasks), **Solo**, (Add to Solo — task 09).
- These three act only on the clicked light:
  - **Rename**: a small popup with a name field (`invoke_props_dialog`), like F2. It renames only the object, never the light data. Reuse `select_light`'s `RENAME` action if its dialog fits.
  - **Frame**: select only that light and frame it, as with `select_light`'s `FRAME` action (Alt+click).
  - **Solo**: `solo_light` for the clicked light, with its label showing whether it is already soloed ("Solo" / "Exit Solo").
- Read-only lights: Rename is disabled. Frame and Solo still work, since they don't edit the light (same as the row's buttons).

## Done when (testable)
- Test: the menu draw adds the entries only when the button operator is `select_light`, and nothing for other buttons (the group menu still works).
- Test: Rename changes `obj.name` and leaves `obj.data.name` unchanged, also for light data shared by two objects.
- Test: Solo from the menu solos the clicked light, and running it again ends the solo.
- Test: Rename is disabled for a library light.
- `make test` passes.
- Manual (GUI): right-click a light's name and check that the three entries sit above Blender's own entries. Rename one light and frame another.

## Afterwards
Append a `## v6 task 05: Light right-click menu` entry to ARCHITECTURE.md (how the menu finds the light, the final entry order). Add the menu's operators to `tests/smoke_engines.py`.
