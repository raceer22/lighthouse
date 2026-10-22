# Suggested features

Suggestions for making Lighthouse smoother to use, collected after the v5 release (1.3.0). Items 1–6 build on `new-features.md`. Items 7–11 are new. **Decided** in `v6-decisions.md`. This file is kept as the record of the original suggestions and their open questions.

Suggested order: 1 (Sun fix) → 3 + 4 (follow selection, Active Light panel and panel order) → 7 (row right-click menu) → 5 (additive solo), then the rest.

## From `new-features.md`

### 1. New lights: Sun starts 10× too bright (bug)

- `LIGHTHOUSE_OT_add_light` creates lights with `bpy.data.lights.new()`. Checked in 5.2.2:

  | Type | `bpy.data.lights.new` | Shift+A |
  |---|---|---|
  | Point | 10 W | 10 W |
  | Spot | 10 W | 10 W |
  | Area | 10 W | 10 W |
  | Sun | **10 W/m²** | **1.0 W/m²** |

- Fix: start a Sun at Shift+A's 1.0 W/m², so Lighthouse lights match the ones Blender adds.
- Why: a new Sun is 10× brighter than the one from Shift+A and blows out the scene.

### 2. New lights: "too small"

- Point, spot and area lights already match Shift+A (10 W), so the complaint is about Blender's defaults, not a difference from them.
- Proposal: a Preferences setting, **"New lights start from preset"**, with one dropdown per light type (or one for all types). New lights get that preset's power, color, radius and Kelvin. If it's empty, Blender's defaults apply.
  - Why: it reuses the preset code and files that already exist. It also covers the "configurable starting temperature" item from `new-features-decisions.md`.
