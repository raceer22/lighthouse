# Lighthouse architecture

## Task 01: installable extension with a Lights tab

**Components**
- `lighthouse/blender_manifest.toml`: extension manifest (id `lighthouse`, GPL-3.0-or-later, Blender ≥ 4.2, no dependencies).
- `lighthouse/lights.py`: `light_objects(view_layer)` returns every `LIGHT` object in a view layer. It is the single source of "which lights are listed", so later filters and sorting land here.
- `lighthouse/__init__.py`: `LIGHTHOUSE_PT_lights`, a `VIEW_3D` / `UI` panel in the "Lights" category, plus `register()` / `unregister()` over a `classes` tuple.
- `Makefile`: `test`, `validate`, `build` (zip into `dist/`), `install` (install-file into `user_default` and enable).
- `tests/`: pytest drives headless Blender. `blender_runner.run_in_blender()` runs a snippet with the repo on `sys.path` and returns JSON printed after a marker line.

**Data flow**
On each redraw, the panel's `draw()` calls `light_objects(context.view_layer)` and emits one label per object. Nothing is cached, so adding or deleting lights shows up on the next redraw.

**Blender API quirks**
- `view_layer.objects` is synced lazily. After `bpy.data.objects.remove()` and linking new objects in one script, iterating it can yield `None` until `view_layer.update()` runs. The UI resyncs before drawing; headless scripts must call `update()` themselves.
- An installed extension's module name is `bl_ext.<repo>.lighthouse` (for example `bl_ext.user_default.lighthouse`), so code inside the package must use relative imports.
- `--command extension validate` requires `__init__.py` to exist, not just the manifest.
- Fedora's Blender 5.2.2 package logs an OpenColorIO config-version error on every launch. It is an environment issue, unrelated to the extension.

## Task 02: row controls

**Components**
- `lighthouse/lights.py`: `power_unit(light)` returns `"W/m²"` for sun lights and `"W"` for the rest.
- `lighthouse/__init__.py`: `LIGHTHOUSE_OT_select_light` (`lighthouse.select_light`, `name` property) deselects everything in the view layer, selects the named object and makes it active. It is registered with `UNDO`.
- The panel row shows an unembossed operator button (`LIGHT_<TYPE>` icon plus the object name), `energy` as a slider, a unit label and the `color` swatch.

**Data flow**
The slider and swatch are `layout.prop()` on `obj.data`, so they edit the same RNA properties as the Properties editor's Light tab, and Blender's undo system records them. Neither control has its own state or handlers.

**Blender API quirks**
- `Light.energy` has no RNA unit or subtype (checked in 5.2), so a `prop()` slider shows a bare number. That is why the unit is a separate label.

## Task 03: search, type filter, sort

**Components**
- `lighthouse/lights.py`: `listed_lights(view_layer, name_filter="", type_filter='ALL')` returns the lights the panel shows. It keeps lights whose type matches (`'ALL'` matches every type) and whose name contains the search, ignoring case, then sorts them by name ignoring case. `light_objects()` stays unfiltered, so code that must ignore the list filters (such as task-06's bulk actions) keeps using it.
- `lighthouse/__init__.py`: `LIGHTHOUSE_PG_filters` (`name_filter`, `type_filter`) is attached to `bpy.types.WindowManager.lighthouse` in `register()` and removed in `unregister()`. The panel draws a search field and a row of type buttons above the list.

**Data flow**
`draw()` reads `context.window_manager.lighthouse` and passes both filters to `listed_lights()`. As before, nothing is cached.

**Blender API quirks**
- Filters live on the WindowManager, not the Scene. Python properties on the WindowManager are not saved in the .blend file and are not part of undo, so typing a search adds no undo steps and doesn't mark the file as changed.
- `name_filter` uses `options={'TEXTEDIT_UPDATE'}` so the list narrows on each keystroke instead of only when you press Enter. RNA doesn't expose that flag (no `is_*` attribute in 5.2), so tests can't check it; check it by hand in the UI.

## Task 04: hidden, library and shared-data rows

**Components**
- `lighthouse/lights.py`: `row_state(obj, view_layer)` returns a `RowState(dimmed, read_only, shared)`. `dimmed` is set when the object is hidden in the viewport, in renders or in the view layer (`hide_get()`). `read_only` is set when the light data has a `library` or a system (non-editble) ovearride. `shared` is set when `light.users > 1`.
- `lighthouse/__init__.py`: the panel sets `row.active = not dimmed`. It puts the slider, unit and swatch in a sub-row with `enabled = not read_only`, so a library light can still be selected by name. Shared rows get a flat `LINKED` button, `LIGHTHOUSE_OT_shared_light_info`, a no-op `INTERNAL` operator whose docstring is the tooltip.

**Data flow**
`draw()` calls `row_state()` for each listed light. Hidden lights were always listed, because `view_layer.objects` includes hidden objects, and `tests/test_row_states.py` keeps it that way. Shared rows `prop()` the same datablock, so editing one row changes every row that uses it.

**Blender API quirks**
- `UILayout.label()` has no tooltip, which is why the shared indicator is an operator button.
- `override_hierarchy_create()` overrides the light object but leaves its light data linked (`library` set), so the library check covers it. Only data overridden on its own (`light.override_create()`) reaches the `is_system_override` branch.
- `make validate` warns about the OCIO 2.5 config on Fedora's Blender 5.2.2 package. As with the launch error noted under task 01, this comes from the environment, not the extension.

## Task 05: mute and solo

**Components**
- `lighthouse/lights.py`: `toggle_solo(scene, view_layer, obj)` handles solo, switch and un-solo. `soloed_light_name(scene)` reads the soloed light. `row_state()` takes an optional `scene` and adds `muted` (hidden in both viewport and render) and `soloed`.
- `lighthouse/__init__.py`: `LIGHTHOUSE_OT_mute_light` and `LIGHTHOUSE_OT_solo_light` (both `UNDO`, `name` property). Each row ends with an eye button and a solo button, drawn with `depress=` for the active state.

**Data flow**
The first solo writes a JSON snapshot `{"light": name, "flags": {name: [hide_render, hide_viewport]}}` to `scene["lighthouse_solo"]` and hides every other light in both. Soloing a different light only changes `"light"` and adds lights that are missing from the snapshot (ones created during solo), so un-solo always goes back to the state from before the first solo. Pressing solo on the soloed light restores the snapshot, skipping lights that no longer exist, and deletes the property. The snapshot is scene data, so it is saved in the .blend file and recorded by undo.

**Known limits**
- The snapshot is keyed by object name. A light renamed during solo is not restored.
- ~~If the soloed light is deleted, no row shows as soloed. Solo any light, then press it again to restore.~~ Fixed in v3 task 05: the Exit Solo row.
- ~~Mute during solo changes the flags, but un-solo overwrites them with the snapshot.~~ Fixed in v3 task 05: mute writes to the snapshot.

**Blender API quirks**
- `bpy.ops.ed.undo()` fails its poll in `--background`, so tests can't check undo. Check it by hand.
- Python string snippets passed to `run_in_blender` are dedented as a whole, so shared snippet fragments must carry the same 8-space indent as the test body.

## Task 06: intensity scale

**Components**
- `lighthouse/lights.py`: `scale_lights(lights, factor)` multiplies `energy` once per light datablock, so data shared by several objects is scaled once. It skips read-only lights. `is_read_only(light)` is the library / system-override check, moved out of `row_state()` so both use it.
- `lighthouse/__init__.py`: `LIGHTHOUSE_OT_scale_lights` (`lighthouse.scale_lights`, `UNDO`) takes `factor` and `scope` (`ALL` / `SELECTED`, from `SCOPE_ITEMS`). Its scope starts from the unfiltered `light_objects()`, so the list filters never narrow it. The property group is renamed `LIGHTHOUSE_PG_settings` and gains `scale_factor` (default 1.0) and `scale_scope`. The panel draws an "Intensity" box above the search field, with the scope toggle, the factor slider and an Apply button that copies both settings into the operator.

**Data flow**
Apply runs one operator call that scales every light in scope, so Blender records a single undo step and one Ctrl+Z restores all values. Task 07's EV buttons can call the same operator with `factor=2` or `0.5` and the chosen scope. The factor and scope live on the WindowManager like the filters, so they are not saved or undone.

**Blender API quirks**
- As in task 05, undo can't be tested in `--background`. Check by hand that one Ctrl+Z after Apply restores every light.

## Task 07: EV buttons

**Components**
- `lighthouse/__init__.py`: `LIGHTHOUSE_OT_step_exposure` (`lighthouse.step_exposure`, `UNDO`) takes `steps` (an integer, +1 or -1 from the buttons) and `scope` (`SCOPE_ITEMS`). It picks the scoped lights the same way `scale_lights` does and calls `scale_lights()` with factor `2 ** steps`, so it inherits the shared-datablock and read-only rules. The Intensity box gains a row of "-1 EV" and "+1 EV" buttons below Apply, each passing the chosen scope.

**Data flow**
One button press is one operator call, so it makes one undo step. Power is in W, or W/m² for sun, and the same factor applies to every light type.

**Blender API quirks**
- As in tasks 05 and 06, undo can't be tested in `--background`. Check by hand that one Ctrl+Z after an EV button restores every light.

## Task 10: user presets

> Superseded in part by v4 task 10: there are no built-ins any more, every preset is a file, and the `USER` icon and reserved names are gone.

**Components**
- `lighthouse/presets.py`: `preset_from_light(light, label)` reads power, color and soft size back as a radius (area `size / 2`, sun `angle`, otherwise `shadow_soft_size`). A sun gives a sun-only preset, and any other type gives a point/spot/area preset. `save_user_preset()` writes `<label>.json` (characters outside `\w`, `-` and space become `_`). `user_presets(folder)` reads every `*.json`, keyed `USER:<file stem>` and sorted by label, and prints `Lighthouse: Skipped user preset <file>: …` for files that aren't valid JSON or are missing fields. `delete_user_preset()` removes the file.
- `lighthouse/__init__.py`: `presets_folder()` is `bpy.utils.extension_path_user(__package__, create=True)`. The `preset` enums on the settings and on `apply_preset` are dynamic (`preset_items`): built-ins first, then user presets with the `USER` icon. `LIGHTHOUSE_OT_save_preset` (poll: active object is a light, invoke opens a name dialog) refuses empty names and built-in labels in any case. Saving an existing user name overwrites it. `LIGHTHOUSE_OT_delete_preset` (confirm on invoke) only lists user presets, so a built-in can't be passed. The Presets row gains `+`, plus `-` when a user preset is chosen.
- `tests/blender_runner.py`: `run_installed(snippet, user_dir)` symlinks the package into `user_dir/extensions/user_default/`, sets `BLENDER_USER_RESOURCES=user_dir` and enables `bl_ext.user_default.lighthouse`. Calls that share `user_dir` act like restarts of one install. `preset_items()` in its prelude calls the dropdown's items callback.

**Data flow**
User presets were read from disk every time the dropdown or `apply_preset` needed them. Since v3 task 02 they are cached (see below). They live outside the .blend file and aren't part of undo.

**Blender API quirks**
- `extension_path_user()` raises `ValueError` unless the package name is `bl_ext.<repo>.<id>`. That's why every preset test (task 09's too) runs through `run_installed` instead of `import lighthouse`.
- Blender doesn't keep the strings returned by a dynamic enum `items` callback alive, so the callbacks fill module-level lists.
- Dynamic enum items are not exposed through `bl_rna...enum_items` (it returns `[]`).
- A preset enum is stored as its item number. Since v3 task 02 the number is a CRC of the key, so the dropdown keeps its preset when others are added or deleted.
- With `BLENDER_USER_RESOURCES` set, enabling an extension logs a `bl_pkg` register traceback (`No module named 'cattrs'`) on Fedora's package. It's environment noise.

