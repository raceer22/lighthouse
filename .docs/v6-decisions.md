# v6: decisions

Settled while reviewing `suggested-features.md` (item numbers there are given in brackets). Each item gives the decision and, where it wasn't obvious, why. Items marked **Verify** depend on Blender behavior that must be checked before building on it.

## New light defaults [1, 2]

1. **New lights match Shift+A.** After `bpy.data.lights.new()`, the add-light operator applies a small table of the values where Shift+A differs (checked in 5.2.2):

   | Type | `lights.new` | Shift+A |
   |---|---|---|
   | Sun | 10 W/m² | **1.0 W/m²** |
   | Area | 0.25 × 0.25 m | **1.0 × 1.0 m** |

   Point and Spot already match (power, radius, spot size), so they have no entry.
   - Why a table: one place to add a type if Blender's two code paths drift apart again.
   - The "too small" complaint in `new-features.md` was the Area size, not Blender's defaults. With this fix, the "start from preset" setting isn't needed for now (parked).

## Speed with many lights [9]

2. **A benchmark script, not a test**: `make bench` builds a scene with about 500 lights in nested collections, times one `LIGHTHOUSE_PT_lights.draw()` pass headless, and prints the result. It's not part of the test suite and has no budget that fails.
   - Why: a timing budget fails at random on a busy machine. The number is compared by hand before a release.
   - Caching (by depsgraph update) is only added if the number calls for it. Under about 10 ms, it's done.
   - It runs first, so there's a baseline before the Active Light panel draws a second set of details.

## Active Light panel and panel order [4]

3. A new **Active Light** panel shows the active light's name, type, power, color or Kelvin, mute and solo, then its details and light linking, the same sections as a row's details.
4. **Active object isn't a light** (or nothing is active): the panel shows a short *"Select a light"* message. It isn't hidden through `poll`.
   - Why: hiding it would make every panel below jump up and down as you click between meshes and lights.
5. **Read-only lights** (library or system override) show greyed out, with the same `state.read_only` rule as rows.
6. **Row details stay.** Rows still expand, and the panel repeats the details for the active light.
   - Why: expanding several rows at once is how lights get compared side by side.
7. **Order**: **Active Light → World → Intensity → Presets → Lights**, set with `bl_order`. This replaces v5 decision 12's order.
   - Why: Lights is the tallest, so it goes last and the short panels stay at fixed places.
   - **Verify**: whether `bl_order` changes layouts where the user already dragged panels, or only new ones.
8. **Presets starts closed** (`DEFAULT_CLOSED`). Intensity stays open, since EV steps are used all the time while lighting.
9. Following the viewport selection in the list (item 3) is **not built**. The Active Light panel solves the same problem without the list jumping, and the Reveal button stays for showing where a light sits in the list.

## Right-click menu on light rows [7]

10. **Right-click on a light's name** prepends Lighthouse entries to `UI_MT_button_context_menu`, the same way as the group menu (v5 decision 1): **Rename, Frame, Duplicate, Duplicate Linked, Delete, Apply Preset ▸, Mute, Solo, Add to Solo**.
    - Why: the modifier clicks only show in tooltips, and the list had no way to delete or duplicate a light.
