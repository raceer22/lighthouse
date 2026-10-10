# Task 06: Empty-state message above the collection tree

**Depends on:** task-05
**Group:** Collections · **Source:** `.notes/new-features-decisions.md` item 9

## Goal
When no lights match and empty collections are shown, the panel still draws the collection tree under the message. The collections stay reachable as targets for `+`, Move here and New Collection.

## Scope
- `LIGHTHOUSE_PT_lights.draw()`, when `empty_message()` returns a message:
  - **Grouped, no search, `show_empty` on:** draw the message (plus Clear Filters when a filter is the cause, as today) above the tree, then draw `list_entries()` as usual. Every count is `(0)`.
  - **`show_empty` off, or flat mode:** today's behaviour, which is the message and then return.
  - **Search:** stays flat, with no collections: the message and Clear Filters, then return.
- Keep the branch in a small helper (for example `lights.tree_under_message(grouped, name_filter, show_empty)`) so it can be tested without drawing.
- `empty_message()` wording is unchanged ("No lights match the filter" / "No lights in this view layer").

## Done when (testable)
- Test: in a view layer with no lights and collections `Set/Lamps`, `list_entries(show_empty=True)` returns both collections, nested, with count 0.
- Test: with type filter `SUN` and only point lights, `list_entries(show_empty=True)` returns the full tree with zero counts.
- Test: the helper returns `True` only when grouped, not searching and `show_empty` is on.
- `make test` passes.
- Manual (GUI): with a type filter that matches nothing, the message and Clear Filters sit above a `(0)` tree. With `show_empty` off, only the message shows. A search that matches nothing shows only the message.

## Afterwards
Update the v3 task 04 note in ARCHITECTURE.md that says the panel always returns early, and append a short `## v4 task 06` entry.
