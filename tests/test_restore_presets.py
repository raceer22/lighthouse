from pytest import approx

from blender_runner import reports, run_installed


def folder_of(config):
    return config / "extensions" / ".user" / "user_default" / "lighthouse"


def test_restore_brings_back_a_deleted_default_and_keeps_an_edited_one(tmp_path):
    presets, output = run_installed("""
        empty_scene()
        key = add_light("Key", "SUN")
        key.data.energy = 9
        bpy.context.view_layer.objects.active = key
        bpy.ops.lighthouse.delete_preset(preset="USER:Moonlight")
        bpy.ops.lighthouse.save_preset(name="Midday Sun", overwrite=True)
        bpy.ops.lighthouse.restore_default_presets()
        addon = __import__("sys").modules[bpy.types.LIGHTHOUSE_OT_save_preset.__module__]
        found = addon.all_presets()
        report({key: [p.power, p.radius] for key, p in found.items()})
    """, tmp_path / "config")

    assert presets["USER:Moonlight"] == approx([0.05, 0.0093])
    assert presets["USER:Midday Sun"][0] == 9
    assert reports(output)[-1] == "Restored Moonlight"


def test_restore_with_every_default_present_writes_nothing(tmp_path):
    run_installed("report(preset_items())", tmp_path / "config")
    folder = folder_of(tmp_path / "config")
    before = {p.name: p.stat().st_mtime_ns for p in folder.iterdir()} | {".": folder.stat().st_mtime_ns}

    output = run_installed("""
        bpy.ops.lighthouse.restore_default_presets()
        report(None)
    """, tmp_path / "config")[1]

    assert {p.name: p.stat().st_mtime_ns for p in folder.iterdir()} | {".": folder.stat().st_mtime_ns} == before
    assert reports(output) == ["Every default preset is already there"]


def test_restore_leaves_other_user_presets_alone(tmp_path):
    run_installed("""
        empty_scene()
        key = add_light("Key")
        key.data.energy = 77
        bpy.context.view_layer.objects.active = key
        bpy.ops.lighthouse.save_preset(name="Mine")
        bpy.ops.lighthouse.delete_preset(preset="USER:Warm Interior Bulb")
        report(None)
    """, tmp_path / "config")
    mine = folder_of(tmp_path / "config") / "Mine.json"
    before = mine.read_text(), mine.stat().st_mtime_ns

    run_installed("""
        bpy.ops.lighthouse.restore_default_presets()
        report(None)
    """, tmp_path / "config")

    assert (mine.read_text(), mine.stat().st_mtime_ns) == before
