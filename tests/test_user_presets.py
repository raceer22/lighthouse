from pytest import approx

from blender_runner import needs_blender, run_installed


def test_a_preset_saved_from_a_light_in_one_file_applies_after_restarting_with_another_file(tmp_path):
    run_installed(f"""
        empty_scene()
        key = add_light("Key", "SPOT")
        key.data.energy = 250
        key.data.color = (0.9, 0.8, 0.7)
        key.data.shadow_soft_size = 0.2
        bpy.context.view_layer.objects.active = key
        bpy.ops.lighthouse.save_preset(name="My Key")
        bpy.ops.wm.save_as_mainfile(filepath={str(tmp_path / "a.blend")!r})
        report(None)
    """, tmp_path / "config")

    items, light = run_installed(f"""
        bpy.ops.wm.read_homefile(use_empty=True)
        bpy.ops.wm.save_as_mainfile(filepath={str(tmp_path / "b.blend")!r})
        point = add_light("Fill")
        point.select_set(True)
        items = preset_items()
        bpy.ops.lighthouse.apply_preset(preset=[i for i, name, icon in items if name == "My Key"][0])
        report([items, [point.data.energy, list(point.data.color), point.data.shadow_soft_size]])
    """, tmp_path / "config")[0]

    assert [[name, icon] for _, name, icon in items] == [
        ["Golden Hour Sun", "NONE"], ["Midday Sun", "NONE"], ["Moonlight", "NONE"], ["My Key", "NONE"],
        ["Studio Softbox", "NONE"], ["Warm Interior Bulb", "NONE"]]
    assert light == [250, approx([0.9, 0.8, 0.7]), approx(0.2)]


def test_corrupt_user_preset_files_are_skipped_with_a_warning(tmp_path):
    run_installed("""
        empty_scene()
        bpy.context.view_layer.objects.active = add_light("Key")
        bpy.ops.lighthouse.save_preset(name="Good")
        report(None)
    """, tmp_path / "config")
    folder = tmp_path / "config" / "extensions" / ".user" / "user_default" / "lighthouse"
    (folder / "Broken.json").write_text("{not json")
    (folder / "Incomplete.json").write_text('{"label": "Incomplete"}')

    items, output = run_installed("""
        report([name for _, name, _ in preset_items()])
    """, tmp_path / "config")

    assert items == ["Golden Hour Sun", "Good", "Midday Sun", "Moonlight", "Studio Softbox", "Warm Interior Bulb"]
    assert "Skipped user preset Broken.json" in output
    assert "Skipped user preset Incomplete.json" in output


def test_a_deleted_user_preset_is_gone_after_restarting(tmp_path):
    run_installed("""
        empty_scene()
        bpy.context.view_layer.objects.active = add_light("Key")
        bpy.ops.lighthouse.save_preset(name="Keep")
        bpy.ops.lighthouse.save_preset(name="Drop")
        drop = [i for i, name, _ in preset_items() if name == "Drop"][0]
        bpy.ops.lighthouse.delete_preset(preset=drop)
        report(None)
    """, tmp_path / "config")

    items = run_installed("""
        report([name for _, name, _ in preset_items()])
    """, tmp_path / "config")[0]

    assert items == ["Golden Hour Sun", "Keep", "Midday Sun", "Moonlight", "Studio Softbox", "Warm Interior Bulb"]


@needs_blender(5, 0, "Light.use_temperature")
def test_a_preset_saved_from_a_kelvin_light_restores_its_kelvin_and_exposure_after_restarting(tmp_path):
    run_installed("""
        empty_scene()
        key = add_light("Key", "SPOT")
        key.data.use_temperature = True
        key.data.temperature = 3000
        key.data.exposure = 1.5
        bpy.context.view_layer.objects.active = key
        bpy.ops.lighthouse.save_preset(name="Warm Key")
        report(None)
    """, tmp_path / "config")

    light = run_installed("""
        empty_scene()
        fill = add_light("Fill")
        fill.select_set(True)
        bpy.ops.lighthouse.apply_preset(preset=[i for i, name, _ in preset_items() if name == "Warm Key"][0])
        report([fill.data.use_temperature, fill.data.temperature, fill.data.exposure])
    """, tmp_path / "config")[0]

    assert light == [True, 3000, 1.5]


