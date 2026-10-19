# Task progress

## TICKET-01: Own lights before sub-collections
- `_collection_entries()` now lists a collection's own lights before its sub-collections, so Scene Collection lights come first.
- Updated the `list_entries()` docstring and added a v3 task 01 entry to ARCHITECTURE.md.
- `make test`: all 103 pass. The 5 failing ordering tests are fixed and the tests themselves were not edited. The manual GUI check has not been done.

## TICKET-02: Presets that stay correct
- The dropdown keeps its preset (enum numbers are key CRCs). Deleting the shown preset falls back to Candle, and an empty value no longer breaks the panel draw.
- Library and system-override lights are skipped and reported as read-only. Save refuses to overwrite without `overwrite`, catching sanitized-name collisions, and selects what it saved.
- User presets are cached by folder mtime and cleared on save and delete. 6 new tests, `make test`: 109 pass. Not done yet: the manual GUI checks (empty-value draw guard, whether the dialog warning updates live).

## TICKET-03: Bulk actions say when there is nothing to do
- Scale, EV step, Apply preset and Move selected here now warn `No lights selected` / `No lights in the view layer` and return `CANCELLED` (no undo step) when nothing is in scope. They also cancel with the summary as a warning when every light in scope was skipped. `scale_lights(factor=1.0)` cancels silently.
- `tests/blender_runner.py`: `info_reports()` became `reports(output, level="Info")` (Blender prints `Warning: ` in background mode). Added 9 tests in `tests/test_empty_scope.py` and an ARCHITECTURE.md entry.
- `make test`: 118 pass. No existing test relied on `FINISHED` for an empty scope. Not done yet: the manual GUI check (status bar warnings, Ctrl+Z after a cancelled press).

## TICKET-04: Empty state and expand/collapse all
- `empty_message()` explains an empty Lights panel: either no lights in the view layer, or none matching the filters (with a **Clear Filters** button, `lighthouse.clear_filters`). Lights inside collapsed groups do not count as empty.
- `lighthouse.collapse_all_groups` is replaced by `lighthouse.toggle_all_groups`, built on `listed_groups()`. It expands everything when all groups are collapsed and collapses everything otherwise, and the header icon flips between `FULLSCREEN_ENTER` and `FULLSCREEN_EXIT`. Updated the smoke script, acceptance.md and ARCHITECTURE.md.
- `make test`: 122 pass. Added 3 tests in `tests/test_empty_list.py`, and 2 toggle-all tests replace the collapse-all test. Not done yet: the manual GUI check and a re-run of the engine smoke.

## TICKET-05: Solo you can always leave, and that keeps your changes
- While solo is on, the panel draws `Exit Solo (<name or "deleted">)` (`lighthouse.exit_solo`, `UNDO`, polls on `solo.active`). It calls the now public `lights.unsolo()`, and `lights.solo_label()` supplies the name.
- `mute_light` and `hide_group` call `lights.update_snapshot()`, which writes the new flags into the matching snapshot item while solo is on, so un-solo keeps changes made during solo. Collections with no snapshot item are left alone. Updated ARCHITECTURE.md (known limits marked fixed, new entry) and added an `exit_solo` step to the smoke script.
- 5 new tests in `tests/test_exit_solo.py`. `make test`: 126 pass, plus 1 failure in `test_empty_list` caused by the uncommitted "filter" wording edit, which passes without that edit. Not done yet: the manual GUI check and an engine smoke re-run.

## TICKET-06: Operators find the exact light or collection
- The new `id_key()`, `find_object()` and `find_collection()` look up by `(name, library)`. The 9 row and header operators gain a hidden `library` property (default `""`), and the panel fills both properties through `target(op, id)`. On 5.2 the tuple keys work as long as local IDs use `None` (`""` finds nothing). 4.2 was not checked.
- When `library=""` finds no local ID, the lookup falls back to the name alone, so name-only calls such as `move_to_group(name="Linked")` still reach linked data. Added an ARCHITECTURE.md entry.
- 6 new tests in `tests/test_library_lookup.py`. `make test`: 132 pass, plus the `test_empty_list` failure that was already there before this ticket (it fails on the untouched tree too). The engine smoke run passes. Not done yet: the manual GUI check.