## Task 11: detail section

**Components**
- `lighthouse/lights.py`: `detail_properties(light, engine)` returns the RNA paths, relative to the light data, that a row's detail section shows: the soft size (`shadow_soft_size` for point and spot, `angle` for sun, none for area because its size is a shape parameter), then `specular_factor`, `diffuse_factor`, `volume_factor` and `use_shadow`. When `engine == 'CYCLES'` it adds `cycles.max_bounces`, `cycles.use_multiple_importance_sampling`, `cycles.is_caustics_light`, plus `cycles.is_portal` for area lights. Any path the light can't resolve is dropped. `detail_target(light, path)` splits a path into the `(owner, property)` pair that `prop()` needs.
- `lighthouse/__init__.py`: `Object.lighthouse_expanded` (a BoolProperty registered in `register()`) is drawn as a disclosure triangle at the start of each row. An expanded row gets a box below it with one `prop()` per detail path. The box follows the row's dimmed and read-only state.

**Data flow**
`draw()` passes `context.scene.render.engine` to `detail_properties()` on every redraw, so switching engines changes the detail section right away. The details are `prop()` calls on the light data or on `light.cycles`, so they edit the same properties as the Properties editor's Light tab. Collapsed rows draw nothing extra.

**Blender API quirks**
- Every light type has `shadow_soft_size` in RNA, sun and area included, so `hasattr` can't decide what to show. The list depends on the light type, and resolving each path is only a safety net.
- Cycles' "Cast Shadow" is `Light.use_shadow` (it moved off `light.cycles` in 4.0), so EEVEE and Cycles share one shadow toggle.
- The expanded state is object data. It is saved in the .blend file, survives renames, and toggling it adds an undo step.
- The panel layout can't be drawn in `--background`. Check by hand that expanding each type shows its details without console errors, and that switching the engine updates them.

## Task 12: packaging and acceptance pass

**Components**
- `lighthouse/LICENSE`: the full GPLv3 text, shipped inside the zip.
- `build.sh`: validates the manifest, then builds `lighthouse-<version>.zip` into its argument (default `dist`). `make build` calls it. `BLENDER` overrides the binary.
- `README.md`: what the extension is, how to build and install it, and why it declares no `permissions`.
- `tests/acceptance.md`: AC 1–14 mapped to the tests that prove them, plus a GUI checklist for what can't run headless (panel drawing, undo).
- `tests/smoke_engines.py`: a script, not a pytest test. It runs every operator on every light type under Cycles and then EEVEE against an installed copy.
- `tests/test_packaging.py`: also checks that the zip ships the license and that `build.sh` produces the versioned zip.

**Data flow**
`build.sh` → `extension validate` → `extension build --source-dir lighthouse`. Only `lighthouse/` is packaged, so the repo's tests, tasks and docs never reach the zip. Blender leaves out dotfiles and `__pycache__` by default, so the manifest has no `paths_exclude_pattern`.

**Blender API quirks**
- No `files` permission: presets live in `extension_path_user()`, Blender's own per-extension folder, and the permission is meant for access outside Blender.
- `RenderSettings.engine`'s `enum_items` lists only `BLENDER_EEVEE` in `--background` scripts, but setting `'CYCLES'` still works.

## v2 task 01: three panels and finer intensity steps

**Components**
- `lighthouse/__init__.py`: the single `LIGHTHOUSE_PT_lights` panel is split into three top-level panels in the Lights tab, registered in this order: `LIGHTHOUSE_PT_intensity`, `LIGHTHOUSE_PT_presets`, `LIGHTHOUSE_PT_lights`. `LIGHTHOUSE_PT_lights` keeps its idname and holds the search, type filter and list.
- `LIGHTHOUSE_PT_presets.draw_header()` draws the preset dropdown and Apply. The body holds Save and, for user presets only, Delete.
- `LIGHTHOUSE_PT_intensity` draws the scope, the factor as a plain number field with Apply, and an EV row built from `EV_STEPS` (−1, −½, −¼, +¼, +½, +1).
- `LIGHTHOUSE_OT_step_exposure.steps` is a `FloatProperty`. The factor property has no `soft_max`.

**Data flow**
All three panels read `WindowManager.lighthouse`. EV buttons pass their float `steps` to `step_exposure`, which calls `scale_lights(lights, 2 ** steps)`, so fractional steps scale power keyframes exactly like the factor does. Neither path touches `Light.exposure`.

**Blender API quirks**
- Panel order is set by `bl_order` since v6 task 04 (Active Light, World, Intensity, Presets, Lights). Before that, with no `bl_order`, registration order was the default panel order. Blender stores each panel's open/closed flag and drag position in the screen layout, so both are saved with the .blend file without any addon code.
- `draw_header()` runs even while the panel is collapsed, which is what lets presets be applied from a collapsed Presets panel. Drawing still can't run in `--background`, so the header and layout are checked by hand.
- Passing a float to an `IntProperty` operator argument raises `TypeError` ("expected an int type, not float"). A `FloatProperty` accepts ints, so old `steps=1` callers keep working.
- A `FloatProperty` with no `soft_max` gets `soft_max == hard_max` (FLT_MAX when no `max` is set), so dragging the field isn't capped. Dropping `slider=True` removes the slider bar.

## v2 task 02: lights grouped by collection

**Components**
- `lighthouse/lights.py`: `list_entries(view_layer, name_filter, type_filter, grouped)` returns the rows the Lights panel draws, in order. They are `GroupEntry(collection, depth, count)` and `LightEntry(obj, depth, other_collections)` NamedTuples. In grouped mode, `_collection_entries()` walks `view_layer.layer_collection` recursively. It skips `exclude`d layer collections and keeps a collection only if its subtree holds a listed light. Each group lists its sub-collections in outliner order, then its own lights sorted by name ignoring case. Scene Collection lights come last at depth 0 with no header (changed later: see Post-v2 polish). `count` is the size of the set of listed lights in the subtree, so a light in two sub-collections counts once. `other_collections` is how many other entries the same object got. In flat mode (`grouped` off or a non-empty search) the result is `listed_lights()` at depth 0.
- `indent_level(depth)` caps indentation at `MAX_INDENT` (3). `light_info_tooltip(other_users, other_collections)` builds the info icon's text, or `""` when neither case applies.
- `lighthouse/__init__.py`: `LIGHTHOUSE_PG_settings.grouped` (BoolProperty, default True) is drawn as an `OUTLINER` icon toggle next to the search field. `LIGHTHOUSE_PT_lights.draw()` iterates `list_entries()` and calls `draw_group()` (indent, collection icon, `Name (N)`) or `draw_light()` (the v1 row plus indent). `indent()` adds `row.separator(factor=INDENT_STEP * indent_level(depth))`.
- `LIGHTHOUSE_OT_light_info` (`INTERNAL`, no-op, `INFO` icon) replaces `LIGHTHOUSE_OT_shared_light_info` / `LINKED`. Its `other_users` and `other_collections` properties are set on each button, and `description()` turns them into the tooltip through `light_info_tooltip()`.

**Data flow**
`draw()` → `list_entries()` → `listed_lights(view_layer, type_filter=...)` gives the set of listed lights. The collection walk keeps only objects in that set, so grouped and flat modes agree on which lights are listed, and the type filter drops empty groups and changes counts. Every entry for an object holds the same `Object`, so all of its rows edit the same light. `grouped` lives on the WindowManager, so it is not saved and not part of undo.

**Blender API quirks**
- Python wrappers of the same ID compare and hash equal even when fetched separately, so `set`/`Counter` of objects and `obj in listed` work across `view_layer.objects` and `collection.objects`.
- `Collection.objects` holds only directly linked objects (`all_objects` is recursive), which is what a per-level walk needs. Exclusion lives on the `LayerCollection`, not the `Collection`.
- An operator's `description(cls, context, properties)` classmethod gets the properties set on that button, so a single no-op operator can show a different tooltip on each row.
- The test prelude's `empty_scene()` removes objects but keeps the factory `Collection`, an empty collection that `list_entries()` must drop.
- `row.separator(factor=...)` in an aligned row gives a horizontal gap. Its exact width can only be checked in the GUI.

## v2 task 03: group header actions

**Components**
- `lighthouse/lights.py`: `_collection_entries()` now returns its lights as a dict used as an ordered set (list order) instead of a `set`. A child whose collection `is_collapsed()` still gets its `GroupEntry` with the full count, but its child entries are dropped. `is_collapsed()` reads `lighthouse_collapsed` with a `False` default so `list_entries()` still works when the add-on isn't registered (the v2 task 02 tests call it that way).
- `group_lights(view_layer, collection, type_filter)` finds the collection's (non-excluded) layer collection with `_find_layer_collection()` and returns the same lights its header counts, in list order, ignoring collapse.
- `move_lights(objects, collection)` links each object into the target and unlinks it from every other `users_collection` entry, the Scene Collection included. It skips `is_read_only()` objects and returns `(moved, skipped)`. `move_summary()` builds the Info report. `is_read_only()` now takes any ID (light data, object or collection).
- `row_state().dimmed` is `obj.hide_render or not obj.visible_get(view_layer=...)`. `visible_get` covers the object's viewport flag, its eye toggle and hidden or excluded collections. `hide_render` stays because `visible_get` ignores it. `muted` still only reads the object's own flags.
- `lighthouse/__init__.py`: `Collection.lighthouse_collapsed` (BoolProperty, removed in `unregister()`). Operators, all taking a collection `name`:
  - `toggle_group` and `toggle_all_groups` (formerly `collapse_all_groups`) have `bl_options = {'INTERNAL'}`, with no `UNDO`. See v3 task 04 for toggle all.
  - `select_group` (`UNDO`): `invoke()` copies `event.shift` into `extend`. When it replaces the selection, it deselects everything and makes `lights[0]` active unless the active object is already one of the group's lights.
  - `move_to_group` (`UNDO`) refuses a read-only target with an `ERROR` report before touching anything.
  - `hide_group` (`UNDO`) toggles the collection's `hide_render` and `hide_viewport` together, like mute.
