# Acceptance pass: PRD v2 on Blender 5.2.2 LTS

Walks PRD-v2 acceptance criteria 1–21. Each criterion lists its automated evidence (pytest, headless Blender) and any check that needs the GUI. The v1 criteria (PRD.md 1–14) are still covered by the same suite.

- **Automated**: `make test` → 102 passed (2026-10-09). `make validate` and `make build` pass (`dist/lighthouse-0.2.0.zip`).
- **Engine smoke**: `tests/smoke_engines.py` runs every operator on point, sun, spot and area lights in a sub-collection under Cycles, then EEVEE, against the zip installed in a clean profile. It covers `add_light`, every `select_light` action, mute and solo, `toggle_details`, `toggle_group`, `toggle_all_groups`, `clear_filters`, `select_group` (with and without extend), `move_to_group`, `hide_group`, `solo_group`, scale, ±1, ±½ and ±¼ EV, apply, save and delete preset, and the row color slot and details with temperature off and on. Run 2026-10-09: `SMOKE ok CYCLES`, `SMOKE ok BLENDER_EEVEE`, with no Lighthouse warnings or errors.
- **Blender 4.2** (v3 task 07, 2026-10-10, portable `blender-4.2.23-linux-x64`):
  - 5.2.2: `make test` → `1 failed, 133 passed`. The failure is `test_empty_message_names_why_the_list_is_empty` ("filter" vs "filters" wording), which also failed before task 07. Smoke: `SMOKE ok CYCLES`, `SMOKE ok BLENDER_EEVEE`.
  - 4.2.23: `make test BLENDER=~/blender-versions/blender-4.2.23-linux-x64/blender` → `1 failed, 128 passed, 5 skipped`, with the same failure. The skips test `Light.exposure` (4.4+) or `Light.use_temperature` (5.0+). Smoke: `SMOKE ok CYCLES`, `SMOKE ok BLENDER_EEVEE_NEXT`.
  - `make validate` passes on both, and `./build.sh` writes `dist/lighthouse-1.2.0.zip`. Not yet done: the manual GUI pass on 4.2.
- **Manual (GUI)**: the panel can't be drawn, modifier clicks can't be sent and undo can't run in `--background`. Those items are ticked only after someone checks them by hand in Blender 5.2.2.