## TICKET-07: Tidy-up, and prove the Blender 4.2 minimum
- The tests run `$BLENDER` (`make test BLENDER=...`). `blender_version()`, `needs_blender()`, `NEWER_DETAILS` and the prelude's `EEVEE` make the suite version-aware. On 4.2 it skips only the 5 tests that set `exposure` or `use_temperature`. The add-on needed no 4.2 fixes.
- Removed `RowState.shared` and its test. `__init__.py` imports are tidied, the version is now 1.2.0, and `dist/lighthouse-1.2.0.zip` is built. The README has venv setup, `BLENDER=` and "Tested on 4.2.23 LTS and 5.2.2 LTS". acceptance.md and ARCHITECTURE.md have 4.2 entries.
- 5.2.2: 133 pass. 4.2.23: 128 pass, 5 skip. On both, `test_empty_list` still fails, as before this ticket ("filter"/"filters" wording). The smoke run and validate pass on both. Not done yet: the manual GUI check on 4.2.

# v4 tickets (tasks/ rewritten in 13f76ff)

## v4 TICKET-01: Foldable lights row
- A collection with its own lights and at least one listed sub-collection now shows a foldable `Lights (N)` row (`LightsEntry`, `is_lights_folded()`, `Collection.lighthouse_lights_collapsed`, `lighthouse.toggle_lights_row`, `draw_lights_row()`). Leaf collections and Scene Collection lights are unchanged.
- Folding hides only the drawn lights. Counts, `group_lights()` and `listed_groups()` still include them, and `select_light`'s `RANGE` now keeps only `LightEntry` rows. Added the smoke step and an ARCHITECTURE.md entry.
- 6 new tests (`tests/test_lights_row.py`, `tests/test_grouped_lights.py`), and 1 ordering test now expects the row. The `test_empty_list` wording test was fixed first to match `filter(s)`, in its own commit. `make test`: 140 pass. The engine smoke run passes. Not done yet: the manual GUI check.

## v4 TICKET-02: Expand All opens lights rows
- When `toggle_all_groups` expands (every listed collection collapsed), it also unfolds every listed collection's lights row. Collapse leaves lights rows alone. The tooltip now mentions lights rows.
- The "all collapsed?" check (action and header icon) still reads only `lighthouse_collapsed`. A test pins that folded rows alone don't make the next press expand. Added an ARCHITECTURE.md entry.
- 3 new tests in `tests/test_lights_row.py`. `make test`: 143 pass. Not done yet: the manual GUI check (the header icon doesn't change when a lights row is folded, since the draw code can't run headless).