- `LIGHTHOUSE_PT_lights.draw_group()` draws: disclosure triangle (`toggle_group`, no emboss), `Name (N)` label, then an aligned sub-row with Select, Move selected here, Hide (`depress=` when both flags are on). Task 04's Solo goes at the end of that sub-row. The Collapse All button sits next to the group toggle, only while grouped and not searching.

**Data flow**
`draw()` → `list_entries()` honours `lighthouse_collapsed` on each `Collection`. Header buttons pass `collection.name` to their operators, which look the collection up in `bpy.data.collections`. `select_group` reads the panel's type filter from `context.window_manager.lighthouse` and calls `group_lights()`, so it selects exactly the lights the header counts. `move_to_group` acts on every selected light object in the view layer, whatever the filters show. Hiding a group changes only collection flags. The rows of its lights then become dimmed through `visible_get()`, and their muted state and solo snapshot are untouched.

**Blender API quirks**
- A `bpy.props` property registered on an ID type (`Collection`) is stored in that ID's properties, so it is saved in the .blend with no extra work. Setting it from an operator without `UNDO` pushes no undo step. A `prop()` button on ID data would push one, which is why the triangle is an operator.
- `visible_get(view_layer=...)` reflects a collection's `hide_viewport` right after the change. No `view_layer.update()` is needed in tests.
- In background mode an operator's `{'ERROR'}` report is raised to the caller as `RuntimeError`, so tests catch it. `{'INFO'}` reports only go to stdout (`info_reports()`).
- Linking a local object into a library collection raises "Collection 'X' is linked", which is why `move_to_group` checks the target first.
- `Collection.objects.unlink()` works on a scene's master collection (`scene.collection`), so the Scene Collection is unlinked from like any other.

## v2 task 04: pointer-based solo

**Components**
- `lighthouse/__init__.py`: `Scene.lighthouse_solo`, a `PointerProperty` to `LIGHTHOUSE_PG_solo` (`active`, `light` Object pointer, `group` Collection pointer (replaced by `targets` in v6 task 08), and `objects` / `collections` CollectionProperties of `LIGHTHOUSE_PG_solo_object` / `LIGHTHOUSE_PG_solo_collection`, each a pointer plus `hide_render` / `hide_viewport`). It replaces the v1 JSON in `scene["lighthouse_solo"]` and `SOLO_KEY`. An old JSON value is left in place and ignored. The new `LIGHTHOUSE_OT_solo_group` (`UNDO`, collection `name`) is drawn at the end of the group header's action sub-row, after Hide.
- `lighthouse/lights.py`: `toggle_solo_light(solo, view_layer, obj)` and `toggle_solo_group(solo, view_layer, collection)` take the property group, not the scene. Both call `_solo(solo, view_layer, shown, collections)` or, when their target is already soloed, `_unsolo(solo)` (public `unsolo` since v3 task 05). `_collection_paths(view_layer, wanted)` walks the non-excluded layer collection tree and returns each accepted collection with its ancestors. `group_soloed(scene, collection)` and `row_state().soloed` compare pointers for the header and row `depress=`.

**Data flow**
A light solo unhides the collections in `obj.users_collection` plus their ancestors. A group solo shows `collection.all_objects` and unhides the group, its `children_recursive` and its ancestors. `_solo` clears the snapshot only when `active` is off. It then adds every light, and every collection it is about to unhide, that has no snapshot item yet, records the flags, unhides the collections and sets every light's flags to "shown only if in `shown`". Switching target never removes items, so un-solo goes back to the state before the first solo, and collections unhidden for an earlier target stay unhidden until then. `_unsolo` writes back every item whose pointer is still set, then clears both lists, both target pointers and `active`. Renames don't matter, because nothing is looked up by name after the operator resolves its target.

Since v5 task 08 the World is a third solo target, with its own snapshot (see that entry). Lamp and group solo never touch the World.

**Blender API quirks**
- A Python `PointerProperty` to an ID **adds a real user**. Soloing A in a two-light scene takes A from 1 user to 3 (collection + `light` + snapshot item) and B from 1 to 2. Clearing the snapshot drops them again.
- `bpy.data.objects.remove()` / `bpy.data.collections.remove()` set every pointer to the removed ID to `None`, so un-solo skips them.
- `bpy.ops.object.delete()` (viewport Delete) during solo unlinks the light from the scene but **does not** free it, because the snapshot's user keeps it in `bpy.data` and its pointer stays set. Un-solo restores the flags on that orphan, which does no harm, and clearing the snapshot leaves it with 0 users, so it is purged on save. The outliner's Delete can't be run headless, so whether it sets the pointer to `None` or orphans the light like `object.delete` is unverified. Either way un-solo works.
- `object.delete` acts on `selected_objects`, and solo hides the other lights in the viewport, so they can't be selected by `select_set()`. Probes have to pass `temp_override(selected_objects=[...])`.
- Comparing ID pointers with `==` and putting them in sets works, because wrappers for the same ID compare and hash equal.
- Factory startup has a default "Collection", so tests that compare every collection remove it first.

## v2 task 05: light rows

**Components**
- `lighthouse/__init__.py`: `LIGHTHOUSE_OT_select_light` gains an `action` enum (`SELECT`, `TOGGLE`, `RENAME`, `FRAME`) and a `new_name` string. It also has `RANGE`. `invoke()` maps the click's modifiers to `action` (Shift → `RANGE`, Ctrl+Shift → `TOGGLE`, Ctrl → `RENAME`, Alt → `FRAME`, none → `SELECT`). For `RENAME` it pre-fills `new_name` and opens `invoke_props_dialog`, whose `draw()` shows only the name field. `execute()` does the work, so tests pass `action` directly. The module-level `frame_selected(context)` runs `view3d.view_selected` under `temp_override` in the panel's own 3D view (else the first one on screen) and does nothing when there is none, as in `--background`.
- `LIGHTHOUSE_OT_add_light` (`UNDO`, `type` from the new `LIGHT_TYPES`, which `type_filter` now reuses after its `ALL` item) is offered by `operator_menu_enum` as the `+` at the end of the list header. `LIGHTHOUSE_OT_power_unit` (`INTERNAL`, no-op) is the row's unit: it always shows `W`, and its `description()` gives the exact unit from `power_unit()` (`Power in watts per square metre (W/m²)` for Sun).
- `draw_light` row order: disclosure, type dropdown (`prop(light, "type", icon_only=True)` in a sub-row disabled when `read_only`), name button (no icon now that the dropdown shows the type), info, power, unit (`UNIT_WIDTH = 1.5`), swatch (`SWATCH_WIDTH = 2`), mute, solo.
- Highlight: unselected names are flat (`emboss=False`), selected ones are an embossed grey button, and the active light's is embossed with `depress=True`, which fills it with the theme's selection blue. All three are easy to tell apart in the default theme.

**Data flow**
The name button passes only `name`. `invoke()` picks `action` from the event, so redo and Python calls use the stored `action`. `RANGE` rebuilds the panel's rows with `list_entries` and the current filters, deselects every object and selects the lights between the active light (the anchor, which stays active) and the clicked one, in either direction. Lights in collapsed groups or filtered out are skipped because they aren't listed. If the active object isn't a listed light, it acts as `SELECT`. `TOGGLE` on a selected light only deselects it and leaves the active object alone. `RENAME` strips the name, rejects an empty one with an `{'ERROR'}` report and sets `obj.name`, so Blender adds `.001` on a clash. `add_light` names the object and data after the type's label, sets `location` from `scene.cursor.location`, links into `view_layer.active_layer_collection.collection` (refused when `is_read_only`), then deselects every object and selects and activates the new one. The type dropdown writes `light.type` on the data block, so every object sharing it changes (AC 16), as in the Properties editor.

**Blender API quirks**
- At the default N-panel width a 1.5-unit label truncates `W/m²` to `W...`, and widening the column to 2.2 squeezes the power value out of view, because the name button and the power field split what the fixed-width items leave. Hence the uniform `W` and the tooltip.
- A `label()` can't have a tooltip, so the unit is a flat `INTERNAL` operator whose `description()` classmethod builds the text from its properties (the same trick as `light_info`).
- `invoke_props_dialog` draws every operator property unless the operator defines `draw()`.
- Which modifier clicks Blender passes through to an operator button (Ctrl and Alt on buttons can be taken by the UI) is still to be confirmed in the manual GUI check.

## v2 task 06: details accordion

**Components**
- `lighthouse/__init__.py`: `LIGHTHOUSE_PG_expanded` (one `obj` Object pointer) and `LIGHTHOUSE_PG_settings.expanded`, a collection of them on the WindowManager. It replaces `Object.lighthouse_expanded`, which is no longer registered.
- `LIGHTHOUSE_OT_toggle_details` (`INTERNAL`, no `UNDO`) takes the object `name` and `keep_others`. `invoke()` sets `keep_others` from Shift. The row's disclosure triangle draws it, with the icon from `details_open()`.
- `lighthouse/lights.py`: `details_open(settings, obj)` and `toggle_details(settings, obj, keep_others)` hold the accordion logic. `has_property(rna, name)` checks `rna.bl_rna.properties` for properties newer than Blender 4.2. `NEWER_DETAILS` (`exposure` 4.4+, `use_temperature` and `temperature` 5.0+) lead `detail_properties()` when the light has them.
- `draw_details` now takes the object: the box shows `Name` (`prop(obj, "name")`), then the `detail_properties()` paths.

**Data flow**
A triangle click runs `toggle_details`. It first drops entries whose `obj` is `None` (deleted lights). If the light is open it removes only its entry. Otherwise it clears the others (unless `keep_others`) and adds it. Each draw asks `details_open(settings, obj)`, so every row of a multi-linked object shows the same state. The state lives on the WindowManager, so it isn't saved in the .blend, and an operator without `UNDO` pushes no undo step. Entries point at the object, so renaming keeps them.

