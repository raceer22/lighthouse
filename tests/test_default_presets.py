from blender_runner import run_installed

MARKER = ".defaults_installed"


def folder_of(config):
    return config / "extensions" / ".user" / "user_default" / "lighthouse"


def test_a_fresh_user_dir_gets_the_defaults_as_plain_files(tmp_path):
    items = run_installed("report(preset_items())", tmp_path / "config")[0]

    assert sorted(p.name for p in folder_of(tmp_path / "config").iterdir()) == [
        MARKER, "Golden Hour Sun.json", "Midday Sun.json", "Moonlight.json",
        "Studio Softbox.json", "Warm Interior Bulb.json"]
    assert [[name, icon] for _, name, icon in items] == [
        ["Golden Hour Sun", "NONE"], ["Midday Sun", "NONE"], ["Moonlight", "NONE"],
        ["Studio Softbox", "NONE"], ["Warm Interior Bulb", "NONE"]]


def test_a_deleted_default_stays_deleted_after_restarting(tmp_path):
    run_installed("""
        bpy.ops.lighthouse.delete_preset(preset="USER:Moonlight")
        report(None)
    """, tmp_path / "config")

    names = run_installed("report([name for _, name, _ in preset_items()])", tmp_path / "config")[0]

    assert names == ["Golden Hour Sun", "Midday Sun", "Studio Softbox", "Warm Interior Bulb"]


def test_nothing_is_seeded_when_the_marker_is_already_there(tmp_path):
    folder = folder_of(tmp_path / "config")
    folder.mkdir(parents=True)
    (folder / MARKER).touch()

    items = run_installed("report(preset_items())", tmp_path / "config")[0]

    assert items == []
    assert [p.name for p in folder.iterdir()] == [MARKER]


def test_saving_as_moonlight_needs_overwrite_like_any_other_preset(tmp_path):
    (refused, power), output = run_installed("""
        empty_scene()
        key = add_light("Key")
        key.data.energy = 321
        bpy.context.view_layer.objects.active = key
        try:
            bpy.ops.lighthouse.save_preset(name="Moonlight")
            refused = False
        except RuntimeError:
            refused = True
        bpy.ops.lighthouse.save_preset(name="Moonlight", overwrite=True)
        addon = __import__("sys").modules[bpy.types.LIGHTHOUSE_OT_save_preset.__module__]
        report([refused, addon.all_presets()["USER:Moonlight"].power])
    """, tmp_path / "config")

    assert refused
    assert "exists" in output
    assert power == 321


def test_deleting_the_shown_preset_selects_the_next_one_then_the_new_last_then_nothing(tmp_path):
    shown = run_installed("""
        settings = bpy.context.window_manager.lighthouse
        bpy.ops.lighthouse.delete_preset(preset="USER:Golden Hour Sun")
        bpy.ops.lighthouse.delete_preset(preset="USER:Warm Interior Bulb")
        shown = []
        for key in ("USER:Moonlight", "USER:Studio Softbox", "USER:Midday Sun"):
            settings.preset = key
            bpy.ops.lighthouse.delete_preset(preset=key)
            shown.append(settings.preset)
        report(shown)
    """, tmp_path / "config")[0]

    assert shown == ["USER:Studio Softbox", "USER:Midday Sun", ""]