## v4 TICKET-03: Active collection as the target folder
- New `lighthouse.set_active_collection` (`REGISTER`, `UNDO`, like the Outliner's `item_activate`) sets `view_layer.active_layer_collection`. It cancels for unknown or excluded collections and never changes the selection. `find_layer_collection()` is now public.
- A group's `Name (N)` label is now this button, pressed when its collection is active, so `+` and Shift+A add there. Library collections can be made active, and `+` then refuses as before. Added the smoke step and an ARCHITECTURE.md entry.
- 4 new tests in `tests/test_active_collection.py`. `make test`: 147 pass. The engine smoke run passes. Not done yet: the manual GUI check (pressed state, sync with the Outliner, Shift+A).

## v4 TICKET-04: Scene Collection row
- The grouped list now starts with `SceneEntry`: a `Scene Collection` header with a fold for its own lights (blank when it has none), its name as the `set_active_collection` button, and Move here aligned with the other headers (blank slots for Select, Hide and Solo). Top-level collections stay at depth 0.
- `name=""` targets the master collection in `toggle_lights_row`, `move_to_group` and `set_active_collection`. Expand All unfolds it, and its fold is saved with the scene. Updated 10 existing list expectations for the new header, and added the smoke steps and an ARCHITECTURE.md entry.
- 6 new tests. `make test`: 153 pass. The engine smoke run passes, and a stub-layout draw check ran clean (not committed). Open questions took their defaults (no Select, no count). Not done yet: the manual GUI check.

## v4 TICKET-05: Show empty collections
- New `show_empty` setting (WindowManager, default on, drawn as an `OUTLINER_COLLECTION` toggle, kept by `clear_filters`). With it on, `list_entries`/`listed_groups` list every non-excluded collection, empty ones with `(0)`, and empty sub-collections count for the lights row rule. The panel, `RANGE` select and toggle-all pass it, and the defaults keep the old list.
- `GroupEntry.foldable`: `draw_group()` draws a `BLANK1` instead of the triangle when nothing is under the collection, and greys out Select and Solo at `(0)`. The new `all_collapsed()` (using `listed_groups(foldable_only=True)`) leaves triangle-less collections out of the toggle-all check and the header icon. The older toggle-all tests in `test_group_actions.py` and `test_lights_row.py` now set `show_empty = False` (the factory scene's empty `Collection` would otherwise join in). Added an ARCHITECTURE.md entry.
- 7 new tests in `tests/test_show_empty.py`. `make test`: 160 pass. Engine smoke run passes on 4.2.23. On system 5.2.2 it can't install right now (`cattrs` missing from Blender's Python). Not done yet: the manual GUI check (alignment, greyed-out Select/Solo).

## v4 TICKET-06: Empty-state message above the collection tree
- New `lights.tree_under_message(grouped, name_filter, show_empty)`. When no lights match, the panel draws the message (plus Clear Filters for a filter cause) and then the `(0)` collection tree, but only when grouped, not searching and `show_empty` is on. Otherwise it draws the message and returns, as before.
- The message wording is unchanged. Updated the v3 task 04 note in ARCHITECTURE.md and added a v4 task 06 entry.
- 3 new tests in `tests/test_show_empty.py` (a view layer with no lights, a type filter matching nothing, the helper's truth table). `make test`: 163 pass. Engine smoke run passes on 4.2.23 (system 5.2.2 still can't install: `cattrs`). Not done yet: the manual GUI check.

## v4 TICKET-07: New Collection button
- New `lighthouse.new_collection` (`REGISTER`, `UNDO`, `COLLECTION_NEW` button next to `+`). It creates `Collection` inside the active collection (the Scene Collection when the master is active), makes it active and leaves the selection alone. It refuses a library parent with an `ERROR` before creating anything, like `add_light`.
- Folding is left alone (the open question's default). With `show_empty` on, the new collection shows up right away as `(0)`. Added the smoke step and an ARCHITECTURE.md entry.
- 5 new tests in `tests/test_new_collection.py`. `make test`: 168 pass. Engine smoke run passes on 4.2.23 (system 5.2.2 still can't install: `cattrs`). Not done yet: the manual GUI check (New Collection then `+`, one Ctrl+Z removes it).

## v4 TICKET-08: Reveal active light
- New `lights.reveal(view_layer, obj)` expands every collection that holds the light, plus its ancestors, and unfolds their lights rows (or the Scene Collection fold). Siblings stay collapsed, and a light in two collections is revealed in both. New `lighthouse.reveal_active_light` (`INTERNAL`, `VIEW_ZOOM` header button next to toggle-all, `poll()` needs an active light).
- `add_light` calls `reveal()` after linking, so a light added into a folded collection is visible. There is no selection handler and filters are left alone. Added the smoke step and an ARCHITECTURE.md entry.
- 6 new tests in `tests/test_reveal.py`. `make test`: 176 pass. Engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (button greyed out without an active light, reveal after a viewport click).

## v4 TICKET-09: Intensity scope starts as Selected
- `LIGHTHOUSE_PG_settings.scale_scope` now defaults to `SELECTED`. `SCOPE_ITEMS` order and the operators' own `scope` property are unchanged.
- The setting stays on the WindowManager, so a .blend saved with All still opens with Selected. Added an ARCHITECTURE.md entry.
- 2 new tests in `tests/test_scope_default.py` (fresh session, save then reopen). `make test`: 178 pass. Not done yet: the manual GUI check (panel opens with Selected pressed).

## v4 TICKET-10: Presets become plain files
- `BUILTIN_PRESETS` is now `DEFAULT_PRESETS`. `restore_default_presets()` and `seed_default_presets()` (with a `.defaults_installed` marker) write them as JSON once, seeded in `presets_folder()` so a Save before the first draw sees them too. A default you delete stays deleted.
- The dropdown is sorted by label with no icons. Save has no reserved names (`Candle` goes through exists/Overwrite). Delete offers every preset and selects the next, or the new last, or nothing. The `CANDLE` fallback and the built-in checks are gone. README and ARCHITECTURE.md are updated (old notes marked superseded, item 17 cost documented).
- 5 new tests in `tests/test_default_presets.py`. The preset, Kelvin, empty-scope and user-preset tests and the smoke script moved to `USER:<label>` keys. `make test`: 183 pass. Engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (no icons, empty dropdown with Apply greyed out).

## v4 TICKET-11: Restore default presets
- New `lighthouse.restore_default_presets` (no confirm, no `UNDO`), a Restore button next to Save and Delete. It calls `restore_default_presets(presets_folder())`, clears the cache and reports "Restored Candle, …" or "Every default preset is already there".
- It only writes missing defaults, so edited defaults and your own presets are untouched. The selection is left alone (the open question's default). Added the smoke step and an ARCHITECTURE.md entry.
- 3 new tests in `tests/test_restore_presets.py`. `make test`: 186 pass. Engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (button placement, restored presets show up in the dropdown right away).

## v4 TICKET-12: Restore moves to Preferences
- The Restore button left the presets row, which now has only Save and Delete. It is in Edit > Preferences > Add-ons > Lighthouse as "Restore Default Presets", with a one-line hint. The operator is unchanged.
- 3 new tests in `tests/test_restore_in_preferences.py` (preferences registered, preferences draw Restore and the hint, the panel draws Apply/Save/Delete only) using a recording fake layout. Not done yet: the manual GUI check of the Preferences panel.

# v5 tickets

## v5 TICKET-01: Right-click a collection to add there
- `draw_group_menu` is prepended to `UI_MT_button_context_menu`. When the button under the cursor is a header's name button (`set_active_collection`: group headers and the Scene Collection row), it draws New Light ▸ (`LIGHTHOUSE_MT_new_light`, target passed by `context_pointer_set("lighthouse_collection", …)`), New Collection and a separator, disabled on read-only collections. Other buttons get nothing.
- `add_light` and `new_collection` gain hidden `SKIP_SAVE` `name`/`library`/`use_active` (default on, so the header buttons are unchanged). A target (`""` = Scene Collection) is found by `target_layer_collection()`. A missing target cancels and a read-only one raises as before. `add_light` makes its target active. `new_collection`'s dialog field is now `new_name`. `Recorder` moved to `blender_runner.RECORDER` (menus, separators, pointers, `enabled`, operator props, `FakeContext`). Added the smoke steps and an ARCHITECTURE.md entry.
- 11 new tests in `tests/test_group_menu.py`. `test_packaging` was fixed first, in its own commit, to read the version from the manifest (it broke on the 1.2.1 bump). `make test`: 200 pass. Engine smoke run and the new tests pass on 4.2.23. Not done yet: the manual GUI check (`button_operator` in the real right-click menu, the pointer reaching the submenu, greyed-out library entries).

## v5 TICKET-02: One `+` in the header
- New `LIGHTHOUSE_MT_new` (New Light ▸ with no target, so it adds to the active collection, and New Collection with `use_active`), greyed out when the active collection is read-only. The header draws it as `row.menu(..., icon='ADD')` in place of the `+` enum menu and the New Collection button, in grouped, flat and search modes.
- The header row is down from 8 to 7 entries, which frees a slot for task 03. The Recorder's `menu()` now records the icon (the two group-menu expectations gained `"LIGHT"`). Added an ARCHITECTURE.md entry and updated AC 20 in acceptance.md.
- 4 new tests in `tests/test_header_new_menu.py`. `make test`: 204 pass. Not done yet: the manual GUI check (`+` ▸ New Light ▸ Point, New Collection dialog, flat/search/type filter, one Ctrl+Z each) and an engine smoke re-run.

## v5 TICKET-03: Color/Kelvin toggle for new lights
- New pure `new_light_mode()`, `toggled_mode()` (returns `FOLLOW` when a flip lands on the default) and `supports_temperature()` in `lights.py`. New `Scene.lighthouse_new_lights` (`FOLLOW`/`COLOR`/`KELVIN`, saved with the file), `default_new_light_mode()` (always `COLOR` until task 04) and `lighthouse.toggle_new_light_mode` (`UNDO`, with a tooltip such as "New lights start in Kelvin (this file)").
- The header draws the toggle right after `+` on 5.0+ (pressed, `LIGHT_SUN` in Kelvin, `COLOR` otherwise), and nothing before 5.0. In Kelvin, `add_light` sets `use_temperature`, the RNA default temperature and white. Shift+A and duplicates are untouched (no depsgraph handler, see ARCHITECTURE.md). Added smoke steps. Ticket 02's header count now expects 8 on 5.0+ (7 before).
- 8 new tests in `tests/test_new_light_mode.py`. `make test`: 5.2.2 211 pass, 1 skip; 4.2.23 203 pass, 9 skip. The engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (slot alignment, tooltip in both modes, Kelvin field on a new light's row).

## v5 TICKET-04: Color/Kelvin default in Preferences
- New `LIGHTHOUSE_AP_preferences.new_light_mode` (`COLOR`/`KELVIN`, default `COLOR`), drawn expanded as "New lights start in" above Restore, only on 5.0+. `default_new_light_mode()` reads it when installed and falls back to `COLOR` otherwise. The tooltip says "(Preferences default)" or "(this file)".
- `toggled_mode()` and the scene property are unchanged: a `FOLLOW` file follows later default changes, and a pinned file keeps its value. The README mentions the toggle, the Preferences default, `+` as a menu and the right-click menu. Added an ARCHITECTURE.md entry with the pin/un-pin rule.
- 5 new tests in `tests/test_new_light_default.py` (`run_installed`). The restart test loads prefs with `wm.read_userpref()` because the runs use `--factory-startup`. It is skipped on 4.2, where that call crashes Blender headless. `make test`: 5.2.2 216 pass, 1 skip; 4.2.23 204 pass, 13 skip. Not done yet: the manual GUI check (changing the default flips an untouched file's toggle, a pinned file keeps its value).

## v5 TICKET-05: World panel with Strength
- New `WorldSetup` and `world_setup(scene)` in `lights.py`. The world is `SIMPLE` only when World Output > Surface reaches a Background whose Strength isn't linked. A Mix Shader, a node group, a linked Strength, nothing on Surface or `use_nodes` off give `CUSTOM` (the open questions took their defaults), and no world gives `NONE`. `environment` is an Environment Texture on the Background's Color.
- New `LIGHTHOUSE_PT_world` draws Strength (disabled on a read-only world), the custom label or the no-world label. The panels now register as Lights, World, Intensity, Presets. Added a smoke step and an ARCHITECTURE.md entry.
- 9 new tests in `tests/test_world_panel.py` (including item 18: scope All leaves the World strength alone), and `test_panels.py` now has the 4-panel list plus an order test. `make test`: 5.2.2 226 pass, 1 skip; 4.2.23 214 pass, 13 skip. The engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (panel order in a fresh layout, viewport update, Ctrl+Z).

## v5 TICKET-06: World rotation
- `WorldSetup` gains `mapping` and `rotation` (`MAPPING`, `ADDABLE`, `CUSTOM` or `None`). The new `add_world_rotation(node_tree, environment)` inserts Texture Coordinate (Generated) → Mapping → Vector, placed to the left of the texture.
- New `lighthouse.add_world_rotation` (`REGISTER`, `UNDO`) cancels unless the world is `SIMPLE` and `ADDABLE`, and refuses a read-only world. The World panel draws Rotation Z (`index=2`) for `MAPPING`, Add Rotation for `ADDABLE`, and nothing otherwise. Added a smoke step and an ARCHITECTURE.md entry.
- 8 new tests in `tests/test_world_rotation.py`. `make test`: 5.2.2 234 pass, 1 skip; 4.2.23 222 pass, 13 skip. The engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (HDRI turns, node placement, one Ctrl+Z removes both nodes).

## v5 TICKET-07: World mute
- Verify step (render probe on 4.2.23 and 5.2.2, Cycles and EEVEE): a muted Background or node group renders black, but a muted Mix Shader passes its first shader through. So the fallback applies: `world_mute_node()` returns the Background for `SIMPLE` only, and Mute is greyed out for `CUSTOM`. The result is recorded in ARCHITECTURE.md and kept as a Cycles render test.
- New `world_muted()` and `lighthouse.mute_world` (`REGISTER`, `UNDO`, flips `node.mute`, cancels without a node or on a read-only world). The panel gains a top row with the world name and Mute (`depress`, `HIDE_ON`/`HIDE_OFF`), and Strength/Rotation are drawn inactive while muted. The Recorder now marks `"pressed"` and `"inactive"`, and the 5 earlier World panel expectations gained the header row.
- 6 new tests in `tests/test_world_mute.py` (including save/reopen). `make test`: 5.2.2 240 pass, 1 skip; 4.2.23 228 pass, 13 skip. The engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (viewport darkens in Rendered, red node, Ctrl+Z).

## v5 TICKET-08: World in solo
- New `lighthouse.solo_world` (`REGISTER`, `UNDO`, `toggle_solo_world()`): it hides every light, snapshots the World's mute node and un-mutes it. With no world or a `CUSTOM` setup it only hides the lights. `LIGHTHOUSE_PG_solo` gains `world_soloed` plus the World snapshot (`world_saved`, `world`, `world_node`, `world_muted`). The World panel's top row draws Solo after Mute.
- Lamp and group solo never touch the World. Switching from World solo to a lamp or group re-mutes the World right away. `unsolo()` restores the node when it still exists (the lights are restored either way). `mute_world` goes through `update_snapshot()`, so a mute during World solo survives un-solo. `solo_label()` gives "World". Added ARCHITECTURE.md notes and smoke steps.
- 9 new tests in `tests/test_world_solo.py`, and the 5 exact World-panel draw expectations gained Solo. `make test`: 5.2.2 249 pass, 1 skip; 4.2.23 237 pass, 13 skip. The engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (the HDRI stays lit on a lamp solo, only the HDRI lights a World solo, Exit Solo re-mutes the World).

## v5 TICKET-09: Light linking receivers
- Verify step: collections selected in the Outliner can't be read from the sidebar (`selected_ids` needs an Outliner area under `temp_override`, and there is none headless). So the fallback applies: Link Selected links objects only, and the limit is noted in the README and ARCHITECTURE.md.
- New `Receiver`, `receivers()`, `link_receivers()` and `remove_receiver()` in `lights.py` (`collection_objects`/`collection_children` take only indices, so states are paired by position). New `lighthouse.link_receivers` (warns "No objects selected", refuses read-only) and `lighthouse.remove_receiver`. `draw_linking()` ends the details with the Light Linking label, Link Selected and one icon/name/`×` row per receiver. Added smoke steps.
- 6 new tests in `tests/test_light_linking.py`. `make test`: 5.2.2 255 pass, 1 skip; 4.2.23 243 pass, 13 skip. The engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (Cycles Rendered viewport, `×`, Ctrl+Z).

## v5 TICKET-10: Exclude, Clear and sharing
- Exclude Selected is `link_receivers(state='EXCLUDE')`, so listed items only change state. `Receiver` gains `link`, and each row draws its `link_state` directly (expanded Include/Exclude, undo for free).
- New `clear_receivers()` (keeps the collection assigned, the open question's default), `lighthouse.clear_receivers` (greyed out when the list is empty), `receiver_users()` and `shared_label()` ("Shared with Key, Rim (3 lights)", at most 3 names then "…"), drawn with `INFO` under the buttons. Added smoke steps, README and an ARCHITECTURE.md entry.
- 5 new tests, and the task 09 draw test was rewritten for the new section (`tests/test_light_linking.py`, 11 now). `make test`: 5.2.2 260 pass, 1 skip; 4.2.23 248 pass, 13 skip. The engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (Cycles exclude, both sharing lights show the label).

## v5 TICKET-11: Light linking icon on the row
- New `linking_tooltip()` ("Lights only 3 objects, excludes 1", singular wording, child collections named separately as the open question's default) and `linking_counts()` in `lights.py`.
- New `lighthouse.light_linking_info` (`INTERNAL`, tooltip from `description()`). Its click opens the details (Shift keeps others) and never closes them. `draw_light()` draws it as `LINKED` after ⓘ and before power, only when there are receivers. Added a smoke step and an ARCHITECTURE.md entry.
- 3 new tests in `tests/test_light_linking.py`. `make test`: 5.2.2 263 pass, 1 skip; 4.2.23 251 pass, 13 skip. The engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (columns don't shift, tooltip, click opens details).

## v5 TICKET-12: Light linking engine note
- Verify step (render probe): Cycles renders light linking on 4.2.23 and 5.2.2, EEVEE only on 5.2.2 (not 4.2's EEVEE Next), Workbench never. The table is in ARCHITECTURE.md, and the probe is kept as a ~1 s test. Versions in between weren't checked, so EEVEE counts from 5.0.
- New `light_linking_note(engine)` and `engine_name()` (a fixed name table, since the engine enum lists only some built-ins headless). `draw_linking()` draws the note with `INFO` under the section label, and the buttons stay enabled. Unknown engines get the note (the open question's default). README requirements updated.
- 3 new tests. The draw tests now set Cycles (4.2's factory engine is EEVEE). `make test`: 5.2.2 266 pass, 1 skip; 4.2.23 254 pass, 13 skip. The engine smoke run passes on 4.2.23. Not done yet: the manual GUI check (switch engines with details open).

## v5 TICKET-13: v5 release
- Version 1.3.0 (manifest). The README now describes four panels in order (Lights, World, Intensity, Presets): the `+` menu and right-click menu, the Color/Kelvin toggle and its Preferences default, the World panel (simple vs custom, Add Rotation, Mute, Solo), light linking with the engine table and the Outliner limit. tests/acceptance.md gains a v5 checklist with one manual check per task. Every v5 operator was already in the smoke script.
- Fixed `make install`: it now installs `dist/lighthouse-$(VERSION).zip`, since the old glob broke when an older zip was left in `dist/`. `make validate`, `make build` and a clean-profile `make install` pass. The engine smoke passes on 4.2.23. On system 5.2.2 neither install nor smoke can run (`bl_pkg` needs `cattrs`, so there is no `bl_ext`). Added a `## v5 release` ARCHITECTURE.md entry with the known limits.
- `make test`: 5.2.2 266 pass, 1 skip; 4.2.23 254 pass, 13 skip. Not done yet: the manual GUI acceptance pass on 5.2 and 4.2, and the 5.2.2 engine smoke (needs a Blender 5.2 build with a working extension system).

## v6 task 01: New light defaults (released as 1.3.1)
- `add_light` applies a `SHIFT_A_VALUES` table after `lights.new()`: Sun `energy` 1.0, Area `size`/`size_y` 1.0. Point and Spot have no entry. It runs before the Kelvin step, so both apply. ARCHITECTURE.md entry added.
- 3 new tests (`tests/test_new_light_values.py`). `make test`: 5.2.2 269 pass, 1 skip; 4.2.23 256 pass, 14 skip (the new Kelvin test is 5.0+). `make validate` passes on both, and `make build` gives `dist/lighthouse-1.3.1.zip`. Version 1.3.1 is in the manifest only (the README has no changelog).
- Not done yet: the manual GUI check (Area and Sun from Lighthouse vs Shift+A in the Light properties).

## v6 task 02: Benchmark
- New `make bench` runs `tests/bench_lights_panel.py`: 500 lights over 65 nested collections, grouped, 5 rows expanded, and the median of 9 `LIGHTHOUSE_PT_lights.draw()` passes on the suite's `Recorder` stub layout. It only prints. pytest doesn't collect it (270 tests collected, as before).
- **Baseline** (AMD Ryzen 9 9900X, 2026-10-17): **15.7 ms** on 5.2.2 (min 14.9), 14.7 ms on 4.2.23. That's already over the ~10 ms mark, so it's a candidate for caching to weigh at the 1.4.0 release (not built, per the ticket).
- `make test`: 5.2.2 269 pass, 1 skip (unchanged). ARCHITECTURE.md entry and the README's development section mention `make bench`.

## v6 task 03: Active Light panel
- Prefactor: `draw_light_controls()` and `draw_light_details()` now draw a row's controls and details on any layout. The list's `draw_light`/`draw_details` wrap them, and every existing row and details test passed unchanged.
- New `LIGHTHOUSE_PT_active_light`: the active light's controls and details (read-only disabled and muted dimmed via `row_state()`, as on rows), or "Select a light" with no `poll`. It registers last until task 04 (the `test_panels.py` list gained it). 3 new tests (`tests/test_active_light_panel.py`). `make test`: 5.2.2 272 pass, 1 skip; 4.2.23 259 pass, 14 skip.
- `make bench`: 16.1 ms (baseline 15.7 ms, noise). The smoke script doesn't draw panels, so it has no step for this. Not done yet: the manual GUI check (click between a mesh and lights; the panels below stay put; editing power in the panel changes the row).

## v6 task 04: Panel order
- `bl_order` sets Active Light → World → Intensity → Presets → Lights, and Presets is `DEFAULT_CLOSED` (Intensity stays open). In `tests/test_panels.py`, the registration-order test became a `bl_order` test, and a test pins the default-closed flags.
- Verify not settled: a scripted GUI check failed (4.2's `Region.active_panel_category` is read-only, so the tab can't be opened from Python). ARCHITECTURE.md records the expected result (saved layouts keep their order, since `bl_order` is only the default) and leaves it to the manual check.
- `make test`: 5.2.2 273 pass, 1 skip. Not done yet: the manual GUI check (fresh-file order and Presets closed; a 1.3.x file with dragged panels).

## v6 task 05: Light right-click menu
- New `draw_light_menu()` is prepended to `UI_MT_button_context_menu` for a light row's name button (`select_light`): Rename, Frame, Solo/Exit Solo, then a separator. A missing light or another button draws nothing. It's registered and removed alongside the group menu.
- New `LIGHTHOUSE_OT_rename_light` (a dialog that renames the object only, disabled and refused for library lights). Frame is `select_light` FRAME in exec context, and Solo is `solo_light`. 5 tests in `tests/test_light_menu.py`, plus a smoke step and an ARCHITECTURE.md entry.
- `make test` (5.2.2): 278 pass, 1 skip. Not done yet: the manual GUI check (entries above Blender's own; rename one light, frame another).

## v6 task 06: Delete and duplicate
- New `light_scope()` follows the Outliner rule (the selection when the clicked light is selected, otherwise only the clicked light). Labels show the count ("Delete 3 Lights"). Menu order: Rename, Frame, Duplicate, Duplicate Linked, Delete, Solo.
- New `delete_lights` operator (object only, no confirmation; shared data stays, and solo still exits cleanly) and `duplicate_lights` operator (`linked` shares the data; copies go into the same collections, become the selection with the clicked light's copy active, and are shown during solo). Read-only lights are skipped and reported, and the operator cancels when all are read-only.
- 8 tests in `tests/test_delete_duplicate.py`, the menu test updated, plus a smoke step and an ARCHITECTURE.md entry. `make test` (5.2.2): 286 pass, 1 skip. Not done yet: the manual GUI check (Delete 3, then Ctrl+Z; the ⓘ tooltip after Duplicate Linked).

## v6 task 07: Mute and Apply Preset ▸ in the light menu
- New `mute_lights` operator (follows the clicked light over `light_scope()`, goes through `update_snapshot()`, skips read-only lights) and `LIGHTHOUSE_MT_apply_preset` submenu. `apply_preset` gained hidden `SKIP_SAVE` `name`/`library` to target the menu's lights, while the Presets panel still uses the selection.
- **Differs from the ticket:** Blender deselects a light when `hide_viewport` is set, so muted lights are never selected. "Unmute 3 Lights" and "two muted + one unmuted selected" can't happen. The tests cover what can happen instead (a selection's Mute mutes all; Unmute on a muted light acts on that light alone). The ARCHITECTURE.md entry records this.
- 7 tests in `tests/test_menu_mute_preset.py`, plus a smoke step. `make test` (5.2.2): 293 pass, 1 skip. Not done yet: the manual GUI check.

## v6 task 08: Solo targets prefactor
- `LIGHTHOUSE_PG_solo.targets` (items with an `object` or `collection` pointer) replaces `light`/`group`. `lights.py` uses the new `is_solo_target()` / `set_solo_target()`. Behaviour is unchanged, and every existing solo test passes unchanged (a read-only Python `solo.light` accessor keeps `test_world_solo` working).
- Verify: the 1.3 pointers still load as ID properties, so a persistent `load_post` handler (`migrate_solo_targets`) moves them into `targets`. There are two 4.2.23-saved mid-solo fixtures in `tests/fixtures/`, and a test confirms the migrated target, the label and a clean `exit_solo`.
- 4 tests in `tests/test_solo_targets.py`, plus an ARCHITECTURE.md entry. `make test`: 5.2.2 297 pass, 1 skip. Before the accessor fix, 4.2.23 had 1 fail, the same one as 5.2. After it, the solo tests pass on 4.2.

## v6 task 09: Additive solo
- `solo_light`/`solo_group` gained `extend` (`SKIP_SAVE`, set by Shift+click in `invoke`). The new `toggle_solo()` handles add/remove (removing the last target ends solo), a plain click replacing several targets, and the union of lights shown and collections unhidden. The World stays exclusive (`solo_world` ignores `extend`), and Exit Solo lists up to 3 names then "…".
- The menu gained "Add to Solo" / "Remove from Solo". Collections unhidden by a removed target stay unhidden until the solo ends: an existing test pins that switching rule, so the re-hide I tried first was reverted.
- 7 tests in `tests/test_additive_solo.py`, plus a smoke step and an ARCHITECTURE.md entry. `make test`: 5.2.2 304 pass, 1 skip; 4.2.23 291 pass, 14 skip. Not done yet: the manual GUI check.
