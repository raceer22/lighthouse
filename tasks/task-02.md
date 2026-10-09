# Task 02: Lights grouped by collection

**Depends on:** task-01
**PRD-v2 sections:** Lights list header (grouped/flat toggle), Groups, Light rows (info icon, indentation) · **AC:** 3, 4, 5, 6

## Goal
The Lights panel shows lights nested under the view layer's collections, as in the outliner, with a grouped/flat toggle. In this task group headers only show a name and a count. Collapsing and the header buttons come in task 03.

## Scope
- `lighthouse/lights.py`: a pure function such as `list_entries(view_layer, name_filter, type_filter, grouped)` that returns the ordered rows to draw:
  - **group entries:** collection, depth, count
  - **light entries:** object, depth, number of other listed collections it is in

  `draw()` only iterates over these entries, and tests assert on them.
- Building the tree:
  - Walk `view_layer.layer_collection` recursively and skip layer collections with `exclude` set. Child collections keep their outliner order (`children`). Lights inside a group are sorted by name, ignoring case, as in v1.
  - Keep a collection only if its subtree contains a listed light. Its ancestors are kept for the path even when they hold no lights themselves.
  - Lights linked directly to the Scene Collection go at depth 0 with no header, after the top-level groups (outliner order).
  - The type filter applies, so groups with no light of that type disappear.
  - A light linked into several collections gets an entry under each one. Every entry edits the same object.
  - **Count:** the number of unique listed lights in the group and all its sub-collections. It follows the type filter, and a light in two sub-collections counts once.
- **Flat mode:** when `grouped` is off, or while the search field is non-empty, return the v1 `listed_lights()` order at depth 0 with no headers.
- Add `grouped: BoolProperty(default=True)` to `LIGHTHOUSE_PG_settings` (WindowManager, so it is not saved and not part of undo) and draw it as an icon toggle next to the search field.
- **Group header (this task):** indentation, collection icon and the label `Name (N)`.
- **Indentation:** each level indents by a fixed small step, for example `row.separator(factor=…)`. Put the cap in a small helper (`min(depth, 3)`) so it can be tested.
- **Info icon:** replace `LIGHTHOUSE_OT_shared_light_info` / `LINKED` with one `INFO` button, `LIGHTHOUSE_OT_light_info` (`INTERNAL`, no-op).
  - It is shown when the light data is shared, or when the object is in other listed collections (grouped view only).
  - Its tooltip comes from a `description(cls, context, properties)` classmethod and names whichever case applies, for example "Light data is shared with 2 other objects" or "Also in 1 other collection".

## Out of scope
Collapse, header buttons (select, move, hide, solo), new dimming rules (task 03). Row layout changes (task 05).

## Done when (testable)
- Test: with `Set/Interior/Lamps` as the only collection holding a light, the entries are `Set` (0) → `Interior` (1) → `Lamps` (2) → the light (3) (AC 3).
- Test: an empty collection, and a collection holding only meshes, produce no entries. A Scene Collection light is a depth-0 light entry with no header (AC 3).
- Test: a collection excluded from the view layer produces no header, and its lights are not listed.
- Test: with `grouped=True`, a non-empty search returns flat entries with no groups. Clearing the search returns grouped entries again (AC 4).
- Test: a light linked into `A` and `B` appears under both, with 1 other collection each time. In flat mode it appears once with 0 (AC 5).
- Test: a parent group's count includes nested lights. A light in two sub-collections counts once. Setting the type filter changes the counts and drops groups with no light of that type (AC 6).
- Test: the indent helper caps at 3.
- `make test` passes.
- Manual (GUI): the grouped view matches the outliner's nesting, the toggle switches modes, and the info icon tooltip names the right case.

## Afterwards
Append a `## v2 task 02: lights grouped by collection` entry to ARCHITECTURE.md with (1) new components, (2) how data flows between them, (3) Blender API quirks encountered.
