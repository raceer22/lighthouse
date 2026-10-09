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
- If the soloed light is deleted, no row shows as soloed. Solo any light, then press it again to restore.
- Mute during solo changes the flags, but un-solo overwrites them with the snapshot.

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

**Components**
- `lighthouse/presets.py`: `preset_from_light(light, label)` reads power, color and soft size back as a radius (area `size / 2`, sun `angle`, otherwise `shadow_soft_size`). A sun gives a sun-only preset, and any other type gives a point/spot/area preset. `save_user_preset()` writes `<label>.json` (characters outside `\w`, `-` and space become `_`). `user_presets(folder)` reads every `*.json`, keyed `USER:<file stem>` and sorted by label, and prints `Lighthouse: Skipped user preset <file>: …` for files that aren't valid JSON or are missing fields. `delete_user_preset()` removes the file.
- `lighthouse/__init__.py`: `presets_folder()` is `bpy.utils.extension_path_user(__package__, create=True)`. The `preset` enums on the settings and on `apply_preset` are dynamic (`preset_items`): built-ins first, then user presets with the `USER` icon. `LIGHTHOUSE_OT_save_preset` (poll: active object is a light, invoke opens a name dialog) refuses empty names and built-in labels in any case. Saving an existing user name overwrites it. `LIGHTHOUSE_OT_delete_preset` (confirm on invoke) only lists user presets, so a built-in can't be passed. The Presets row gains `+`, plus `-` when a user preset is chosen.
- `tests/blender_runner.py`: `run_installed(snippet, user_dir)` symlinks the package into `user_dir/extensions/user_default/`, sets `BLENDER_USER_RESOURCES=user_dir` and enables `bl_ext.user_default.lighthouse`. Calls that share `user_dir` act like restarts of one install. `preset_items()` in its prelude calls the dropdown's items callback.

**Data flow**
User presets are read from disk every time the dropdown or `apply_preset` needs them. Nothing is cached, so a preset saved in another Blender instance shows up on the next redraw. They live outside the .blend file and aren't part of undo.

**Blender API quirks**
- `extension_path_user()` raises `ValueError` unless the package name is `bl_ext.<repo>.<id>`. That's why every preset test (task 09's too) runs through `run_installed` instead of `import lighthouse`.
- Blender doesn't keep the strings returned by a dynamic enum `items` callback alive, so the callbacks fill module-level lists.
- Dynamic enum items are not exposed through `bl_rna...enum_items` (it returns `[]`).
- A preset enum is stored as its item number, so adding or deleting a user preset can shift which entry the dropdown shows.
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
- With no `bl_parent_id` and no `bl_order`, registration order is the default panel order. Blender stores each panel's open/closed flag and drag position in the screen layout, so both are saved with the .blend file without any addon code.
- `draw_header()` runs even while the panel is collapsed, which is what lets presets be applied from a collapsed Presets panel. Drawing still can't run in `--background`, so the header and layout are checked by hand.
- Passing a float to an `IntProperty` operator argument raises `TypeError` ("expected an int type, not float"). A `FloatProperty` accepts ints, so old `steps=1` callers keep working.
- A `FloatProperty` with no `soft_max` gets `soft_max == hard_max` (FLT_MAX when no `max` is set), so dragging the field isn't capped. Dropping `slider=True` removes the slider bar.

## v2 task 02: lights grouped by collection

**Components**
- `lighthouse/lights.py`: `list_entries(view_layer, name_filter, type_filter, grouped)` returns the rows the Lights panel draws, in order. They are `GroupEntry(collection, depth, count)` and `LightEntry(obj, depth, other_collections)` NamedTuples. In grouped mode, `_collection_entries()` walks `view_layer.layer_collection` recursively. It skips `exclude`d layer collections and keeps a collection only if its subtree holds a listed light. Each group lists its sub-collections in outliner order, then its own lights sorted by name ignoring case. Scene Collection lights come last at depth 0 with no header. `count` is the size of the set of listed lights in the subtree, so a light in two sub-collections counts once. `other_collections` is how many other entries the same object got. In flat mode (`grouped` off or a non-empty search) the result is `listed_lights()` at depth 0.
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
  - `toggle_group` and `collapse_all_groups` have `bl_options = {'INTERNAL'}`, with no `UNDO`. Collapse all sets the flag on every collection in `view_layer.layer_collection.collection.children_recursive`.
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
