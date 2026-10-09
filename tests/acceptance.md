# Acceptance pass: Blender 5.2.2 LTS

Walks PRD acceptance criteria 1–14. Each criterion lists its automated evidence (pytest, headless Blender) and any check that needs the GUI.

- **Automated**: `make test` → 50 passed (2026-10-09).
- **Engine smoke**: `tests/smoke_engines.py` runs every operator on point, sun, spot and area lights under Cycles, then EEVEE, against the zip installed in a clean profile. Run 2026-10-09: both engines OK, with no Lighthouse warnings or errors.
- **Manual (GUI)**: the panel can't be drawn and undo can't run in `--background`. Those items are ticked only after someone checks them by hand in Blender 5.2.2.

Known environment noise (Fedora's package, unrelated to Lighthouse): an OpenColorIO 2.5 config error on launch, and a `bl_pkg` register traceback (`No module named 'cattrs'`) when a user profile is set.

## Clean-profile install (AC 1, 14)

```sh
./build.sh
export BLENDER_USER_RESOURCES=$(mktemp -d)
blender --command extension install-file -r user_default -e dist/lighthouse-0.1.0.zip
blender -b --python tests/smoke_engines.py
```

Run 2026-10-09: `STATUS Installed "lighthouse"`, and after a restart `bl_ext.user_default.lighthouse` is enabled and `LIGHTHOUSE_PT_lights` is registered. Disable and re-enable are clean.

## Criteria

| AC | Criterion | Automated evidence | Result |
|----|-----------|--------------------|--------|
| 1 | Installs as an extension in 5.2.2 and enables without errors | clean-profile install above; `test_build_produces_installable_zip` | ✅ Pass |
| 2 | "Lights" tab lists all lights in the view layer | `test_lists_every_light_in_view_layer_and_nothing_else`, `test_list_follows_lights_added_and_deleted` | ✅ Pass (list); tab: manual ☐ |
| 3 | Row power slider and color update the light, and the Properties editor reflects it | `test_editing_power_on_one_shared_row_changes_the_other`, `test_editing_a_detail_changes_the_light_the_properties_editor_shows` | ✅ Pass (data); slider/swatch: manual ☐ |
| 4 | Name and type filters narrow the list | `test_name_search_…`, `test_type_filter_…`, `test_lights_are_listed_alphabetically_ignoring_case` | ✅ Pass |
| 5 | Clicking a name selects the light and makes it active | `test_clicking_a_name_selects_only_that_light_and_makes_it_active` | ✅ Pass |
| 6 | Hidden lights listed greyed out, library lights not editable | `test_hidden_lights_stay_listed`, `test_hidden_lights_are_dimmed_…`, `test_light_linked_from_a_library_is_read_only_…`, `test_light_with_system_override_is_read_only_…` | ✅ Pass (state); greyed/disabled look: manual ☐ |
| 7 | Scale 0.5 halves all or only the selected lights; one undo restores | `test_scaling_all_lights_by_half_halves_every_power`, `test_scaling_selected_lights_changes_only_the_selected_ones` | ✅ Pass (scale); one-step undo: manual ☐ |
| 8 | +1 EV doubles, -1 EV halves, sun included | `test_plus_one_ev_…`, `test_minus_one_ev_…`, `test_ev_steps_work_on_every_light_type` | ✅ Pass |
| 9 | Keyframes scale too, and the value after a frame change matches | `test_scaling_a_keyframed_light_scales_its_keyframes`, `test_after_a_frame_change_the_animated_power_is_the_scaled_value`, `test_ev_steps_scale_keyframes` | ✅ Pass |
| 10 | Solo hides others, un-solo restores exact flags, mute hides only that light | `test_solo_hides_every_other_light_and_unsolo_restores_their_exact_flags`, `test_switching_solo_…`, `test_mute_hides_only_that_light_…` | ✅ Pass |
| 11 | Built-in presets apply power/color/radius to compatible selected lights, skip others | `test_60w_bulb_changes_a_selected_point_light_but_not_a_selected_sun`, `test_candle_sets_…`, `test_daylight_sets_…` | ✅ Pass |
| 12 | User preset saved in one .blend is available in another | `test_a_preset_saved_from_a_light_in_one_file_applies_after_restarting_with_another_file` | ✅ Pass |
| 13 | Correct under Cycles and EEVEE, no errors for missing properties | `test_eevee_details_…`, `test_switching_to_cycles_adds_cycles_options_…`; engine smoke above | ✅ Pass (headless); panel draw: manual ☐ |
| 14 | Manifest validates and the extension builds into a zip | `test_manifest_validates`, `test_build_script_builds_the_versioned_zip`, `test_zip_ships_the_gpl3_license` | ✅ Pass |

## Manual checklist (Blender 5.2.2 GUI, console open)

Start Blender from a terminal with the extension installed. Each step should leave no Lighthouse warnings or errors in the console.

- [ ] **AC 2**: N-panel › **Lights** tab is present and lists every light, hidden ones included.
- [ ] **AC 3**: dragging a row's power slider and changing its color swatch updates Properties › Light at the same time.
- [ ] **AC 6**: a hidden light's row is greyed out. A linked-library light's slider and swatch are disabled, but its name still selects it.
- [ ] **AC 7**: scale by 0.5 (All, then Selected), then press Ctrl+Z once. Every value comes back. Do the same with +1 EV.
- [ ] **AC 13**: under EEVEE, then under Cycles, expand a row of each type (point, sun, spot, area). The details match the engine and update when you switch engines. Solo, mute, apply a preset, save and delete a user preset.
