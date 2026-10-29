# Lighthouse architecture

How the extension is put together as of 1.4.0: the modules, where state lives, how the main features work, and the Blender API quirks behind the less obvious choices. The reasoning for each feature as it was built is in the git history; the original requirements are in [history/](history/).

## Modules

Only `lighthouse/` is packaged. Imports run one way, so nothing lower down imports anything above it:

```
ui  →  operators  →  common, properties  →  presets  →  lights
```

| Module | Holds |
|---|---|
| `lights.py` | The logic, as plain functions over Blender data: which lights are listed and in what order, row state, solo, scaling, moving, deleting and duplicating, the World setup, light linking. The tests call it directly. |
| `presets.py` | `Preset`, the default presets, reading and writing preset files, `apply_preset()`. |
| `common.py` | Code several modules share: the presets folder and its cache, the preset enum items, enum item tuples (`LIGHT_TYPES`, `SCOPE_ITEMS`, `NEW_LIGHT_MODES`), target lookup helpers, `_lights_in_scope()`. |
| `properties.py` | The `LIGHTHOUSE_PG_*` property groups: panel settings and the solo snapshot. |
| `handlers.py` | App handlers: tracking the last active light, and migrating 1.3 solo files on load. |
| `preferences.py` | `LIGHTHOUSE_AP_preferences`: the New Light default and Restore Default Presets. |
| `operators/` | One module per kind of data acted on: `lights`, `groups`, `solo`, `world`, `presets`, `linking`, and `view` (folding, details, filters, which change only what is drawn). |
| `ui/` | `panels.py` (the five panels), `menus.py` (the `+` menus and the right-click entries), `draw.py` (row and details drawing shared by the Lights and Active Light panels). |
| `__init__.py` | Joins each package's `classes`, registers them, and adds the ID properties, menu entries and handlers. |

Each module ends with a `classes` tuple. Packages concatenate their modules' tuples, and `register()` registers the result in order.

Code inside the package must use relative imports, because an installed extension's module is `bl_ext.<repo>.lighthouse`, not `lighthouse`.

## Where state lives

Where a piece of state lives decides whether it is saved with the .blend file and whether it is part of undo.

| State | Stored on | Saved | Undo |
|---|---|---|---|
| Search, type filter, grouped, show empty, scale factor and scope, chosen preset, open details | `WindowManager.lighthouse` (`LIGHTHOUSE_PG_settings`) | no | no |
| Collapsed collection, folded lights row | `Collection.lighthouse_collapsed`, `Collection.lighthouse_lights_collapsed` | yes | no step of their own (the fold operators have no `UNDO`) |
| Solo targets and snapshot | `Scene.lighthouse_solo` (`LIGHTHOUSE_PG_solo`) | yes | yes |
| Color/Kelvin mode for new lights | `Scene.lighthouse_new_lights` (`FOLLOW`, `COLOR`, `KELVIN`) | yes | yes |
| Last active light | `Scene.lighthouse_last_light` | yes | yes |
| Default Color/Kelvin mode | add-on preferences | with the user preferences | no |
| Presets | JSON files in `extension_path_user()` | on disk, outside the .blend | no |

Panel open/closed state and drag order are stored by Blender in the screen layout, with no code here.

## How it works

### The light list

`LIGHTHOUSE_PT_lights.draw()` calls `list_entries()` on every redraw. Nothing is cached, so changes in the scene show up on the next redraw.

- **Which lights:** `light_objects()` is every `LIGHT` object in the view layer, hidden ones included. `listed_lights()` narrows it by type and by name (case-insensitive) and sorts by name. Bulk actions start from `light_objects()`, so the list filters never narrow them.
- **Grouped mode** (the default, when not searching) walks `view_layer.layer_collection` as the Outliner does, skipping excluded layer collections. It returns, in order:
  - `SceneEntry`: the Scene Collection header, always first.
  - `GroupEntry(collection, depth, count, foldable)`: a collection header. `count` is the number of distinct listed lights in its subtree.
  - `LightsEntry`: a foldable "Lights (N)" row, used only when a collection has both its own lights and sub-collections.
  - `LightEntry(obj, depth, other_collections)`: one light row.

  A collection lists its own lights first, then its sub-collections. Only collections on the path to a listed light are shown, unless `show_empty` is on. Collapsing a collection keeps its header and count and drops what's below it. Folding a lights row drops only that collection's own lights.