**Blender API quirks**
- WindowManager ID pointers survive undo: in a headless run, `ed.undo` after a toggle reverted the scene and `expanded[0].obj` still resolved to the same light, so no `session_uid` matching is needed. To be confirmed by Ctrl+Z in the GUI.
- `path_resolve` can't serve as the version check for the new properties, because a light proxy forwards it to the real RNA. `bl_rna.properties` membership is the lookup the task names, and it is what the 4.2 stub test fakes.

## v2 task 07: Kelvin, exposure and acceptance pass

**Components**
- `lighthouse/lights.py`: `color_control(light)` returns `"temperature"` when the light has `use_temperature` (checked with `has_property`) and it is on, and `"color"` otherwise. The row's fixed color slot draws `prop(light, color_control(light), text="")` at the same `SWATCH_WIDTH`.
- `lighthouse/presets.py`: `Preset` gains `exposure=0.0`, `use_temperature=False` and `temperature=6500.0`. The built-ins use Kelvin (Candle 1850 K, 60W Bulb 2700 K, Daylight 5500 K) and keep their RGB as the fallback. `presets.py` now imports `has_property` from `lights.py`.
- `tests/smoke_engines.py` puts the lights in a sub-collection and runs every v2 operator too (group operators, `toggle_details`, `add_light`, every `select_light` action, fractional EV), plus the color slot and details with temperature on and off.
- `tests/acceptance.md` is rewritten for PRD-v2 AC 1–21. The manifest is 1.1.0.

**Data flow**
- Save: `preset_from_light` copies `exposure`, `use_temperature` and `temperature` only where the light has them, so on older Blender the preset keeps the defaults. `save_user_preset` writes every field through `_asdict()`.
- Load: `user_presets` reads the three new keys with `data.get()`, so a pre-v2 file gives exposure 0 and temperature off.
- Apply: `apply_preset` always sets power, RGB color and radius. Where the light has them it sets `exposure`, then `use_temperature` and `temperature`. If the preset uses Kelvin and the light has temperature, the color is set to white after that. Without `use_temperature` (before 5.0), only the RGB fallback is applied.

**Blender API quirks**
- In 5.2, `Light.color` tints the blackbody color: a 3000 K Cycles render with `color` red came out pure red. A Kelvin preset therefore applies white, and its stored `color` is only the fallback for versions without temperature. A user preset saved from a tinted Kelvin light loses the tint, which was accepted as rare.
- `Light.temperature` is clamped to 800–20000 K, with 6500 K as the default.
- The stub for a pre-5.0 light has to hide the newer properties from `getattr`/`setattr` as well as from `bl_rna.properties`, or an unguarded write would reach the real 5.2 light and the test would pass anyway.
- ~~The smoke script must not interleave `hide_group` and `solo_group` toggles: un-solo restores the flags solo recorded, so a hide in between is undone.~~ Since v3 task 05 a hide during solo is written to the snapshot and kept.

## Post-v2 polish: list order and Presets header

**Components**
- `_collection_entries()` now emits a collection's own lights (sorted by name, ignoring case) before its sub-collections, so Scene Collection lights come first at depth 0.
- `LIGHTHOUSE_PT_presets` no longer has `draw_header()`. Its header is the plain `bl_label`, and `draw()` starts with the preset dropdown and Apply, followed by Save and Delete. This replaces the task 05 header layout and amends PRD-v2 AC 1.

**Data flow**
`group_lights()` and the Shift+click range both follow `list_entries()` order. Group select makes the group's first own light active (before lights in sub-collections), and a range runs over the new order.

**Blender API quirks**
- Without `draw_header()`, presets can't be applied while the panel is collapsed. That trade-off was chosen for a cleaner header.

## v3 task 01: own lights first

**Components**
- `_collection_entries()` builds a collection's own lights (sorted by name, ignoring case) first, then appends each child's `GroupEntry` and, unless it is collapsed, the child's entries. The `list_entries()` docstring says the same.

**Data flow**
`lights` stays an ordered dict, so `group_lights()`, group select and Shift+click ranges all follow the new order with no further changes. The ordering note in "Post-v2 polish" above now matches the code.

## v3 task 02: presets

**Components**
- `preset_items()` numbers each item `zlib.crc32(key) & 0x7FFFFFFF`, so the stored dropdown value follows the preset, not its position.
- `cached_user_presets()` / `clear_user_presets_cache()` in `__init__.py`: a module-level cache keyed by the presets folder's `st_mtime_ns`. Save and delete clear it.
- `LIGHTHOUSE_OT_save_preset` has an `overwrite` BoolProperty. It refuses when `preset_path()` already exists (so `Key/Fill` collides with `Key_Fill`), its dialog `draw()` shows a warning and the checkbox, and a successful save selects the new preset.
- `LIGHTHOUSE_OT_delete_preset` resets the dropdown to `CANDLE` when it deletes the shown preset. *(Superseded by v4 task 10: it selects the next preset instead.)*
- `apply_preset()` skips read-only (library / system override) light data and returns `(changed, incompatible, read_only)`. `preset_summary()` names both skip reasons.
- `LIGHTHOUSE_PT_presets.draw()` disables Apply and hides Delete while `settings.preset` is `''`.

**Data flow**
Dropdown value (CRC of the key) → `all_presets()` → `cached_user_presets()` → the JSON files, re-read only when the folder's mtime changes or after a save or delete. A file edited in place outside Blender doesn't change the folder's mtime, so the edit is picked up only after a restart.

**Blender API quirks**
- A dynamic enum stores the item number. Numbers derived from keys keep the selection stable.
- When the stored number has no item (for example, the file was removed outside Blender), the property reads `''`, and assigning `''` to another enum raises `TypeError`. That is why the panel guards it.
- Not verified: whether the save dialog redraws while you type. The overwrite warning may only update after the field is confirmed (Enter or Tab). Check this in the manual GUI test.

## v3 task 03: empty-scope feedback

**Components**
- `_lights_in_scope(context, scope)` in `__init__.py` returns the lights in scope and the warning to give when there are none: `No lights selected` for SELECTED, `No lights in the view layer` for ALL. `apply_preset` and `move_to_group` always use SELECTED.
- `scale_lights`, `step_exposure`, `apply_preset` and `move_to_group` report that warning and return `{'CANCELLED'}` when the scope is empty. When lights are in scope but none changed (all read-only or of an incompatible type), they report the usual summary as a WARNING and also cancel.
- `scale_lights` with `factor == 1.0` cancels silently, like `step_exposure` with `steps == 0`.
- The checks live in `execute()`, not `poll()`, because `poll()` can't read the `scope` property, and a greyed-out button doesn't say why.

**Data flow**
A cancelled operator pushes no undo step, so Ctrl+Z after a press that did nothing undoes the previous real change.

**Blender API quirks**
- In `--background`, reports are printed as `Info: <message>` and `Warning: <message>`. `tests/blender_runner.py` reads them with `reports(output, level="Info")`, and `run_in_blender_with_reports(snippet, level=...)` passes the level through.

## v3 task 04: empty state and expand/collapse all
- `lights.empty_message(view_layer, name_filter, type_filter)` returns `None` whenever `listed_lights()` has a match, because a light inside a collapsed group still draws its group header. Otherwise it returns "No lights match the filters" when the view layer has lights, and "No lights in this view layer" when it has none. The panel draws the message with the `INFO` icon and returns early, except in the grouped, unsearched list with `show_empty` on (see v4 task 06). In the filter case it also adds `lighthouse.clear_filters` (`INTERNAL`, no undo), which resets `name_filter` and `type_filter`.
- `lights.listed_groups(view_layer, type_filter)` walks the non-excluded layer collections and keeps every collection whose `all_objects` holds a listed light, whatever its collapse state.
- `lighthouse.toggle_all_groups` (`INTERNAL`, no undo) replaces `collapse_all_groups`. It expands every listed group when all of them are collapsed and collapses all of them otherwise. The header icon is `FULLSCREEN_ENTER` when everything is collapsed and `FULLSCREEN_EXIT` otherwise.

## v3 task 05: exit solo and snapshot updates
- New components: `lights.unsolo(solo)` (was `_unsolo`), `lights.solo_label(solo)` (the soloed light's or collection's name, or `"deleted"` once its pointer is `None`), `lights.update_snapshot(solo, id, hide)`, and `lighthouse.exit_solo` (`UNDO`, `poll()` requires `solo.active`). `LIGHTHOUSE_PT_lights.draw()` always draws it as an icon in the header row, before Add: `SOLO_ON` and pressed while solo is on, greyed out by `poll()` otherwise, so the list never shifts. A full-width row under the header was tried first and dropped because it pushed the list down whenever solo changed. The `description()` tooltip reads `Exit Solo (<label>)`.
- Mute and hide flow: `mute_light` and `hide_group` set the flags as before, then call `update_snapshot()`. While solo is on, it writes `hide` to both flags of the matching `objects` or `collections` item. An ID without an item (a collection solo never unhid) is left alone, so un-solo still ignores it. What you set during solo is what un-solo restores.
- Quirks: `update_snapshot()` compares pointers in both lists rather than checking the ID type, because `lights.py` doesn't import `bpy`. A group that starts fully hidden and is hidden again during solo ends hidden either way, so the test starts `Interior` render-only hidden to tell the two behaviours apart. The tooltip label is read when it is shown, so it follows renames without extra code. Not yet checked: the manual GUI pass (row appears and disappears, label follows renames, one Ctrl+Z after Exit Solo brings solo back) and an engine smoke re-run with the new `exit_solo` step.

## v3 task 06: lookup by name and library
- New components: `lights.id_key(id)` returns `(name, library filepath or "")`, `lights.find_object(view_layer, name, library)` returns the object only if it is in the view layer, and `lights.find_collection(name, library)`. `select_light`, `mute_light`, `solo_light`, `toggle_details`, `toggle_group`, `select_group`, `move_to_group`, `hide_group` and `solo_group` gain `library: StringProperty(options={'HIDDEN'})`, default `""`. `exit_solo` takes no target and is unchanged. The panel sets both properties through one draw helper, `target(op, id)`.
- Tuple-key lookup, checked on Blender 5.2.2 (4.2 was not available to check): `bpy.data.objects.get((name, filepath))` returns the ID linked from that library, and `get((name, None))` returns the local one. `get((name, ""))` returns `None`, so the helpers map `""` to `None`. The filepath must match `id.library.filepath` exactly, which is why `id_key()` reads it from the ID.
- Fallback: when `library` is `""` and no local ID has the name, `_lookup()` falls back to a plain `get(name)`. This keeps name-only calls working for linked data that has no local namesake (`test_move_into_a_library_collection_is_refused_and_nothing_moves`, `move_to_group(name="Linked")`). A local ID always wins over a linked one with the same name. Not yet checked: the manual GUI pass (the eye on a linked `Key` row and a local `Key` row each hide only their own light).

