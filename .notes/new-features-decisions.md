# New features: decisions

Settled while reviewing `new-features.md`. Each item gives the decision and, where it wasn't obvious, why.

## Objects: foldable lights row

1. A collection's direct lights fold under a `Lights (N)` row, but only when the collection has its own lights **and** at least one listed sub-collection. A leaf collection lists its lights directly, as today.
   - Why: in a leaf collection, folding the lights row would hide the same thing as folding the collection.
2. The fold state is stored on each collection, like `lighthouse_collapsed`. It is saved in the .blend file, adds no undo step and starts open. Reopening a collection keeps its lights row as you left it.
   - Why: if reopening a collection always opened its lights row, a big collection would show all its lights every time, which is the problem this feature solves.
3. Expand All also opens every lights row. Collapse All only collapses collections. The "are all collapsed?" check, which picks the icon, looks only at collections.
4. The lights row has a triangle, an icon and `Lights (N)`, and no action buttons.
   - Shift+click range selection skips folded lights rows, the same way it skips collapsed groups.
   - The collection header's count and Select still include every light in the collection.

## Collections

5. **Scene Collection row**: a header at the top that doesn't indent the tree, so top-level collections stay at depth 0.
   - It has a triangle for its own lights, which does the job of the lights row from item 1, and a **Move selected here** button.
   - It has no Hide or Solo, because the master collection has no hide flags of its own.
6. **Show empty collections**: a toggle icon next to the grouped toggle, on by default. It lives on the WindowManager, so it isn't saved or undone, and Clear Filters doesn't reset it.
   - On: every non-excluded collection is listed. Under a type filter, a collection without matching lights shows `(0)`.
   - Off: the list is exactly today's, keeping only collections with matching lights.
7. **Fold triangle**: shown when a collection has anything under it, meaning its own lights or listed sub-collections (empty ones included). A collection with nothing under it gets a blank space of the same width, so names stay aligned.
8. **Header buttons on a collection with no matching lights**: Select and Solo are greyed out, and Move here and Hide stay enabled. All four are still drawn so the columns line up.
9. **When no lights match**:
   - With show-all on, the message (plus Clear Filters when a filter is the cause) is drawn above the collection tree, and the tree shows `(0)` counts.
   - With show-all off, the panel does what it does today: it shows only the message and stops.
   - Search stays flat, with no collections.
10. **Target folder** is Blender's active collection (`view_layer.active_layer_collection`).
    - Clicking a collection's name makes it active. The Scene Collection works the same way. The active collection's name is drawn pressed, like the active light's.
    - It stays in sync with the Outliner and with Shift+A in the viewport, and it doesn't touch object selection.
    - `add_light` already links new lights into it. A library collection is refused there.
11. **New collection**: a button in the list header that creates a collection inside the active one and makes the new collection active. It refuses to create inside a library collection.

## Features

12. **Reveal active light**: a header button that unfolds every collection and lights row hiding the active light.
    - It's greyed out when the active object isn't a light.
    - It doesn't run on its own when the selection changes, because it would undo your folding and mark the file as changed.
    - The panel can't be scrolled from Python, so it can't jump to the row.
    - A light added with `+` into a folded collection is revealed automatically.
13. **Intensity scope** starts as Selected. It lives on the WindowManager, so every session starts at Selected.
14. **Presets become plain files**: on first run, the built-ins are written to the presets folder as normal JSON presets. A marker file records that this happened, so deleted presets don't come back on restart.
    - From then on, any preset can be deleted, overwritten or re-saved.
    - This removes the built-in vs user distinction: the reserved-name check, the `CANDLE` fallback and the `USER` icon.
    - The dropdown shows plain names with no icons, sorted alphabetically.
15. **Restore default presets** is a button in the Presets panel, next to Save and Delete. It re-adds missing defaults only, so it never overwrites edits and needs no confirmation. To reset an edited default, delete it and press Restore.
16. **Deleting the preset that's shown** selects the next one. With no presets left, the dropdown is empty and Apply is greyed out. The panel already handles an empty value.
17. **Known cost of 14**: a built-in's dropdown key changes from `CANDLE` to `USER:Candle`. A .blend file saved with a built-in selected therefore opens with nothing selected.

## Out of scope (atm)
- Batch rename selected objects
- Duplicate object (middle mouse click)
- Menu for custom bindings
- Renaming collections from the panel (Ctrl+click like lights would be cheap later)