Known environment noise (Fedora's package, unrelated to Lighthouse): an OpenColorIO 2.5 config error on launch, and a `bl_pkg` register traceback (`No module named 'cattrs'`) when a user profile is set.

## Clean-profile install and smoke

```sh
./build.sh
export BLENDER_USER_RESOURCES=$(mktemp -d)
blender --command extension install-file -r user_default -e dist/lighthouse-0.2.0.zip
blender -b --python-exit-code 1 --python tests/smoke_engines.py
# on another version: BLENDER=/path/to/blender-4.2 and run the same with $BLENDER
```

Run 2026-10-09: `STATUS Installed "lighthouse"`, exit code 0, both engines OK.

## Criteria

| AC | Criterion | Automated evidence | Result |
|----|-----------|--------------------|--------|
| 1 | Intensity, Presets and Lights are separate panels; presets work from the collapsed header | `test_intensity_presets_and_lights_are_top_level_panels_in_the_lights_tab`, `test_presets_panel_draws_its_header` | ✅ Pass (registration); collapse/reorder: manual ☐ |
| 2 | Factor has no slider, defaults to 1.0; six EV buttons multiply by `2 ** steps` | `test_each_ev_button_multiplies_power_by_two_to_the_steps`, `test_plus_quarter_ev_raises_a_100_w_light_to_about_118_92_w`, `test_quarter_ev_step_scales_keyframes`, `test_ev_steps_never_change_a_lights_own_exposure` | ✅ Pass (math); field look: manual ☐ |
| 3 | Grouped view nests lights as in the outliner | `test_collections_on_the_path_to_a_light_are_kept_as_nested_groups`, `test_collections_without_lights_are_left_out_and_scene_collection_lights_have_no_header`, `test_excluded_collection_has_no_header_…`, `test_indentation_stops_growing_after_three_levels` | ✅ Pass |
| 4 | Search flattens the list; clearing restores the mode | `test_search_flattens_the_list_and_clearing_it_restores_groups`, `test_flat_mode_lists_every_light_by_name_with_no_groups` | ✅ Pass |
| 5 | A light in two collections appears under both, with the info icon | `test_light_in_two_collections_is_listed_under_each_and_once_when_flat`, `test_info_tooltip_names_whichever_cases_apply` | ✅ Pass (data); icon: manual ☐ |
| 6 | Group counts include sub-collections, follow the type filter, count once | `test_group_counts_include_sub_collections_once_and_follow_the_type_filter` | ✅ Pass |
| 7 | Group select selects the group's lights; Shift+click extends | `test_select_group_selects_only_the_lights_in_it_and_its_sub_collections`, `test_select_group_with_extend_keeps_the_earlier_selection`, `test_select_group_follows_the_type_filter_…` | ✅ Pass (operator); Shift+click: manual ☐ |
| 8 | Move selected here leaves each editable light only in the target | `test_move_relinks_selected_lights_only_into_the_target_and_skips_library_lights`, `test_move_into_a_library_collection_is_refused_and_nothing_moves` | ✅ Pass |
| 9 | Hide group toggles both collection flags; muted lights stay muted; lights dimmed | `test_hide_group_toggles_both_collection_flags_and_never_touches_light_flags`, `test_lights_in_a_hidden_group_are_dimmed_but_not_muted` | ✅ Pass (state); dimmed look: manual ☐ |
| 10 | Soloing a light in a hidden group shows it; un-solo restores every flag | `test_soloing_a_light_in_a_hidden_group_shows_it_and_unsolo_restores_every_flag`, `test_solo_hides_every_other_light_…` | ✅ Pass |
| 11 | Group solo shows only its lights; switching keeps the first snapshot | `test_group_solo_shows_only_its_lights_…`, `test_switching_light_to_group_to_light_…`, `test_only_the_soloed_target_reports_itself_soloed_…` | ✅ Pass |
| 12 | Renaming during solo doesn't break un-solo | `test_renaming_the_soloed_light_another_light_and_a_hidden_collection_during_solo_still_restores_them`, `test_deleting_a_snapshotted_light_and_collection_during_solo_…` | ✅ Pass |
| 13 | Collapsing is saved with the file, no undo step | `test_collapsed_group_stays_collapsed_after_saving_and_reopening`, `test_toggle_group_flips_collapsed_without_an_undo_step`, `test_toggle_all_collapses_every_listed_group_…` | ✅ Pass (save, no `UNDO`); Ctrl+Z: manual ☐ |
| 14 | Details accordion; Shift keeps others; no undo step, not saved | `test_opening_details_closes_the_others_unless_keep_others_is_set`, `test_open_details_are_panel_state_outside_undo_and_the_object`, `test_renaming_a_light_keeps_its_details_open`, `test_toggling_details_forgets_deleted_lights` | ✅ Pass (logic); Shift+click, Ctrl+Z: manual ☐ |
| 15 | Click, Shift, Ctrl, Alt on a name; selected/active rows highlighted | `test_select_action_…`, `test_toggle_adds_…`, `test_rename_renames_…`, `test_frame_selects_only_that_light_without_a_3d_view`, `test_range_…` (3 tests) | ✅ Pass (actions); modifier clicks, highlight: manual ☐ |
| 16 | Row type dropdown changes the type; one undo reverts; disabled on library lights | `test_changing_the_type_of_shared_light_data_changes_every_object_using_it`, `test_light_linked_from_a_library_is_read_only_…` | ✅ Pass (data); undo, disabled look: manual ☐ |
| 17 | No gap between power and color; unit label visible | none (layout only) | manual ☐ |
| 18 | Kelvin field instead of swatch; details show Exposure and Temperature | `test_row_shows_kelvin_only_for_a_light_using_temperature`, `test_eevee_details_show_only_properties_each_light_type_uses` | ✅ Pass (choice, paths); drawn field: manual ☐ |
| 19 | Built-ins apply Kelvin on 5.0+, RGB on older; user Kelvin preset round-trips; pre-v2 file loads | `test_built_ins_set_their_kelvin_with_a_white_color_that_does_not_tint_it`, `test_built_ins_set_only_the_rgb_color_on_a_light_without_temperature`, `test_a_preset_saved_from_a_kelvin_light_restores_its_kelvin_and_exposure_after_restarting`, `test_a_preset_file_saved_before_v2_applies_with_no_exposure_and_temperature_off` | ✅ Pass |
| 20 | `+` adds a light at the cursor in the active collection, selected and active | `test_add_light_puts_each_type_at_the_cursor_in_the_active_collection_selected_and_active` | ✅ Pass (operator); `+` menu: manual ☐ |
| 21 | No errors on Cycles or EEVEE for any type, on 5.2.2 and without temperature properties | engine smoke above; `test_details_leave_out_properties_an_older_blender_lacks`, `test_built_ins_set_only_the_rgb_color_…`, `test_row_shows_kelvin_…` (stub) | ✅ Pass (headless 5.2.2); real 4.2: not run; panel draw: manual ☐ |

## Manual checklist (Blender 5.2.2 GUI, console open)

Start Blender from a terminal with the extension installed. Each step should leave no Lighthouse warnings or errors in the console. Under EEVEE, then Cycles, use one light of each type (point, sun, spot, area), some of them in nested collections.

**Panels and intensity**
- [ ] **AC 1**: the Lights tab shows Intensity, Presets and Lights as three panels. Each collapses and can be dragged to reorder. With Presets collapsed, its header dropdown and Apply still work.
- [ ] **AC 2**: the factor field is a plain number (no bar) showing 1.0. The six EV buttons read −1, −½, −¼, +¼, +½, +1.
- [ ] **AC 7 (v1)**: scale by 0.5, then press Ctrl+Z once and every value comes back. Do the same with +¼ EV.

**List and groups**
- [ ] **AC 3–5**: grouped view nests as in the outliner. Typing a search goes flat, and clearing it goes back. A light in two collections shows under both with an info icon whose tooltip explains why.
- [ ] **AC 7**: click a group's select button, then Shift+click another group's. The first selection is kept.
- [ ] **AC 9**: hide a group. Its lights are drawn dimmed, and unhiding it leaves a pre-muted light muted.
- [ ] **AC 13**: collapse a group and press Ctrl+Z. The group stays collapsed (no undo step). Save, reopen, and it is still collapsed.

**Rows**
- [ ] **AC 14**: open one light's details, then another's. The first closes. Shift+click a third, and both stay open. Ctrl+Z doesn't change them.
- [ ] **AC 15**: on a name, a click selects, Shift+click selects a range, Ctrl+Shift+click toggles, Ctrl+click opens Rename, and Alt+click frames the light. Selected and active rows are highlighted. Note which modifier clicks Blender passes through to the button.
- [ ] **AC 16**: change a row's type from the dropdown, then press Ctrl+Z once and it reverts. On a library light the dropdown is disabled.
- [ ] **AC 17**: power runs straight into the color swatch with no gap, and the W or W/m² label is visible. Widen and narrow the sidebar.
- [ ] **AC 18**: turn on Use Temperature for a light. Its row shows a Kelvin field (e.g. "6500 K") in place of the swatch, readable in full at the default sidebar width. Its details show Exposure, Use Temperature and Temperature.
- [ ] **AC 19**: apply Candle to a point light. The row shows 1850 K, and Properties › Light shows the color white. Save a preset from it, restart Blender, apply it to another light, and Kelvin and exposure come back.
- [ ] **AC 20**: `+` › each type adds a light at the 3D cursor in the active collection, selected and active.
- [ ] **AC 21**: every step above, under both engines, leaves the console free of Lighthouse errors.