## v3 task 07: 4.2 verification
Checked on Blender 4.2.23 LTS (portable build) against 5.2.2 LTS. The add-on code needed no changes for 4.2. Every difference was already guarded, and the fixes went into the tests.
- `Light.exposure` (4.4+) and `Light.use_temperature` / `temperature` (5.0+) are missing on 4.2. `has_property()` keeps them out of the details and away from `apply_preset`, so built-in presets set their RGB fallback color. The tests read the expected detail list from `blender_runner.NEWER_DETAILS` and expect the RGB color below 5.0. Tests that set these properties skip with `needs_blender(major, minor, what)`.
- `bpy_extras.anim_utils.action_get_channelbag_for_slot` and `AnimData.action_slot` are missing on 4.2. The keyframe scaling already falls back to `action.fcurves`, and the keyframe tests now do the same.
- The EEVEE engine id is `BLENDER_EEVEE_NEXT` on 4.2 and `BLENDER_EEVEE` on 5.2. The add-on only compares the id with `'CYCLES'`. The test prelude's `EEVEE` and `smoke_engines.py` pick whichever id the running Blender lists.
- The same on both versions: `invoke_props_dialog(title=...)`, which 4.2 accepts, and the `(name, library)` tuple keys for `bpy.data.*.get()`, which pass `test_library_lookup.py` on 4.2.
- Tooling: the tests run `$BLENDER` (via `blender_runner.blender_binary()`), and `make test BLENDER=...` passes it through. `RowState.shared` was removed because the info icon reads `light.users` directly.

## v4 task 01: foldable lights row
- New components: `lights.LightsEntry(collection, depth, count)`, `lights.is_lights_folded(collection)` (reads `lighthouse_lights_collapsed`, `False` while unregistered), `Collection.lighthouse_lights_collapsed` (BoolProperty, default `False`, saved in the .blend), `lighthouse.toggle_lights_row` (`INTERNAL`, no undo, `name` + `library`) and `LIGHTHOUSE_PT_lights.draw_lights_row()` (indent, disclosure triangle, `Lights (N)` label with the `LIGHT` icon, no action buttons).
- `_collection_entries()` gathers a collection's sub-collection entries first, then decides how to list its own lights. With own listed lights and at least one listed sub-collection, it emits a `LightsEntry` at the collection's content depth and the lights one level deeper. Folded, the row stays and its lights are dropped. A leaf collection lists its lights directly. Depth 0 (the Scene Collection, or the collection `group_lights()` starts from) never gets a row.
- Folding only changes what is drawn: `GroupEntry.count`, `group_lights()` and `listed_groups()` still include every light. `select_light`'s `RANGE` keeps only `LightEntry` rows, so a folded row's lights are not selected. The fold is independent of `lighthouse_collapsed`, so collapsing and expanding a collection keeps its lights row folded.

## v4 task 02: Expand All and lights rows
- `lighthouse.toggle_all_groups` also sets `lighthouse_lights_collapsed = False` on every collection from `listed_groups()` when it expands. When it collapses, lights rows are left as they are.
- The "all collapsed?" check, used for both the action and the `FULLSCREEN_ENTER` / `FULLSCREEN_EXIT` header icon, still reads only `lighthouse_collapsed`. A folded lights row never changes what the button does.

## v4 task 03: active collection
- New components: `lights.find_layer_collection(layer_collection, collection)` (was `_find_layer_collection`, now public) and `lighthouse.set_active_collection` (`name` + `library`), which sets `view_layer.active_layer_collection` to the collection's non-excluded layer collection. It never touches the selection or the active object, and it cancels when the collection is unknown or excluded. `draw_group()` draws the `Name (N)` label as this operator's button with the collection icon: flat normally, embossed and pressed when it is the active collection.
- Undo: clicking a collection in the Outliner runs `outliner.item_activate`, whose `bl_options` are `{'REGISTER', 'UNDO'}` (checked on 5.2.2), so `set_active_collection` is `{'REGISTER', 'UNDO'}` too.
- Because it is Blender's own active collection, the choice stays in sync with the Outliner and Shift+A, and `add_light` already links there. A library collection can be made active (the Outliner allows it), and `+` then refuses with its read-only error.

## v4 task 04: Scene Collection row
- New components: `lights.SceneEntry(collection, count)`, first in the grouped list (not in flat mode or while searching). `count` is the Scene Collection's own listed lights. Those lights follow at depth 0 unless `scene.collection.lighthouse_lights_collapsed` is set, and top-level collections stay at depth 0, so the tree doesn't shift. `LIGHTHOUSE_PT_lights.draw_scene_row()` draws the fold triangle (a `BLANK1` of the same width when there are no own lights), the `Scene Collection` name as the `set_active_collection` button (pressed while the master layer collection is active), then blanks for Select, Hide and Solo around Move here, so Move here lines up with the other headers. The open questions took their defaults: no Select, and no count in the label.
- Targeting the master collection: it isn't in `bpy.data.collections`, so `name=""` means `context.scene.collection` (no ID has an empty name). `scene_or_collection(context, name, library)` resolves it for `toggle_lights_row` and `move_to_group`. `set_active_collection` maps `""` to `view_layer.layer_collection`. The draw code sets `name = ""` explicitly, so a button never picks up the last-used name.
- `toggle_all_groups` also unfolds the Scene Collection's lights when it expands. Collapse All leaves them alone, and they don't count towards "all collapsed?". `lighthouse_lights_collapsed` on the master collection is saved with the scene (checked through save and reopen). `move_lights()` already unlinks from `scene.collection`, so moving into it needed no new logic.

## v4 task 05: show empty collections
- New components: `LIGHTHOUSE_PG_settings.show_empty` (WindowManager, default `True`, not saved or undone, left alone by `clear_filters`), drawn as an `OUTLINER_COLLECTION` icon toggle next to the grouped toggle. `list_entries(..., show_empty=False)` and `listed_groups(..., show_empty=False, foldable_only=False)` list every non-excluded collection when it is on, with count `0` when nothing under it is listed. The defaults keep today's list. The panel, `select_light`'s `RANGE` and `toggle_all_groups` pass the setting.
- `GroupEntry.foldable` (default `True`) is set when anything is listed under the collection: its own lights, or sub-collections (empty ones count while shown). The lights row rule counts shown empty sub-collections too. `draw_group()` draws a `BLANK1` instead of the triangle when it is not foldable, and greys out Select and Solo (sub-rows with `enabled = False`) at count `0`, while Move here and Hide stay enabled.
- `all_collapsed(view_layer, filters)` drives the toggle-all action and its header icon. It uses `listed_groups(..., foldable_only=True)`, so empty collections without a triangle don't count, while toggle-all still collapses and expands everything listed. The older toggle-all tests set `show_empty = False`, because the factory scene's empty `Collection` would otherwise join in.

## v4 task 06: empty-state message above the collection tree
- `lights.tree_under_message(grouped, name_filter, show_empty)` decides what the panel draws when `empty_message()` returns a message. In the grouped, unsearched list with `show_empty` on, it draws the message (and Clear Filters when a filter is the cause) and then the usual `list_entries()` tree, all at `(0)`, so `+`, Move here and making a collection active still work. Otherwise it draws the message and returns, as before. The message wording is unchanged.