- **Open questions**:
  - What does "too small" mean: power (dim), radius (sharp shadows), or the light's size in the viewport?
  - One preset per type, or one for all types? A Sun preset uses W/m², so one preset can't suit both suns and the other types.
  - Does a missing or deleted preset fall back to Blender's defaults silently, or with a warning?
  - Should it also apply to Shift+A? (So far, decision 9 says only Lighthouse's New Light.)

### 3. Viewport selection shows the light in the list

- **Follow selection, without writing anything**: while drawing, treat the active light as expanded and its collapsed groups as open. Nothing is written to `expanded` or `lighthouse_collapsed`, so no handler or msgbus is needed, it adds no undo steps, and the list goes back to normal when the selection changes.
  - The existing Reveal button (`lighthouse.reveal_active_light`) stays, for opening the groups permanently.
  - A header toggle could turn following on and off, for artists who don't want the list to change as they click in the viewport.
- **The catch**: a sidebar panel can't scroll itself to a row. In a long list, the active light's row and details may be out of view, which is why item 4 matters.
- **Open questions**:
  - On by default?
  - Should a light that the search or type filter hides still be shown when it's active?
  - Should a selection of more than one light open all of them, or only the active one?

### 4. Panel order: Lights at the bottom, plus an Active Light panel

- New **Active Light** panel: the active light's name, type, power, color or Kelvin, mute and solo, then its details and light linking (the same sections as the row details). If the active object isn't a light, it shows a short message, or the panel hides itself through `poll`.
  - Why: this solves item 3's scrolling problem. The selected light is always visible and editable, wherever its row is in the list.
- New order: **Active Light → World → Intensity → Presets → Lights**, set with `bl_order`.
  - Why: Lights takes the most space, so it goes last and the short panels stay at a fixed place.
- Consider starting Intensity and Presets closed (`bl_options = {'DEFAULT_CLOSED'}`).
- **Verify**: Blender saves panel order the user dragged in the screen layout. `bl_order` sets the order of new layouts, and may not change files where panels were already rearranged.
- **Open questions**:
  - If the Active Light panel shows the details, should the row's details stay?
  - What does the panel show when the active light is read-only (from a library)?

### 5. Shift+click on solo adds to the current solo

- Click on the solo icon (the star): solo only this, as now. Shift+click: add it to the current solo, or remove it if it's already soloed.
- The solo state (`LIGHTHOUSE_PG_solo`) currently holds one `light` or one `group`. It would need to become a collection of targets, with the visibility snapshot left unchanged.
- **Open questions**:
  - Can lights and groups be mixed in one solo?
  - Does removing the last item end solo, like Exit Solo?
  - Does Shift+click on the World's star add the World to a lamp solo, or stay World-only (decision 17)?
  - Does a plain click while several items are soloed replace them all with this one?
  - Muting a light that's part of the solo: same rules as today?

### 6. Picking an HDRI

- A **Load HDRI…** button in the World panel opens Blender's image browser and puts the chosen image into the Environment Texture node that the panel already detects. With no Environment Texture node, the button could add one before the Background node.
- Why: comparing HDRIs while lighting is common, and the panel already finds the node.
- **Open questions**:
  - Should the old image be kept in the file, or cleared if nothing else uses it?
  - Should the button also appear for custom world setups, or only simple ones?

## New suggestions

### 7. Right-click menu on light rows

- Prepend Lighthouse entries to `UI_MT_button_context_menu` for a light's name button, the same way as the group menu: **Rename, Frame, Duplicate, Delete, Apply Preset ▸, Mute, Solo, Add to Solo**.
- Why: the modifier clicks (Shift, Ctrl+Shift, Ctrl, Alt) only show in the tooltip, so most users never find them. The list also has no way to delete or duplicate a light.
- **Open questions**:
  - Duplicate: linked data (Alt+D) or a full copy (Shift+D)? Or both?
  - Delete: delete right away (undoable) or ask first?
  - Do these act on the clicked light only, or on every selected light when the clicked one is selected?

### 8. Alt+drag edits every selected light

- In Blender, Alt+drag (or Alt+Enter) on a value applies it to every selected object.
- **Verify**: whether it works on Lighthouse's power, color and Kelvin fields, which edit `obj.data` from a panel.
  - If it works: mention it in the tooltip and the README.
  - If it doesn't: decide whether row edits should spread to the selection, since that's what users will expect.

### 9. Speed with many lights

- `LIGHTHOUSE_PT_lights.draw()` rebuilds the list (`list_entries`, `row_state`, `linking_counts`) on every redraw, with no cache.
- Proposal: a benchmark test that times one draw pass in a scene with about 500 lights in nested collections, with a budget (for example under 10 ms). Cache by depsgraph update only if it goes over budget.
- Why: big interior and archviz scenes are the add-on's main use, and a slow sidebar makes the whole viewport feel slow.

### 10. Empty scene

- With no lights in the view layer, show a large **Add Light** button (the same `+` menu) under the message, not just text.
- Why: the first thing a user does in an empty scene is add a light. Right now they have to find the small `+` in the header.

### 11. Finding and installing the add-on

- A short GIF or screenshots at the top of the README: list, solo, EV steps, light linking.
- Publish on extensions.blender.org, so users can install it from inside Blender and get updates automatically.
- **Open question**: does the extension meet the platform's review rules as it is (manifest, permissions, license)? `make validate` covers the manifest only.

## Still out of scope

These items from `new-features.md` stay out of scope. They're listed so they aren't suggested again:

- Batch rename selected objects
- Duplicate object with a middle-mouse click (item 7's Duplicate is a menu entry instead)
- Menu for custom key bindings
- Focus on a collection
- Changing the light linking collection
- Reflection of a light's settings
- Every light setting from across Blender in the details (for example spot softness)
- Active camera picker

Added after the v6 review (see `v6-decisions.md`):

- New lights start from a preset (item 2): parked, since "too small" was the Area size bug, now part of item 1
- Following the viewport selection in the list (item 3): parked, the Active Light panel covers it
- Large Add Light button in an empty scene (item 10)
- README media and publishing on extensions.blender.org (item 11)
