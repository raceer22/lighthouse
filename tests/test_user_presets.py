from pytest import approx

from blender_runner import run_installed


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

    assert ["Candle", "60W Bulb", "Daylight"] == [name for _, name, _ in items[:3]]
    assert [[name, icon] for _, name, icon in items[3:]] == [["My Key", "USER"]]
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

    assert items == ["Candle", "60W Bulb", "Daylight", "Good"]
    assert "Skipped user preset Broken.json" in output
    assert "Skipped user preset Incomplete.json" in output


def test_a_deleted_user_preset_is_gone_after_restarting_and_built_ins_cannot_be_deleted(tmp_path):
    built_in_refused = run_installed("""
        empty_scene()
        bpy.context.view_layer.objects.active = add_light("Key")
        bpy.ops.lighthouse.save_preset(name="Keep")
        bpy.ops.lighthouse.save_preset(name="Drop")
        drop = [i for i, name, _ in preset_items() if name == "Drop"][0]
        bpy.ops.lighthouse.delete_preset(preset=drop)
        try:
            bpy.ops.lighthouse.delete_preset(preset='CANDLE')
            refused = False
        except TypeError:
            refused = True
        report(refused)
    """, tmp_path / "config")[0]

    items = run_installed("""
        report([name for _, name, _ in preset_items()])
    """, tmp_path / "config")[0]

    assert built_in_refused
    assert items == ["Candle", "60W Bulb", "Daylight", "Keep"]


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