@needs_blender(5, 0, "Light.use_temperature")
def test_a_preset_file_saved_before_v2_applies_with_no_exposure_and_temperature_off(tmp_path):
    folder = tmp_path / "config" / "extensions" / ".user" / "user_default" / "lighthouse"
    folder.mkdir(parents=True)
    (folder / "Old.json").write_text("""{
      "label": "Old", "type_compat": ["AREA", "POINT", "SPOT"],
      "power": 80.0, "color": [0.5, 0.6, 0.7], "radius": 0.1
    }""")

    light = run_installed("""
        empty_scene()
        fill = add_light("Fill")
        fill.data.use_temperature = True
        fill.data.exposure = 2
        fill.select_set(True)
        bpy.ops.lighthouse.apply_preset(preset=[i for i, name, _ in preset_items() if name == "Old"][0])
        report([fill.data.energy, list(fill.data.color), fill.data.use_temperature, fill.data.exposure])
    """, tmp_path / "config")[0]

    assert light == [80, approx([0.5, 0.6, 0.7]), False, 0]


def test_selected_preset_stays_selected_when_a_preset_sorting_before_it_is_saved(tmp_path):
    selected = run_installed("""
        empty_scene()
        bpy.context.view_layer.objects.active = add_light("Key")
        bpy.ops.lighthouse.save_preset(name="Alpha")
        bpy.ops.lighthouse.save_preset(name="Beta")
        settings = bpy.context.window_manager.lighthouse
        settings.preset = "USER:Beta"
        # Added without the operator (which selects what it saves), as another Blender instance would.
        common = __import__("sys").modules["bl_ext.user_default.lighthouse.common"]
        presets = __import__("sys").modules["bl_ext.user_default.lighthouse.presets"]
        presets.save_user_preset(common.presets_folder(), presets.DEFAULT_PRESETS[0]._replace(label="Aardvark"))
        report(settings.preset)
    """, tmp_path / "config")[0]

    assert selected == "USER:Beta"


def test_deleting_the_selected_preset_selects_the_next_one(tmp_path):
    after_alpha, after_last = run_installed("""
        empty_scene()
        bpy.context.view_layer.objects.active = add_light("Key")
        bpy.ops.lighthouse.save_preset(name="Alpha")
        bpy.ops.lighthouse.save_preset(name="Beta")
        settings = bpy.context.window_manager.lighthouse
        settings.preset = "USER:Alpha"
        bpy.ops.lighthouse.delete_preset(preset="USER:Alpha")
        after_alpha = settings.preset
        settings.preset = "USER:Beta"
        bpy.ops.lighthouse.delete_preset(preset="USER:Beta")
        report([after_alpha, settings.preset])
    """, tmp_path / "config")[0]

    assert after_alpha == "USER:Beta"
    assert after_last == "USER:Golden Hour Sun"


def test_saving_over_an_existing_preset_needs_overwrite(tmp_path):
    results = run_installed("""
        empty_scene()
        key = add_light("Key")
        bpy.context.view_layer.objects.active = key
        def save(**props):
            try:
                return bpy.ops.lighthouse.save_preset(**props) == {'FINISHED'}
            except RuntimeError:
                return False
        results = [save(name="My Key")]
        key.data.energy = 321
        results += [save(name="My Key"), save(name="My Key", overwrite=True)]
        results += [save(name="Key_Fill"), save(name="Key/Fill"), save(name="Key/Fill", overwrite=True)]
        results.append([p.power for p in __import__("sys").modules["bl_ext.user_default.lighthouse.common"].all_presets().values()
                        if p.label == "My Key"])
        report(results)
    """, tmp_path / "config")[0]

    assert results == [True, False, True, True, False, True, [321]]


def test_a_saved_preset_becomes_the_selected_one(tmp_path):
    selected = run_installed("""
        empty_scene()
        bpy.context.view_layer.objects.active = add_light("Key")
        bpy.ops.lighthouse.save_preset(name="Fresh")
        report(bpy.context.window_manager.lighthouse.preset)
    """, tmp_path / "config")[0]

    assert selected == "USER:Fresh"


def test_user_presets_are_parsed_once_until_a_save(tmp_path):
    counts = run_installed("""
        empty_scene()
        bpy.context.view_layer.objects.active = add_light("Key")
        bpy.ops.lighthouse.save_preset(name="One")
        bpy.ops.lighthouse.save_preset(name="Two")
        common = __import__("sys").modules["bl_ext.user_default.lighthouse.common"]
        presets = __import__("sys").modules["bl_ext.user_default.lighthouse.presets"]
        parsed = []
        real_loads = presets.json.loads
        presets.json = type("Json", (), {"loads": staticmethod(lambda text: parsed.append(1) or real_loads(text)),
                                          "dumps": staticmethod(presets.json.dumps)})
        common.all_presets()
        common.all_presets()
        counts = [len(parsed)]
        bpy.ops.lighthouse.save_preset(name="Three")
        common.all_presets()
        report(counts + [len(parsed)])
    """, tmp_path / "config")[0]

    assert counts[0] <= 2
    # One re-read of the folder: the three saved presets and the five defaults.
    assert counts[1] == counts[0] + 8
