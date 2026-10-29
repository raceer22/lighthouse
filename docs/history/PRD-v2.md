# Lighthouse: PRD v2

> Requirements as of v2, kept as a record. Later versions changed some of them; see [ARCHITECTURE.md](../ARCHITECTURE.md) for current behavior.

Follow-up to [PRD.md](PRD.md). Everything there still holds unless this document changes it. The changes are listed under [Changes to PRD.md](#changes-to-prdmd).

## Problem

The first version works, but it stops scaling once a scene has more than a handful of lights:

- The list is flat, so it ignores how the scene is organised in collections, and there is no way to hide, solo or select a whole set of lights.
- Opening several detail sections makes the panel long and messy, and each one has to be closed by hand.
- Selecting from the panel always replaces the selection, and rows don't show what is selected. That makes the "Selected Lights" scope, presets and any bulk action guesswork.
- Exposure only moves in whole EV steps, which is too coarse. The factor slider's bar is pinned to the left because of its soft max.
- A light's type and name can only be changed outside the panel.
- The unit label takes a third of the row's width, which leaves a gap between power and color.
- Light `exposure` and Kelvin `temperature` are ignored. When they are set, the row's power and the result of a preset are wrong.
- The Intensity and Presets boxes always take about 7 rows above the list.

## Solution

### Panel layout
- The Lights tab has three top-level panels that can each be collapsed and reordered by dragging: **Intensity**, **Presets** and **Lights**. Blender remembers their open/closed state and order.
- The Presets panel header is just its label. The body holds the preset dropdown and Apply, then Save (`+`) and delete (`-`).

### Intensity
- The factor is a plain number field (no slider bar), default 1.0.
- The EV row has six buttons: **−1, −½, −¼, +¼, +½, +1**. `lighthouse.step_exposure` takes a float `steps` and multiplies power by `2 ** steps`.
- EV and factor still scale `energy` (and its keyframes) as in PRD.md. They never change a light's own `exposure`.

### Lights list header
- Search field and type filter, as before.
- A **grouped/flat** toggle. Grouped is the default. While the search field is non-empty, the list is flat whatever the toggle says, and it goes back to the toggle's mode when the search is cleared. The toggle lives on the WindowManager, so it is not saved and not part of undo.
- A **collapse all groups** button (grouped view only).
- A small **`+`** button that opens a light type menu (Point, Sun, Spot, Area). The new light is created at the 3D cursor in the active collection, then selected and made active.

### Groups (grouped view)
- Groups are the view layer's collections, named after them and nested as in the outliner.
- A collection is shown only if it contains a listed light, directly or in a sub-collection. Its parent collections are kept for the path, even when they hold no lights themselves.
  - Example: if `Set/Interior/Lamps` is the only collection with lights, the tree shows `Set` → `Interior` → `Lamps`.
- Lights linked directly to the Scene Collection are listed at the top level with no group header.
- Within a collection (and at the top level), its own lights come first, sorted by name, then its sub-collections.
- Collections excluded from the view layer are not shown. Their lights are not in the view layer, as before.
- With a type filter active, groups that have no light of that type are hidden.
- A light linked into several collections gets a row under each one. All of those rows edit the same object.

**Group header**, left to right:
1. Disclosure triangle to collapse or expand the group.
2. Collection name and light count, for example `Interior (4)`. The count covers listed lights in the group and all its sub-collections, follows the type filter, and counts a light once even if it sits in two sub-collections.
3. **Select** icon: selects every light in the group, sub-collections included. Click replaces the selection, and Shift+click adds to it.
4. **Move selected here** icon: moves the selected lights into this collection, unlinking them from every other collection. Read-only (library) objects are skipped.
5. **Hide** icon: toggles the collection's own `hide_render` and `hide_viewport`, the outliner's camera and monitor toggles. Light objects' flags are not touched, so a light muted on its own stays muted after the group is unhidden.
6. **Solo** icon (see [Solo](#solo)).

Groups have no power or color controls.

**Collapsed state**
- Stored on the collection (`Collection.lighthouse_collapsed`), so it is saved with the file.
- Toggled by an operator registered without `UNDO`, so collapsing and expanding never create an undo step.

### Light rows
The row stays on one line, left to right:

1. **Disclosure triangle** for the details.
2. **Type dropdown**, drawn as the current type's icon (`prop(light, "type", icon_only=True)`). It is disabled for read-only lights. On shared light data it changes every user, as the Properties editor does.
3. **Name button**:
   - Click: select only this light and make it active.
   - Shift+click: add this light to the selection or remove it.
   - Ctrl+click: open a rename popup with the current name filled in.
   - Alt+click: select only this light and frame it in the 3D viewport.
   - The tooltip lists all four.
   - Selected rows are highlighted, and the active light gets a stronger highlight.
4. **Info icon**, shown only when needed. It replaces the separate `LINKED` icon and covers two cases, with a tooltip naming whichever apply:
   - the light data is shared with other objects;
   - the object is also in N other collections (grouped view only).
5. **Power** field. It takes all remaining width.
6. **Unit label** (`W` or `W/m²`) in a fixed-width sub-row of about 1.5 UI units. This removes the gap between power and color.
7. **Color swatch**, fixed at about 2 UI units. If the light uses temperature, it is replaced by a **Kelvin** field.
8. **Mute** and **Solo**, as before.

Each nesting level indents the row by a fixed small step. Indentation stops growing after 3 levels, so deep trees don't eat the row.

Rows are dimmed when `obj.visible_get(view_layer=...)` is false, so lights inside a hidden group show dimmed. A row only shows as muted when its own object flags are hidden.

### Light details
- **Accordion:** opening a light's details closes every other open detail section. Shift+click on the triangle opens it without closing the others.
- Which details are open is stored on the WindowManager as object pointers. It is not saved, not part of undo, and survives renames. `Object.lighthouse_expanded` is removed.
- The details box gains, in order:
  - **Name** field at the top.
  - **Exposure**, where `Light.exposure` exists.
  - **Use Temperature** and **Temperature** (K), where `Light.use_temperature` exists (Blender 5.0+).
  - The existing soft size, influence, shadow and Cycles settings.

### Solo
- One solo slot per scene. It holds either a light or a group, and switching between them keeps the first snapshot, as switching between lights does today.
- **Soloing a light** shows that light, hides every other light (object flags), and unhides every collection above it.
- **Soloing a group** shows every light in the group and its sub-collections, hides every other light, and unhides the group, its sub-collections and the collections above it.
- **Snapshot:** the first solo saves every light's `hide_render`/`hide_viewport`, plus the flags of each collection it changes. Un-solo restores all of them exactly.
- **Storage:** the snapshot is a `Scene` collection property whose items hold a `PointerProperty` to the object or collection and its saved flags. The JSON string `scene["lighthouse_solo"]` is no longer used. Pointers survive renames done anywhere, the snapshot is saved in the .blend file and recorded by undo, and items whose target was deleted are skipped.

### Kelvin and exposure
- Rows show a Kelvin field instead of the color swatch for lights with `use_temperature` on.
- Presets store `exposure`, `use_temperature` and `temperature` alongside power, color and radius.
  - Applying a preset sets them all. On Blender versions without `use_temperature`, only the RGB color is set.
  - User preset files saved before v2 load with exposure 0 and temperature off.
  - Saving a preset from a light records whichever color mode the light uses.
- Built-in presets use Kelvin, with an RGB fallback:

| Preset | Kelvin | RGB fallback |
|---|---|---|
| Candle | 1850 K | current Candle color |
| 60W Bulb | 2700 K | current 60W Bulb color |
| Daylight | 5500 K | current Daylight color |

## Constraints

Same as PRD.md, plus:

- Python panels can't do drag and drop or reliable double-click detection. Moving lights uses the group header icon, and renaming uses Ctrl+click or the Name field.
- Every property added in Blender after 4.2 (`use_temperature`, `temperature`, and `exposure` if it is not present on 4.2) must be looked up before use, so the addon still runs on 4.2.
- Operators that change scene data keep `UNDO`. Operators that only change panel state (collapse, accordion) don't.

## Acceptance Criteria

1. Intensity, Presets and Lights are three separate panels in the Lights tab. Each can be collapsed and reordered, and the Presets header is a plain label with the dropdown and Apply in the body.
2. The factor field has no slider bar and defaults to 1.0. Each of the six EV buttons multiplies power by `2 ** steps`, for example +¼ turns 100 W into ≈118.92 W.
3. Grouped view shows lights nested under their collections as in the outliner. Collections without lights are left out unless they are on the path to one, and Scene Collection lights appear at the top level.
4. Typing a search switches the list to flat. Clearing it restores the toggle's mode.
5. A light linked into two collections appears under both, with the info icon showing on its rows.
6. Group header counts include sub-collections, follow the type filter, and count a light once.
7. Group select selects every light in the group and its sub-collections, and Shift+click adds to the selection.
8. Move selected here leaves each selected, editable light in only the target collection.
9. Hiding a group toggles the collection's `hide_render` and `hide_viewport`. Unhiding it leaves a light muted before the hide still muted. Lights in a hidden group are drawn dimmed.
10. Soloing a light inside a hidden group makes it visible. Un-solo restores every light and collection flag exactly as before the first solo.
11. Group solo shows only that group's lights (sub-collections included), and switching between light and group solo keeps the first snapshot.
12. Renaming a light or collection during solo doesn't stop un-solo from restoring it.
13. Collapsing a group is saved with the file and creates no undo step.
14. Opening a light's details closes the others. Shift+click keeps the others open. Opening and closing details creates no undo step and is not saved.
15. Click, Shift+click, Ctrl+click and Alt+click on a name do select, toggle in selection, rename, and select-and-frame respectively. Selected and active rows are highlighted.
16. The type dropdown on a row changes the light's type, and one undo reverts it. It is disabled on library lights.
17. A row has no visible gap between power and color, and the unit label is still visible.
18. A light with temperature on shows a Kelvin field instead of the color swatch, and its details show Exposure and Temperature.
19. Built-in presets apply Kelvin on Blender 5.0+ and RGB on older versions. A user preset saved from a Kelvin light restores Kelvin, and a pre-v2 preset file still loads.
20. The `+` button adds a light of the chosen type at the 3D cursor in the active collection, and the new light is selected and active.
21. No errors on Cycles or EEVEE for any light type, on 5.2.2 and with temperature properties absent.

## Out of Scope

- Drag and drop between groups, double-click rename, and Ctrl/Shift range selection.
- Deleting lights from the panel.
- Showing or re-including collections excluded from the view layer.
- Migrating solo snapshots saved in the old JSON format. A file saved mid-solo with v1 has to be restored by hand.
- Shape parameters (spot size, area shape), which stay in the Properties editor.
- Everything still out of scope in PRD.md, except type switching.

## Changes to PRD.md

- **Type switching is now in scope.** "Changing a light's type" moves out of Out of Scope, and the light list line "Type switching ... stay in the Properties editor" now applies to shape parameters only.
- **Row layout:** the icon is a type dropdown, not part of the select button. The `LINKED` icon becomes the shared info icon.
- **Name click:** it gains Shift, Ctrl and Alt behaviours. A plain click still selects only this light.
- **Panel:** one panel with boxes becomes three panels.
- **EV buttons:** ±1 EV becomes six buttons, and `steps` becomes a float.
- **Solo storage:** the name-keyed JSON snapshot becomes a pointer-based property, which removes the known limit "a light renamed during solo is not restored". Solo now also covers collections.
- **Presets:** they store exposure and temperature as well as power, color and radius, and the built-ins use Kelvin.
- **Expanded state:** `Object.lighthouse_expanded` (saved, undoable) becomes WindowManager state (not saved, no undo).

## Additionally
- After implementing each task, append a brief entry to ARCHITECTURE.md detailing: (1) newly added components, (2) how data flows between them, and (3) key Blender API quirks encountered.