- **Flat mode** (grouped off, or any search text) is `listed_lights()` at depth 0 with no headers.
- A light in two collections gets two rows. Both hold the same `Object`, so they edit the same light, and `other_collections` drives the ⓘ tooltip.
- **Empty states:** `empty_message()` explains an empty list ("No lights in this view layer", or "No lights match the filters" with a Clear Filters button). With `show_empty` on in grouped mode, `tree_under_message()` still draws the collection tree under the message, so you can make a collection active or add to it.

### Rows and details

`ui/draw.py` holds `draw_light_controls()` (type, name, ⓘ, linking icon, power, unit, color or Kelvin, mute, solo) and `draw_light_details()`. Both the list and the Active Light panel use them.

- `row_state()` gives each row `dimmed` (not visible in the view layer, or render-hidden), `read_only` (library data or a system override, via `is_read_only()`), `muted` and `soloed`. Dimmed rows are drawn inactive and read-only controls disabled. The name button stays enabled, so a library light can still be selected.
- Controls are `prop()` calls on the light data, so they edit the same RNA as the Properties editor, with Blender's own undo. Alt+drag edits every selected light, as anywhere in Blender.
- `color_control()` picks `temperature` when the light uses it (5.0+), otherwise `color`.
- The details box shows the name, then `detail_properties(light, engine)`: the type's soft-size property, the light's influence factors and shadow, the newer properties (`NEWER_DETAILS`) where the light has them, and the Cycles settings under Cycles. It ends with the light linking section.
- Details work as an accordion: `toggle_details()` opens one light and closes the rest, unless Shift is held. Open lights are object pointers in `WindowManager.lighthouse.expanded`, so a rename keeps them open.

### Active Light panel

The panel draws the active object's row and details. When the active object isn't a light, it falls back to `Scene.lighthouse_last_light`, which a `depsgraph_update_post` handler (`handlers._track_last_light`) sets whenever a light becomes active. It has no `poll()`, so it never disappears and the panels below don't jump. With no light at all it says "Select a light".

### Targets and lookups

Operators that act on one light or collection take a `name` and a hidden `library` (the library filepath, `""` for local data). The draw code fills both with `target(op, id)`, and `find_object()` / `find_collection()` resolve them with `bpy.data.*.get((name, library))`. That keeps a local `Key` and a linked `Key` apart. An empty collection `name` means the Scene Collection, which isn't in `bpy.data.collections` (`scene_or_collection()`, `target_layer_collection()`).

### Selection and scope

- `select_light`'s `invoke()` maps the click's modifiers to an `action`: plain click selects, Shift selects a range in list order, Ctrl+Shift toggles, Ctrl renames, Alt frames. `execute()` does the work, so the tests pass `action` directly.
- The right-click entries use `light_scope()`, the Outliner's rule: the action applies to every selected light if the clicked light is selected, otherwise to the clicked light alone.
- Bulk actions (scale, EV step, Apply Preset, Move selected here) get their lights from `_lights_in_scope()`. When nothing is in scope, or every light in scope was skipped, they report why and return `CANCELLED`, so no empty undo step is pushed. These checks are in `execute()`, not `poll()`: `poll()` can't read the `scope` property, and a greyed-out button can't say why it's greyed out.

### Intensity

`scale_lights(lights, factor)` multiplies `energy` once per light datablock, so shared data isn't scaled twice. It skips read-only data and scales the `energy` F-curve's keyframes and handles too, so animation keeps its shape. An EV step is the same call with `2 ** steps`. Neither path touches `Light.exposure` or the World.

### Solo and mute

Mute hides a light in both viewport and render. Solo is a snapshot-and-restore on `Scene.lighthouse_solo`:

- **Targets:** `targets` holds the soloed lights and collections. A plain click replaces them, and Shift+click (`extend`) adds or removes one. The shown lights are the union of the soloed lights and every light in the soloed collections.
- **The snapshot:** `_solo()` records each light's `hide_render`/`hide_viewport` the first time solo touches it, and each collection's flags the first time it unhides that collection. Switching or adding targets only adds new items, so un-solo always returns to the state from before the first solo.
- **Ending solo:** `unsolo()` writes back every item whose pointer still resolves, then clears the snapshot. Items for deleted lights are skipped.
- **Changes during solo:** mute and group hide call `update_snapshot()`, which writes the new flags into the snapshot, so they survive un-solo. A light muted during solo is marked `muted`, so changing the targets never brings it back.
- **The World** is an exclusive target. World solo hides every light and un-mutes the World's Background, with its own small snapshot (`world`, `world_node`, `world_muted`). Lamp and group solo leave the World alone and end a World solo first.
- **Exit Solo** sits in the Lights header at all times. It's greyed out by `poll()` when no solo is active, so the header never shifts. Its tooltip names the targets (`solo_label()`).
- **Old files:** files saved mid-solo by 1.3 kept their target in the `light`/`group` pointers. The `load_post` handler `migrate_solo_targets` moves those into `targets`.