## v4 task 07: New Collection
- New component: `lighthouse.new_collection` (`REGISTER`, `UNDO`), drawn as a `COLLECTION_NEW` icon button next to `+`. The button asks for a name in a dialog (`invoke_props_dialog`, default `Collection`; a blank name falls back to it). It creates `bpy.data.collections.new(name)` (Blender adds `.001` on a clash) inside `view_layer.active_layer_collection.collection`, which is the Scene Collection when the master is active, and makes the new collection's layer collection active through `find_layer_collection()`. It never touches the selection.
- A library parent is refused with an `ERROR` report ("… is read-only (linked from a library)") before anything is created, the same as `add_light`. Creating inside a collapsed collection leaves folding alone (the open question's default). With `show_empty` on, the new collection is listed right away as `(0)`.

## Collection rename (Ctrl+click)
- `lighthouse.set_active_collection` gains `action` (`ACTIVATE`/`RENAME`) and `new_name`, the same pattern as `select_light`. `invoke` picks `RENAME` on Ctrl and opens a "Rename Collection" dialog pre-filled with the current name. The name is stripped. A blank name, or a library collection, is refused with an `ERROR`. Ctrl+click on the Scene Collection cancels, because the master collection can't be renamed. Renaming never changes the active collection.

## v4 task 08: reveal active light
- `lights.reveal(view_layer, obj)` expands every non-excluded collection that holds `obj` directly, plus its ancestors (via `_collection_paths()`), and unfolds those holders' lights rows, or the Scene Collection's fold when the master holds `obj`. It changes nothing else, so siblings stay collapsed. A light in two collections is revealed in both.
- New component: `lighthouse.reveal_active_light` (`INTERNAL`, no `UNDO`, like `toggle_group`), a `VIEW_ZOOM` button in the list header (grouped, unsearched mode only, next to toggle-all). `poll()` needs the active object to be a light. The panel can't be scrolled from Python, so it only unfolds. Filters are not cleared.
- `add_light` calls `reveal()` after linking, so a light added into a folded collection shows up. There is no selection-change handler, because revealing on its own would undo the user's folding and mark the file as changed.

## v4 task 09: scope starts as Selected
- `LIGHTHOUSE_PG_settings.scale_scope` defaults to `SELECTED` (the toggle still reads All | Selected). It lives on the WindowManager, so it is not saved in the .blend and every session starts at Selected. The operators' own `scope` property is unchanged, and the panel always passes the chosen scope.

## v4 task 10: presets as plain files
- `presets.py`: `BUILTIN_PRESETS` is now the tuple `DEFAULT_PRESETS`, used only to write files. `restore_default_presets(folder)` writes each default whose `preset_path()` is missing and returns the labels written, never overwriting anything. `seed_default_presets(folder)` calls it once and then writes `.defaults_installed` (not `*.json`, so `user_presets()` ignores it). A default the user deletes stays deleted.
- `presets_folder()` seeds on its first call of the session (a module flag), so even a Save before any draw sees `Candle.json`. `all_presets()` is `cached_user_presets()`. `preset_items()` has icon `NONE` and no description, sorted by label ignoring case. Save has no reserved names, so `Candle` follows the exists/Overwrite flow. Delete offers every preset, and when it deletes the shown one it selects the next in dropdown order, or the new last one, or assigns nothing when none are left (assigning `''` raises `TypeError`). It reads `self.preset` before deleting, because the dynamic enum resolves to another item once the file is gone. The panel shows Delete whenever a preset is set.
- Known cost (item 17): a default's key changed from `CANDLE` to `USER:Candle`, so a .blend saved with a built-in selected opens with nothing selected. The panel handles `''`. There is no migration.

## v4 task 11: restore default presets
- New component: `lighthouse.restore_default_presets` (no confirm, no `UNDO`, because preset files aren't part of undo), a Restore button next to Save and Delete *(superseded by v4 TICKET-12: the button is in the add-on Preferences)*. It calls `restore_default_presets(presets_folder())` and clears the presets cache. It reports `INFO` "Restored Candle, Daylight", or "Every default preset is already there".
- It only writes missing files, so edited defaults and other presets are left alone and a full folder isn't touched (same mtime). To reset an edited default, delete it and press Restore. The selection is left alone even when the dropdown is empty (the open question's default).

## v4 TICKET-12: Restore moves to Preferences
- The presets panel row is back to Save and Delete. New `LIGHTHOUSE_AP_preferences` (`AddonPreferences`, `bl_idname = __package__`) draws a "Restore Default Presets" button for the same operator and the hint "Brings back deleted defaults. Defaults you edited are kept."
- The operator, `restore_default_presets()` and seeding are unchanged.

## v5 task 01: group context menu
- New components: `draw_group_menu(self, context)`, prepended to Blender's `UI_MT_button_context_menu` in `register()` and removed in `unregister()`, and `LIGHTHOUSE_MT_new_light` (one `add_light` entry per `LIGHT_TYPES` item). `draw_group_menu` only draws when `context.button_operator` belongs to a header's name button (`set_active_collection`, so group headers and the Scene Collection row). It then draws New Light ▸ and New Collection in a column, followed by a separator. The column is disabled when the collection `is_read_only`. Light rows, header icons and the search field get Blender's plain menu.
- `add_light` and `new_collection` gain hidden `name`, `library` and `use_active` (default `True`), all `SKIP_SAVE`. With `use_active` off they use `target_layer_collection(context, name, library)` (name `""` is the Scene Collection) and cancel when it is `None` (missing or excluded). Read-only targets are refused as before. `add_light` then makes the target active. `new_collection` makes the new collection active, as before. The header `+` and the New Collection button don't set a target. `new_collection`'s dialog field is renamed from `name` to `new_name`, as in the rename dialogs. `target_collection(op, context, collection)` fills a button's target, with `""` for the master collection.
- The submenu gets its target through `layout.context_pointer_set("lighthouse_collection", collection)` before `layout.menu()`. `LIGHTHOUSE_MT_new_light` reads `context.lighthouse_collection` and, when it is missing, adds to the active collection (for task 02's header `+`).
- Tests: `tests/blender_runner.RECORDER` holds the `Recorder` fake layout (moved from the preferences test). It records operators with the properties draw set, plus menus, enum menus, separators, context pointers and `enabled`, and `FakeContext` supplies `button_operator` and context pointers.

**Blender API quirks**
- A button's operator properties (`context.button_operator`) tell their operator apart by `bl_rna.identifier`, for example `LIGHTHOUSE_OT_set_active_collection` (the same as `Class.bl_rna.identifier`). This was checked headless only. Reading it in the real right-click menu, and the context pointer reaching the submenu, still need the GUI check.
- `bpy.ops` calls from Python never reuse an operator's last properties, so `SKIP_SAVE` can only be seen headless as `is_skip_save` on the RNA properties.
- Menu draw functions added with `prepend()` live in `Menu.draw._draw_funcs`.

## v5 task 02: compact header +
- New component: `LIGHTHOUSE_MT_new`, drawn in the Lights panel header as `row.menu(..., text="", icon='ADD')` where the `+` enum menu was. It holds New Light ▸ (`LIGHTHOUSE_MT_new_light` with no context pointer, so it adds to the active collection) and New Collection (`use_active` on), in a column disabled when the active collection `is_read_only`.
- The separate New Collection button is gone, so the header row has one button fewer (7 when grouped and not searching). That slot is free for task 03. The menu is drawn in every mode, so adding works flat, while searching and with a type filter that hides every header.
- Tests: `tests/test_header_new_menu.py` draws the panel through the Recorder with a stand-in that carries the panel's `draw_*` methods, and takes everything before the type filter row as the header. The Recorder's `menu()` now records the icon when one is given.

## v5 task 03: Color/Kelvin toggle
- New pure functions in `lights.py`: `new_light_mode(scene_value, default)` (`'FOLLOW'` means the default applies), `toggled_mode(scene_value, default)` (flips the mode in effect, and returns `'FOLLOW'` when the result is the default, so a file stores a mode only while it differs) and `supports_temperature()` (`use_temperature` in `Light`'s RNA, Blender 5.0+).
- New `Scene.lighthouse_new_lights` (`FOLLOW`/`COLOR`/`KELVIN`, default `FOLLOW`, saved with the .blend), `default_new_light_mode(context)` (always `'COLOR'` until task 04 reads the preferences) and `lighthouse.toggle_new_light_mode` (`REGISTER`, `UNDO`, because the value is file data and undoing something else would otherwise revert it). Its `description()` reads, for example, "New lights start in Kelvin (this file)".
- The header draws the toggle right after `+`, in the slot New Collection left, pressed in Kelvin with `LIGHT_SUN` (Kelvin) or `COLOR` icons. Before 5.0 it isn't drawn and `add_light` ignores the mode.
- `add_light` in Kelvin mode sets `use_temperature`, the RNA default `temperature` and a white `color` (so the tint doesn't skew the temperature). Color mode leaves Blender's default color.
- No depsgraph handler (decisions item 9): a handler can't reliably tell a new light from a duplicated or appended one, and would quietly change lights the user copied. So only Lighthouse's New Light (header `+`, group menu) follows the mode. Shift+A, duplicates and appends are left alone, and a test pins that.

## v5 task 04: Color/Kelvin default
- `LIGHTHOUSE_AP_preferences.new_light_mode` (`COLOR`/`KELVIN`, default `COLOR`) is drawn as "New lights start in" (expanded) above Restore Default Presets, only when `supports_temperature()`. `default_new_light_mode(context)` reads it through `context.preferences.addons.get(__package__)`, and falls back to `'COLOR'` when the add-on isn't installed (the `import lighthouse; register()` tests).
- Pin/un-pin rule: `Scene.lighthouse_new_lights` is `FOLLOW` until the header toggle is flipped. A `FOLLOW` file uses the current preference, including later changes to it. A flip stores the opposite of the mode in effect (`COLOR` or `KELVIN`), which pins the file. A flip that lands on the default stores `FOLLOW` again (`toggled_mode()`, unchanged from task 03). So a file stores a value only while it differs from the default it was toggled against. If the default later changes to match a pinned value, the file stays pinned until it is toggled.
- The toggle's tooltip says "(Preferences default)" or "(this file)".
- Tests: `tests/test_new_light_default.py` uses `run_installed`. The test runs use `--factory-startup`, which skips `userpref.blend`, so the restart test calls `bpy.ops.wm.read_userpref()` in its second run. That call crashes Blender 4.2 headless, so the test is skipped there (the setting is hidden before 5.0).

## v5 task 05: World panel
- `lights.world_setup(scene)` returns `WorldSetup(state, source, background, environment)`. `source` is the node linked to the active World Output's Surface (`node_tree.get_output_node('ALL')`). The state is `SIMPLE` only when `source` is a Background node whose Strength input is not linked. A linked Strength (the slider would do nothing), any other source (Mix Shader, node group), nothing linked to Surface, or `use_nodes` off all give `CUSTOM`. No world gives `NONE`. `environment` is the Environment Texture linked to the Background's Color, if any.
- `LIGHTHOUSE_PT_world` draws Strength for `SIMPLE` (disabled on a read-only world), "Custom world setup, edit in Shader Editor" for `CUSTOM` and "No world in this scene" for `NONE`.
- Panel order (superseded by v6 task 04's `bl_order`): with no `bl_order`, registration order set the default order, so `classes` registered Lights, World, Intensity, Presets. In new layouts Lights now comes before Intensity and Presets. Layouts where the user dragged the panels keep their order.
- Intensity actions only touch lights, so scope All leaves the World strength alone (item 18, pinned by a test).

## v5 task 06: World rotation
- `WorldSetup` gains `mapping` and `rotation` (both default `None`). With an environment, `rotation` is `'MAPPING'` when a Mapping node feeds its Vector, `'ADDABLE'` when Vector is unlinked, and `'CUSTOM'` for anything else. With no environment it is `None`.
- `add_world_rotation(node_tree, environment)` adds Texture Coordinate (Generated) → Mapping → Vector, placed 400 and 200 units left of the texture. `lighthouse.add_world_rotation` (`REGISTER`, `UNDO`, so one Ctrl+Z removes both nodes) cancels unless the world is `SIMPLE` and `ADDABLE`, and refuses a read-only world.
- The World panel draws the Mapping's Rotation Z (`index=2`, an Euler socket, so it shows in degrees) for `MAPPING`, Add Rotation for `ADDABLE`, and nothing for `CUSTOM` or no environment.

## v5 task 07: World mute
- Verify result (8×8 px, 1 sample, camera only, white Backgrounds, rendered 2026-10-10 in Cycles and EEVEE on 4.2.23 and 5.2.2): a muted Background renders black (max RGB 0.004). A muted node group also renders black. A muted Mix Shader passes its first shader through at full brightness. Since not everything renders black, the item 16 fallback applies: Mute acts on the detected Background of a `SIMPLE` setup only, and is greyed out for `CUSTOM` ones.
- `world_mute_node(setup)` (the Background for `SIMPLE`, else `None`) and `world_muted(setup)`. `lighthouse.mute_world` (`REGISTER`, `UNDO`) flips `node.mute`, so the mute shows red in the Shader Editor and is saved with the file. It cancels when there is no node to mute or the world is read-only. Strength is never touched.
- The World panel now starts with a row holding the world's name and Mute (`HIDE_ON`/`HIDE_OFF`, `depress` when muted, like a light row). There is room for task 08's Solo. While muted, the Strength/Rotation column is drawn inactive.
- The Cycles render check is kept as `test_muted_background_renders_black_but_a_muted_mix_shader_passes_through` (it takes about a second). The test Recorder now marks pressed operators (`"pressed"`) and inactive layouts (`"inactive"`).

## v5 task 08: World in solo
- `LIGHTHOUSE_PG_solo` gains `world_soloed` and a World snapshot: `world_saved`, `world` (World pointer), `world_node` (the node's name) and `world_muted` (its `mute` before solo). Only World solo takes it.
- `lights.toggle_solo_world(solo, view_layer, scene)` calls `_solo(solo, view_layer, [], [])` (every light hidden, light snapshot kept when switching), then snapshots `world_mute_node()` and un-mutes it. No world, or a `CUSTOM` setup, only hides the lights. Pressing it again during a World solo calls `unsolo()`. `lighthouse.solo_world` (`REGISTER`, `UNDO`) wraps it, drawn as `SOLO_ON`/`SOLO_OFF` after Mute in the World panel's top row (not greyed out with Mute, since a World solo without a node still darkens the lights).
- Data flow: lamp and group solo leave the World alone; for a full solo the user mutes the World. Switching from World solo to a lamp or group restores the World's `mute` right away and clears the World snapshot (`_leave_world_solo`), while the light snapshot carries on as for any switch. `unsolo()` restores the node's `mute` when the snapshot exists and the world and node (looked up by name in `world.node_tree`) still exist, then clears it and `world_soloed`. A deleted node is skipped, and the lights are still restored.
- `mute_world` calls `update_snapshot(solo, node, node.mute)`. During a World solo that writes `world_muted`, so un-solo keeps the choice. Without a World snapshot (a lamp solo) it is a plain mute. `solo_label()` returns `"World"`, so `exit_solo`'s tooltip reads `Exit Solo (World)`.
- The 5 exact-list World panel expectations in `test_world_panel.py` and `test_world_rotation.py` gained the Solo button. Not yet checked: the manual GUI pass (HDRI stays lit on a lamp solo, only the HDRI lights a World solo, Exit Solo re-mutes the World).

## v5 task 09: light linking receivers
- Verify result: Link Selected can't pick up collections selected in the Outliner. `selected_ids` needs an Outliner area under `context.temp_override()`, and the sidebar's operator has no reliable one (none at all headless, where `context.window` is `None`, so it can't be tested either). So Link Selected links selected objects only, noted in the README. Child collections already in the receiver collection are still listed and removable.
- `lights.Receiver(id, kind, state)` and `receivers(obj)`: child collections first, then objects, each sorted by name ignoring case. `collection_children` / `collection_objects` take only integer indices (no string keys), in the same order as `children` / `objects`, so states are paired up by position.
- `link_receivers(light_obj, ids, state)` creates "Light Linking for <light>" when there is no receiver collection, links ids not yet in it, sets `state` on every given id and skips the light itself; returns `(added, updated)`. `remove_receiver(light_obj, id)` unlinks one object or child collection.
- `lighthouse.link_receivers` (`REGISTER`, `UNDO`, `name`/`library`/`state`) warns "No objects selected" and cancels when only the light is selected, and refuses a read-only light or receiver collection. `lighthouse.remove_receiver` (`REGISTER`, `UNDO`) takes the light's `name`/`library` plus `receiver`, `receiver_library` and `kind`. `draw_linking(box, obj)` (module level, so the Recorder can call it) ends `draw_details()`. Not yet checked: the manual GUI pass in a Cycles Rendered viewport.

## v5 task 10: exclude, clear and sharing
- Exclude Selected is `link_receivers` with `state='EXCLUDE'`: listed items only change state. `Receiver` gains `link` (the `CollectionObject`/`CollectionChild`), and each row draws `prop(link.light_linking, "link_state", expand=True)`, so the Include/Exclude toggle has undo with no operator.
- `clear_receivers(light_obj)` unlinks every object and child collection and keeps the collection assigned (open question default): every light sharing it changes, as the label warns. `lighthouse.clear_receivers` (`REGISTER`, `UNDO`) refuses read-only data and is greyed out for an empty list.
- `receiver_users(collection)` scans `bpy.data.objects` for lights using the collection. `shared_label(obj)` names the other lights, at most `SHARED_NAMES = 3` then "…" (open question default), and counts all of them, drawn with `INFO` under the buttons. Not yet checked: the manual GUI pass (exclude darkens one object in Cycles, both sharing lights show the label).

## v5 task 11: linking row icon
- `linking_tooltip(included, excluded, included_collections=0, excluded_collections=0)` ("Lights only 3 objects, excludes 1", "Excludes 2 objects", "" for none). Child collections are named separately (open question default): "Lights only 2 objects and 1 collection, excludes 1". `linking_counts(obj)` returns the four counts from `receivers()` in that argument order.
- `draw_light()` draws `lighthouse.light_linking_info` (`INTERNAL`, `LINKED`, no emboss) right after ⓘ and before power, only when the tooltip isn't "". Like ⓘ, the name button gives up the room, so the power/color/toggle columns stay put. Its `description()` is the tooltip, and its `invoke` opens the details (Shift keeps others open, as `toggle_details`) but never closes open ones. Not yet checked: the manual GUI pass (column alignment, tooltip, click opens details).

## v5 task 12: engine note
- Verify result (16×16 px factory scene, world strength 0, the Cube excluded from the Light, rendered 2026-10-10; max RGB lit → excluded):

  | Blender | Cycles | EEVEE | Workbench |
  |---|---|---|---|
  | 4.2.23 | renders (0.83 → 0.01) | **not rendered** (0.84 → 0.84, EEVEE Next) | not rendered (0.56 → 0.56, ignores scene lights) |
  | 5.2.2 | renders (1.0 → 0.02) | renders (1.0 → 0.004) | not rendered (0.57 → 0.57) |

- Versions between 4.2 and 5.2 weren't checked, so `EEVEE_LIGHT_LINKING = (5, 0)` (EEVEE may already render it in 4.3/4.4, where the note would then be wrong). `light_linking_note(engine)` returns `None` for Cycles (and EEVEE from 5.0), else "Not rendered in <engine>, Cycles only" / "…, Cycles and EEVEE only". Unknown engines get the note (open question default).
- `engine_name()`: the RenderSettings engine enum lists only some built-ins headless (5.2 shows just `BLENDER_EEVEE`), so built-ins come from `ENGINE_NAMES` and third-party engines from their registered `RenderEngine.bl_label`.
- `draw_linking(box, obj, engine)` draws the note with `INFO` under the "Light Linking" label; buttons and rows stay enabled. The probe is kept as `test_excluding_the_cube_darkens_it_in_engines_without_a_note` (Cycles and EEVEE, ~1 s). The draw tests set Cycles, since 4.2's factory engine is EEVEE. Not yet checked: the manual GUI pass (switching engines with details open).

## v5 release
- Version 1.3.0 (the open question's default). `make test`: 5.2.2 266 pass, 1 skip; 4.2.23 254 pass, 13 skip (the 5.0+/4.4+ property tests and the 4.2 `read_userpref` crash). `make validate` passes on both, `make build` writes `dist/lighthouse-1.3.0.zip`.
- `make install` now installs `dist/lighthouse-$(VERSION).zip` (read from the manifest). The old `lighthouse-*.zip` glob passed every zip in `dist/` and failed once an older one was left there. On 4.2.23, `make install` into a clean `BLENDER_USER_RESOURCES` profile and the engine smoke (Cycles, EEVEE Next) pass. On this machine's system 5.2.2 (Fedora package) the extension system can't load (`bl_pkg` needs `cattrs`, so `bl_ext` doesn't exist), so neither the install nor the smoke can run there. The 5.2.2 pytest suite runs the add-on from source.
- Known limits:
  - Light linking edits receivers only (no shadow linking). Link Selected doesn't pick up collections selected in the Outliner (task 09).
  - Light linking renders in Cycles, and in EEVEE from 5.0 (checked on 5.2.2; 4.2's EEVEE Next doesn't). Versions between 4.2 and 5.2 weren't probed, so the EEVEE note may be wrong on 4.3/4.4. Workbench never renders it (task 12).
  - World Mute uses the fallback: it mutes the detected Background of a simple world only and is greyed out for custom setups, since a muted Mix Shader passes its first input through (task 07).
- Not done: the manual GUI pass (tests/acceptance.md, v5 section) on 5.2 and 4.2, which needs someone at Blender.

## v6 task 01: New light defaults
- `bpy.data.lights.new()` and Shift+A (`object.light_add`) start lights differently. `LIGHTHOUSE_OT_add_light` applies `SHIFT_A_VALUES` right after `lights.new()`, so every Lighthouse add (the `+` menu, a group's right-click New Light) matches Shift+A. Checked in 5.2.2:

  | Type | `lights.new` | Shift+A (the table) |
  |---|---|---|
  | Sun | `energy` 10 W/m² | `energy` 1.0 |
  | Area | `size`, `size_y` 0.25 m | `size`, `size_y` 1.0 |

  Point and Spot already match (power, radius, spot size), so they have no entry.
- Why one table: one place to add a type if Blender's two code paths drift apart again. It runs before the Kelvin step, which only touches `use_temperature`, `temperature` and `color`, so the two stay independent.
- Released on its own as 1.3.1.

## v6 task 02: Benchmark
- `make bench` (`BLENDER=` works as for `make test`) runs `tests/bench_lights_panel.py`, which pytest doesn't collect (no `test_` prefix). It builds 500 lights (all four types) spread over 65 nested collections (5 top-level, each with 4 sub-collections, each of those with 2), grouped mode on and 5 rows expanded. Then it times `LIGHTHOUSE_PT_lights.draw()` over 9 passes after a warm-up and prints the median, min and max in ms.
- The draw runs on the suite's `Recorder` stub layout (`blender_runner.RECORDER`, the same as the draw tests), since a real `UILayout` doesn't exist headless. So it measures Lighthouse's own Python (the list walk, row state, linking counts), not Blender's widget layout.
- There's no budget and no failing threshold, since timing fails at random on a busy machine. The number is compared by hand before a release. Caching (by depsgraph update) is only worth adding if it is well over about 10 ms.
- Baseline (AMD Ryzen 9 9900X, 2026-10-17): **15.7 ms** on 5.2.2, 14.7 ms on 4.2.23 (median of 9).

## v6 task 03: Active Light panel
- Prefactor: a row's controls and its details box moved out of `LIGHTHOUSE_PT_lights` into module functions that take a layout. `draw_light_controls(row, context, obj, state, other_collections)` draws everything after the details toggle (type, name button, ⓘ and linking icons, power, unit, color or Kelvin, mute, solo). `draw_light_details(layout, obj, state, engine)` draws the box (name, the type's settings, light linking). The panel's `draw_light` and `draw_details` methods stay as thin wrappers, so the draw tests that call them run unchanged.
- `LIGHTHOUSE_PT_active_light` ("Active Light", same space, region and category). With a light active, it draws one row with `draw_light_controls` and then `draw_light_details`, with `row_state()` deciding read-only (disabled) and dimmed (inactive) exactly as for a list row. Mute and solo are the row's operators, so solo state and snapshots stay shared. The ⓘ count of other collections is `len(users_collection) - 1`, which matches what the grouped list counts for a light listed once per collection.
- No `poll`: with a non-light or nothing active it draws "Select a light". Hiding it would make every panel below jump up and down as you click between meshes and lights.
- Following the viewport selection in the list isn't built (v6 decision 9). Panel order is task 04. Until then the panel registers last.
- `make bench` (Lights panel only): 16.1 ms after this task, vs the 15.7 ms baseline (noise). The Active Light panel draws one light, so it adds about one row and one details box per redraw.

## v6 task 04: Panel order
- `bl_order` on all five panels: Active Light 0, World 1, Intensity 2, Presets 3, Lights 4. This replaces v5 decision 12's registration order. The short panels stay at fixed places, and the tall list goes last. `LIGHTHOUSE_PT_presets` has `bl_options = {'DEFAULT_CLOSED'}`, and Intensity stays open.
- Verify (does `bl_order` override a layout saved in a file?): **not settled**. Blender documents `bl_order` as the *default* order, and each panel's position is saved in the file's screen layout (see above), so a 1.3.x file should keep its saved order and only new panels and new files follow `bl_order`. A headless check isn't possible: Python can't read a region's panel order, and on 4.2 `Region.active_panel_category` is read-only, so a scripted GUI screenshot can't open the Lights tab. This is left to the manual GUI check (open a 1.3.x file with dragged panels). If it turns out `bl_order` overrides a dragged layout, the README says so (no workaround).

## v6 task 05: Light right-click menu
- `draw_light_menu()` is prepended to `UI_MT_button_context_menu` next to `draw_group_menu()`, and is registered and removed with it. It draws only when `context.button_operator` is `LIGHTHOUSE_OT_select_light` (a row's name button), and finds the light from that button's `name` and `library` with `find_object()`. A missing light draws nothing. It ends with a separator, so Blender's own entries follow.
- Final entry order (later tasks fill the gaps): Rename, Frame, (Duplicate, Duplicate Linked, Delete, Apply Preset ▸, Mute: tasks 06/07), Solo, (Add to Solo: task 09).
- Rename is a new `LIGHTHOUSE_OT_rename_light` (an `invoke_props_dialog` with a name field, like Ctrl+click). It renames only the object, never the light data. `select_light`'s RENAME couldn't be reused from a menu: its `invoke` picks the action from the click's modifier keys. It's disabled (and refused in `execute`) for a library light.
- Frame is `select_light` with `action='FRAME'`, drawn with `operator_context = 'EXEC_DEFAULT'` so `invoke` doesn't reset the action. Solo is `solo_light`, labelled "Exit Solo" when that light is a solo target (`is_solo_target()`). Neither edits the light, so both stay enabled on library lights.

## v6 task 06: Delete and duplicate
- Selection rule (`light_scope()` in `lights.py`, reused by task 07): as in the Outliner, an entry acts on every selected light when the clicked light is selected, otherwise only on the clicked light. `scope_label()` gives "Delete" for one and "Delete 3 Lights" for more (the same for Duplicate and Duplicate Linked).
- `LIGHTHOUSE_OT_duplicate_lights` (`linked` false is Shift+D, true is Alt+D): `obj.copy()` plus a `data.copy()` unless linked, linked into every collection of the original, with no grab afterward. The copies become the selection, and the clicked light's copy becomes active. During solo, copies are unhidden. They have no snapshot item, so exiting solo leaves them shown.
- `LIGHTHOUSE_OT_delete_lights`: `bpy.data.objects.remove()` on each object, with no confirmation (Ctrl+Z restores). Light data is never removed directly: data with no users left is dropped by Blender when it saves or purges, as with the Outliner's Delete, so a shared light data block stays with its other object. A deleted soloed light leaves a snapshot item pointing at nothing, which `unsolo()` already skips.
- Read-only (library) lights in scope are skipped, and the Info report says how many ("Deleted 2 lights, skipped 1 read-only"). When every light in scope is read-only, the operator cancels with a warning.

## v6 task 07: Mute and Apply Preset in the light menu
- Menu order is now: Rename, Frame, Duplicate, Duplicate Linked, Delete, Apply Preset ▸, Mute, Solo (Add to Solo comes in task 09).
- `LIGHTHOUSE_OT_mute_lights` acts on `light_scope()`, following the clicked light: unmuted means every light in scope is muted, muted means they're all unmuted (`light_muted()`: hidden in both viewport and render, shared with the row's `mute_light`). Each changed light goes through `update_snapshot()`, as the row does. The label is "Mute"/"Unmute" plus the count from `scope_label()`.
- Quirk: setting `hide_viewport` deselects an object right away (Blender won't keep a disabled object selected), so a muted light is never in a selection. Right-clicking a muted light therefore always gets plain "Unmute" for that light alone. "Unmute 3 Lights" can't occur, and a selection's mute only ever mutes. Also, a light hidden by solo reads as muted (as on the row), so its entry is "Unmute".
- Apply Preset ▸ is `LIGHTHOUSE_MT_apply_preset`. The menu sets `context_pointer_set("lighthouse_light", obj)` and the submenu draws one `apply_preset` per preset with that light's `name`/`library`. `apply_preset` gained those two `SKIP_SAVE` hidden properties: set means `light_scope()` of that light, empty (the Presets panel) means the selected lights as before. Skipped-light reporting is unchanged (`preset_summary`).

## v6 task 08: Solo targets
- `LIGHTHOUSE_PG_solo.targets` is a CollectionProperty of `LIGHTHOUSE_PG_solo_target`, each holding an `object` (a soloed light) or a `collection` (a soloed group), with the other pointer empty. It replaces the `light` and `group` pointers. The snapshot (`objects`, `collections`) and the World fields are unchanged.
- `lights.py` reads it through `is_solo_target(solo, id)` (used by `row_state`'s `soloed`, `group_soloed`, both toggles and the menu label) and writes it with `set_solo_target(solo, id)` (clear, then one item). `_solo` and `unsolo` clear it. `solo_label` names the first target. Behaviour is as before: a click replaces the target, and clicking the only target ends solo. A read-only Python `light` property on the group returns the first soloed light, so older code and tests that read `solo.light` still work.
- Verify result: a file saved mid-solo by 1.3 still holds the old pointers as ID properties after the RNA properties are gone (`solo.get("light")` / `solo.get("group")` returns the Object/Collection). A persistent `load_post` handler, `migrate_solo_targets`, moves them into `targets` and deletes the old keys. Fixtures `tests/fixtures/solo_light_1_3.blend` and `solo_group_1_3.blend` were saved by the pre-change add-on on Blender 4.2.23 (so both 4.2 and 5.2 open them). `tests/test_solo_targets.py` loads them and checks the migrated target, the label, and that `exit_solo` restores every light.

## v6 task 09: Additive solo
- `solo_light` and `solo_group` have an `extend` property (`SKIP_SAVE`). `invoke` sets it on Shift+click, and the menu's Add to Solo sets it directly. Both call `toggle_solo(solo, view_layer, id, extend)` in `lights.py` (`toggle_solo_light`/`toggle_solo_group` are thin wrappers).
- Rules: plain click solos only the clicked item, replacing any others, or ends solo if it is the only target. Extend adds the item, or removes it if soloed, and removing the last target ends solo (`unsolo`). Lights and groups mix. After every change, the shown lights are the union (each soloed light plus `all_objects` of each soloed group), and the unhidden collections are the union of their paths (`_collection_paths`).
- Collections a solo has unhidden stay unhidden when a target is removed or replaced, until the solo ends (the existing switching rule, pinned by `test_mute_solo.py`). Lights are recomputed from the full list each time, and the snapshot is still taken once (new items are only added for lights and collections without one).
- The World stays exclusive: `solo_world` takes `extend` but ignores it (Shift+click works like a plain click), and a lamp or group click during a World solo leaves it first (`_leave_world_solo`), with or without extend.
- `solo_label` (Exit Solo's tooltip) lists the surviving targets' names, at most `SHARED_NAMES`, then "…". It says "deleted" only when none are left.
- The right-click menu has "Add to Solo" / "Remove from Solo" after Solo (`solo_light` with `extend=True`, for the clicked light only).

## v6 task 10: Mutes during solo
- `LIGHTHOUSE_PG_solo_object.muted`: `update_snapshot()` sets it on mute and clears it on unmute, along with the restore flags. Every Mute (the row, the Active Light panel, the right-click menu) goes through it.
- `_solo()` hides every light that is either outside the targets' union or has `muted` set. So adding, removing or replacing targets never re-shows a light muted during the solo, even one inside a soloed group.
- Un-solo is unchanged (it restores the snapshot flags, which already say muted). The snapshot items are cleared at un-solo, so a new solo starts with every `muted` flag cleared.

## v6 task 11: Load HDRI
- `hdri_target(world)` (`lights.py`) is the world's only Environment Texture node (from `environment_textures()`, top-level nodes only, linked anywhere or not), or None when it has none or several. `LIGHTHOUSE_OT_load_hdri` opens Blender's file browser (`fileselect_add`, `filter_image`) and sets `bpy.data.images.load(filepath, check_existing=True)` on that node. It never adds nodes (that's task 12). It cancels with a warning for a read-only world or when there isn't exactly one Environment Texture.
- The World panel's `draw_load_hdri()` draws "Load HDRI…" for any setup with exactly one Environment Texture: under Strength and Rotation for a simple setup, and under the "Custom world setup" note for a custom one (a Mix Shader with one texture still gets it). It's disabled for a read-only world.
- The previous image is left alone: it loses the node's user and Blender drops it when the file is saved with no users left. No fake user, no removal.
- Task 12, Background-only worlds: `hdri_addable(setup)` is true for a `SIMPLE` setup with no Environment Texture and an unlinked Background Color. There `load_hdri` loads the image and `add_environment()` adds an Environment Texture with it, linked to the Background's Color and placed 300 px to its left. Rotation is left alone. A Background whose Color is linked to some other node (an RGB node, a ramp) gets no button and the operator cancels (pinned by a test), since adding a node would cut the user's link. Custom setups with no Environment Texture still get no button.
- Verify result (task 12): after the added node, `world_setup()` is `SIMPLE` with `environment` set to it and `rotation == 'ADDABLE'`, so the panel shows Strength, Add Rotation and Load HDRI. `add_world_rotation` then gives `'MAPPING'`. `world_mute_node()` is still the Background, so World mute and World solo act on it as before. All of this is covered in `tests/test_load_hdri.py`.