11. **What the entries act on**:
    - **Delete, Duplicate, Duplicate Linked, Mute, Apply Preset**: every selected light when the clicked light is selected, otherwise only the clicked light (the Outliner's rule). Labels show the count, for example "Delete 3 Lights".
    - **Rename, Frame, Solo, Add to Solo**: only the clicked light.
    - Why: Rename only makes sense for one light, View Selected already frames a selection, and soloing several lights is what Add to Solo is for.
12. **Duplicate** makes a full copy (Shift+D). **Duplicate Linked** shares the light data (Alt+D). Both put the copy in the same collection as the original, with no move or grab afterward. Shared data already shows in the row's ⓘ tooltip.
13. **Delete** removes the object right away, with no confirmation, and Ctrl+Z brings it back. Only the object is removed. Light data with no users left is cleaned up by Blender, as with the Outliner's Delete.
14. **Mute on a mixed selection follows the clicked light**: if it's unmuted, every light in the selection is muted, and if it's muted, they're all unmuted. The label says which ("Mute 3 Lights" / "Unmute 3 Lights").
    - Why: toggling each light scrambles a mixed selection. This matches Ctrl+click on the Outliner's eye.
15. **Rename** opens a small popup with a name field (`invoke_props_dialog`), like F2, and renames **only the object**.
    - Why: the row's name is an operator button, not a text field. Renaming the data too would surprise people who name shared light data on purpose.

## Additive solo [5]

16. **Shift+click on a star** adds that light or group to the current solo, or removes it if it's already soloed. A plain click works as now.
    - `LIGHTHOUSE_PG_solo` holds a collection of targets (each a light or a group) instead of one `light` or `group`. The visibility snapshot is unchanged.
17. **Lights and groups mix freely** in one solo. The visible set is the union: each soloed light, plus every light in each soloed group.
18. **Removing the last item ends solo**, exactly like Exit Solo.
19. **A plain click while several items are soloed replaces them** with the clicked item, even if it was already part of the solo. Clicking the star of the only soloed item still ends solo, as now.
20. **Shift+click on the World's star works like a plain click**: World-only solo, which replaces any lamp solo.
    - Why: a lamp solo already leaves the World on (v5 decision 17), so "lamps + World" needs nothing extra.
21. **Mutes made during a solo stick** through later Shift+adds, removes and replaces. Each snapshot item gets a "muted during solo" flag, set when the light is muted and cleared when it's unmuted (in `update_snapshot`). Recomputing visibility keeps those lights hidden.
    - Why: without it, adding to a solo would quietly show a light you just muted.
22. **Exit Solo tooltip**: up to 3 names, then "…" ("Exit Solo (Key, Practicals, Rim, …)"), following `shared_label`. Deleted targets are dropped from the list.
23. **Supersedes** v5 decision 17's "only one thing is soloed at a time" for lamps and groups. The World stays exclusive: a World solo still replaces a lamp solo, and the other way round.
    - **Verify**: how files saved in the middle of a solo with the old single-target `LIGHTHOUSE_PG_solo` load after the change.

## Load HDRI [6]

24. A **Load HDRI…** button in the World panel opens Blender's image browser and puts the chosen image into the Environment Texture node.
    - **Simple setups**: swaps the image, or, with only a Background node, adds an Environment Texture before it (and leaves Rotation to the existing Add Rotation button).
    - **Custom setups with exactly one Environment Texture node**: only swaps the image and never adds nodes.
    - Other custom setups: no button.
    - Why: swapping an image is safe in any tree with one Environment Texture. Adding nodes is only safe where the panel fully understands the tree.
    - **Verify**: the added node matches what the panel's detection (v5 decision 14) and Add Rotation (v5 decision 15) expect.
25. **The previous image is left to Blender**: it loses a user and is dropped when the file is saved and reopened. Lighthouse doesn't remove it or give it a fake user.

## Alt+drag [8]

26. **Alt+drag already works** on the row's power, color and Kelvin fields (checked). Mention it in the README.
    - Why not the tooltips: those fields are Blender's own Light properties drawn with `layout.prop`, which can't take a custom tooltip.

## Delivery

27. **1.3.1** (patch): new light defaults (decision 1), on its own.
28. **1.4.0**: one feature release, in this order:
    1. Benchmark (decision 2)
    2. Active Light panel and panel order (decisions 3–9)
    3. Right-click menu on light rows (decisions 10–15). Add to Solo arrives with step 4.
    4. Additive solo (decisions 16–23)
    5. Load HDRI (decisions 24–25)
    6. Alt+drag docs (decision 26)

## Out of scope (atm)

- New lights start from a preset (item 2): parked, since the "too small" complaint was the Area size bug. Also covers a configurable starting temperature.
- Following the viewport selection in the list (item 3): parked, the Active Light panel covers it.
- Large Add Light button in an empty scene (item 10)
- README media and publishing on extensions.blender.org (item 11)
- Everything in `suggested-features.md` → "Still out of scope"