### Presets

- **On disk:** each preset is a JSON file in `extension_path_user(__package__)`. On the first run of a session, `presets_folder()` writes the defaults (Candle, 60W Bulb, Daylight) once and leaves a `.defaults_installed` marker, so a default the user deleted stays deleted. Restore Default Presets (in Preferences) writes back missing defaults only.
- **The cache:** `cached_user_presets()` re-reads the folder only when its mtime changes, and Save and Delete clear the cache. A file edited in place outside Blender doesn't change the folder's mtime, so the edit is seen only after a restart.
- **The dropdown:** it's a dynamic enum whose item numbers are a CRC of each preset's key, so the selection follows the preset rather than its position.
- **Applying:** `apply_preset()` always sets power, RGB color and radius. Where the light has them, it also sets `exposure` (4.4+) and the Kelvin temperature (5.0+). A Kelvin preset sets the color to white, because in 5.x `color` tints the blackbody color. On versions without temperature, the RGB fallback is used.

### Adding lights and collections

- **New Light:** `add_light` creates the light at the 3D cursor, in the active collection or in a given target (from a header's right-click menu). It applies `SHIFT_A_VALUES` so new lights match Shift+A, applies the Kelvin mode, and calls `reveal()` so the light isn't hidden inside a folded collection.
- **Color or Kelvin:** a file follows the default from Preferences until its header toggle is flipped. `toggled_mode()` stores a value only while it differs from that default.
- **What follows the mode:** only Lighthouse's own New Light. Shift+A, duplicates and appends are left alone, because a handler can't reliably tell a new light from a copied one.
- **New Collection** creates the collection inside the active collection, or the target, and makes it active.
- **Active collection:** clicking a collection name sets Blender's own `view_layer.active_layer_collection`, so it stays in step with the Outliner and Shift+A.

### World

`world_setup(scene)` classifies the active World Output:

- `SIMPLE`: a Background node whose Strength isn't driven by another node.
- `CUSTOM`: anything else, such as a Mix Shader, a node group or nodes turned off.
- `NONE`: the scene has no world.

The World panel draws Strength only for `SIMPLE` setups. Rotation is a Mapping node in front of the Environment Texture, added by Add Rotation. Mute mutes the Background node, so `CUSTOM` setups can't be muted (see [Rendering](#rendering)). Load HDRI sets the image on the world's only Environment Texture. On a Background-only simple world, it adds an Environment Texture first.

### Light linking

The details' Light Linking section edits only the light's receiver collection (`obj.light_linking.receiver_collection`), never shadow linking. `link_receivers()` creates the collection when needed and sets each item's `link_state` to Include or Exclude. `receivers()` lists child collections, then objects. When several lights share a receiver collection, the section says so, and an edit changes all of them. `light_linking_note(engine)` warns when the current engine doesn't render light linking (see [Rendering](#rendering)).

## Blender API quirks

### Extension and packaging
- `blender --command extension validate` needs `__init__.py`, not just the manifest.
- `extension_path_user()` raises `ValueError` unless the package is `bl_ext.<repo>.<id>`, so preset tests run through `run_installed()`.
- Blender leaves dotfiles and `__pycache__` out of the zip by default, so the manifest has no `paths_exclude_pattern`.
- No `files` permission is declared, because presets live in Blender's own per-extension folder.

### Properties and RNA
- A Python `PointerProperty` to an ID **adds a real user**. A solo snapshot keeps its lights' user counts raised until it's cleared. `bpy.ops.object.delete()` during solo therefore unlinks the light but doesn't free it, and un-solo restores flags on the orphan, which does no harm.
- `bpy.data.objects.remove()` sets every pointer to the removed ID to `None`.
- Python wrappers of the same ID compare and hash equal, so sets of objects work across `view_layer.objects` and `collection.objects`.
- `Light.energy` has no RNA unit, so the unit is a separate button. The row always shows `W`, because `W/m²` gets truncated at the default sidebar width. The tooltip gives the exact unit.
- Every light type has `shadow_soft_size` in RNA, so `hasattr` can't decide which details to show. The list is chosen by type.
- Cycles' Cast Shadow is `Light.use_shadow`, shared with EEVEE since 4.0.
- `has_property()` checks `bl_rna.properties`, not `path_resolve`, because a light proxy forwards `path_resolve` to the real RNA.
- Blender doesn't keep the strings a dynamic enum `items` callback returns alive, so the callbacks fill module-level lists. Dynamic enum items aren't listed in `bl_rna...enum_items`.
- A dynamic enum stores the item number. When that number has no item, the property reads `''`, and assigning `''` to an enum raises `TypeError`. The panel guards against it.
- `name_filter` uses `TEXTEDIT_UPDATE` so the list narrows on each keystroke. RNA doesn't expose that flag, so it can't be tested.
- An `IntProperty` operator argument rejects floats, which is why EV `steps` is a `FloatProperty`. A `FloatProperty` without `soft_max` can be dragged without a cap.
- `bpy.ops` calls from Python never reuse an operator's last properties, so `SKIP_SAVE` shows up headless only as `is_skip_save`.
- `Light.temperature` is clamped to 800–20000 K, and defaults to 6500 K.
- `bpy.data.lights.new()` and Shift+A start Sun and Area lights with different values (Sun 10 vs 1.0 W/m², Area size 0.25 vs 1.0 m), so `add_light` applies `SHIFT_A_VALUES`.
- Setting `hide_viewport` deselects an object right away, so a muted light is never selected. The right-click menu therefore never offers "Unmute N Lights".
- Files saved by an older add-on keep removed RNA properties as ID properties (`solo.get("light")`), which is what lets `migrate_solo_targets` read them.

### Collections, lookups and the view layer
- `view_layer.objects` syncs lazily. After removing and linking objects in one script, it can yield `None` until `view_layer.update()`. The UI resyncs before drawing.
- `Collection.objects` holds only directly linked objects (`all_objects` is recursive). Exclusion lives on the `LayerCollection`.
- `visible_get(view_layer=...)` covers the object's eye, its viewport flag and hidden or excluded collections, but not `hide_render`. That's why `row_state().dimmed` checks both.
- `bpy.data.objects.get((name, filepath))` returns the ID linked from that library, and `get((name, None))` the local one. `get((name, ""))` returns `None`, so the helpers map `""` to `None`.
- Linking an object into a library collection raises "Collection 'X' is linked", so operators check `is_read_only()` on the target first.
- `Collection.objects.unlink()` works on the scene's master collection.

### UI and drawing
- `UILayout.label()` has no tooltip. Indicators that need one (ⓘ, the unit, the linking icon) are flat `INTERNAL` operators whose `description()` classmethod builds the text from the button's properties.
- `invoke_props_dialog` draws every operator property unless the operator defines `draw()`.
- A `prop()` button on ID data pushes an undo step. Collapse and fold are operators without `UNDO` so they push none.
- `draw_header()` runs while a panel is collapsed. The Presets header no longer uses it, so presets can't be applied from a collapsed panel; that was chosen for a cleaner header.
- `bl_order` sets the default panel order: Active Light, World, Intensity, Presets, Lights. Whether it overrides an order saved in an older file isn't settled (see [Known limits](#known-limits)).
- In the right-click menu, `context.button_operator` identifies the clicked button by `bl_rna.identifier`, which is how `draw_group_menu()` and `draw_light_menu()` add entries only to Lighthouse rows. Submenus get their target through `layout.context_pointer_set()`.
- Link Selected can't use collections selected in the Outliner: `selected_ids` needs an Outliner area, and the sidebar has none.
- The panel can't be scrolled from Python, so Reveal Active Light only unfolds.

### Versions
- Blender 4.2 lacks `Light.exposure` (4.4+), `use_temperature` and `temperature` (5.0+), and the action-slot API (`action_get_channelbag_for_slot`, 4.4+). Each is guarded, and keyframe scaling falls back to `action.fcurves`.
- The EEVEE engine id is `BLENDER_EEVEE_NEXT` on 4.2 and `BLENDER_EEVEE` on 5.x. The code only compares against `'CYCLES'`.
- In `--background`, the engine enum lists only some built-ins, so `engine_name()` uses `ENGINE_NAMES` for built-ins and `RenderEngine.bl_label` for third-party engines.

### Rendering

Checked by rendering tiny images in Cycles and EEVEE on 4.2.23 and 5.2.2 (2026-10-10). Both probes are kept as tests.

- **World mute:** a muted Background or node group renders black, but a muted Mix Shader passes its first shader through at full brightness. So Mute acts only on the Background of a `SIMPLE` world.
- **Light linking** (16×16 px, the Cube excluded from the light, max RGB lit → excluded):

  | Blender | Cycles | EEVEE | Workbench |
  |---|---|---|---|
  | 4.2.23 | renders (0.83 → 0.01) | not rendered (0.84 → 0.84) | not rendered |
  | 5.2.2 | renders (1.0 → 0.02) | renders (1.0 → 0.004) | not rendered |

  Versions in between weren't checked, so `EEVEE_LIGHT_LINKING = (5, 0)`.
- In 5.x, `Light.color` tints a Kelvin light's blackbody color. That's why Kelvin presets and Kelvin new lights set the color to white.

### Testing headless
- Panels can't draw and `bpy.ops.ed.undo()` fails its poll in `--background`. The draw tests use a fake layout (`Recorder`), and undo is checked by hand ([tests/acceptance.md](../tests/acceptance.md)).
- An operator's `ERROR` report is raised to the caller as `RuntimeError`. `INFO` and `WARNING` reports are only printed (`Info: …`, `Warning: …`).
- Tests run with `--factory-startup`, which skips `userpref.blend`. A test that needs saved preferences calls `bpy.ops.wm.read_userpref()`, which crashes 4.2 headless, so that test is skipped there.
- The Fedora Blender 5.2.2 package logs an OpenColorIO config error on launch and, with `BLENDER_USER_RESOURCES` set, a `bl_pkg` traceback (`No module named 'cattrs'`). Both come from the environment, not the extension. That package can't load extensions at all, so installed-copy checks need another build.

## Testing

- `make test` runs pytest, and each test drives headless Blender (`BLENDER=` picks the binary). Helpers in `tests/blender_runner.py`:
  - `run_in_blender()` runs a snippet with the repo on `sys.path` and returns the JSON it reports.
  - `run_installed()` symlinks the package into a throwaway user folder and enables it as `bl_ext.user_default.lighthouse`. Calls that share the folder behave like restarts of one install.
  - `reports()` reads operator reports from the output, and `needs_blender()` skips a test on versions that are too old.
  - `RECORDER` and `drawn()` record what a `draw()` would lay out.
- `tests/fixtures/` holds .blend files saved by 1.3 on Blender 4.2, for the solo migration.
- `tests/smoke_engines.py` runs every operator on every light type under Cycles and EEVEE against an installed copy. `tests/acceptance.md` maps the acceptance criteria to tests and lists the checks that need the GUI.
- `make bench` times `LIGHTHOUSE_PT_lights.draw()` with 500 lights in 65 collections, on the `Recorder` layout. That measures Lighthouse's own Python, not Blender's widget layout. There's no threshold; compare the number by hand before a release.

### Release checks

- **1.4.0** (2026-10-19): `make validate` passes on 5.2.2 and 4.2.23. `dist/lighthouse-1.4.0.zip` installs into a fresh `BLENDER_USER_RESOURCES` profile, and `tests/smoke_engines.py` exits 0 there on both versions under Cycles and EEVEE. Bench: 15.7 ms on 5.2.2 and 14.7 ms on 4.2.23 (median of 9, AMD Ryzen 9 9900X).
- **1.3.0**: `make test` passes on 5.2.2 (266 pass, 1 skip) and 4.2.23 (254 pass, 13 skip). `make validate` passes on both. On 4.2.23, `make install` and the engine smoke pass.

## Known limits

- **Panel order:** it's not settled whether `bl_order` overrides the panel order saved in a 1.3.x file with dragged panels. Python can't read a region's panel order, so this needs the manual GUI check.
- **Light linking:** only receivers are edited, with no shadow linking. Link Selected ignores collections selected in the Outliner. EEVEE before 5.0 and Workbench don't render light linking, and versions between 4.2 and 5.2 weren't probed.
- **World:** Mute works only on simple worlds.
- **Presets:**
  - A preset file edited in place outside Blender is picked up only after a restart.
  - A .blend saved by an older version with a built-in preset selected opens with no preset selected, because the defaults' keys changed when they became files. There is no migration.
  - A preset saved from a tinted Kelvin light loses the tint.
- **Selection:** "Unmute N Lights" never appears, because a muted light is never selected.
- **Performance:** the Lights panel's draw is over the ~10 ms mark at 500 lights. Caching is a candidate for a later release.
