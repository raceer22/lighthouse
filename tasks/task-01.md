# Task 01: Right-click a collection to add there

**Depends on:** none
**Group:** Group menu · **Source:** `.notes/new-features-decisions.md` items 1–5

## Goal
Right-clicking a collection header, or the Scene Collection row, shows **New Light ▸** and **New Collection** at the top of Blender's context menu. New Light adds the light into that collection and makes the collection active. New Collection creates a collection inside it and makes the new one active. On a library collection both entries are greyed out. Left click and Ctrl+click work as before.

## Verify first
- In `UI_MT_button_context_menu`, `context.button_operator` returns the clicked button's operator properties, and their type tells a Lighthouse header button from any other (for example `bl_rna.identifier == "LIGHTHOUSE_OT_set_active_collection"`). Check this in the GUI with a throwaway draw function that prints it.
- The target reaches the New Light ▸ submenu. The likely route is `layout.context_pointer_set()` before `layout.menu()`. If the pointer doesn't reach the submenu, draw the four light types inline instead, one operator per type.

Record what works under "Blender API quirks" in the ARCHITECTURE.md entry.

## Scope
- `lighthouse/__init__.py`:
  - `add_light` gets hidden `name` and `library` properties (filled by `target()`) and `use_active` (default `True`). All three have `SKIP_SAVE`, so a call never reuses the previous call's target.
    - With `use_active` off, it adds into `scene_or_collection(name, library)`, so `name=""` is the Scene Collection. It then makes that collection active (item 3).
    - With `use_active` on, it adds to the active collection as it does today. Existing calls and the header `+` don't change.
  - `new_collection` gets the same three properties for its parent. Its dialog field is renamed from `name` to `new_name`, as in the rename dialogs, so that `target()` can set `name`. Update the one test that passes `name=`.
  - Both operators cancel when the target doesn't exist, and refuse a read-only target as they do today.
  - `LIGHTHOUSE_MT_new_light`: one entry per `LIGHT_TYPES` item. It targets the collection it was given, or the active collection when it was given none (task 02 uses that case).
  - `draw_group_menu(self, context)` is prepended to `UI_MT_button_context_menu` in `register()` and removed in `unregister()`. When the button under the cursor is a header's name button (`set_active_collection`, which covers group headers and the Scene Collection row), it draws New Light ▸, New Collection and a separator. For any other button it draws nothing.
  - On a read-only collection (`is_read_only`), the two entries are drawn disabled (item 5).
- `tests/blender_runner.py`: move the `Recorder` fake layout here from `tests/test_restore_in_preferences.py`. Add `menu`, `operator_menu_enum`, `separator`, `context_pointer_set` and an `enabled` attribute, so this task and later ones can check draw code headless.

## Open questions
Not decided: which header buttons get the menu. Default: only the name button. It covers both row types with one rule, and the icon buttons (Select, Move here, Hide, Solo) keep Blender's plain menu.

## Out of scope
The header `+` (task 02).

## Done when (testable)
- Test: with `Props` active, `add_light(type='SPOT', name="Set", use_active=False)` links the new light into `Set` only, selects it, makes it the active object and makes `Set` the active collection.
- Test: a following `add_light(type='POINT')` with no target adds to `Set` (now active). The previous target didn't stick.
- Test: `add_light(type='POINT', name="", use_active=False)` links into `scene.collection` and makes the master layer collection active.
- Test: with `Props` active, `new_collection(name="Set", use_active=False, new_name="Fill")` creates `Fill` inside `Set` and makes `Fill` active.
- Test: a target that doesn't exist cancels and adds nothing. A linked target raises `RuntimeError` and adds nothing.
- Test (Recorder): with a fake `button_operator` for `Set`'s name button, `draw_group_menu` draws the New Light menu, then New Collection targeting `Set`, then a separator, in that order. With a fake `button_operator` for the Scene Collection row it targets `name=""`. For another operator, or no operator, it draws nothing.
- Test (Recorder): for a linked collection the entries are drawn on a layout with `enabled = False`.
- Test: `draw_group_menu` is in `UI_MT_button_context_menu`'s draw functions after `register()` and gone after `unregister()`.
- `make test` passes.
- Manual (GUI): right-clicking a header shows the Lighthouse entries above Copy Python Command and Assign Shortcut, with a separator between them. New Light ▸ Area adds an Area light to that collection and its header becomes pressed. The Scene Collection row works the same way. A library collection shows both entries greyed out. Right-clicking a light row or the search field shows no Lighthouse entries. Click still activates and Ctrl+click still renames.

## Afterwards
Append a `## v5 task 01: group context menu` entry to ARCHITECTURE.md. Add `add_light` and `new_collection` calls with a target, including `name=""`, to `tests/smoke_engines.py`.
