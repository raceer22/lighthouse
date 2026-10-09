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
