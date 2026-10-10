import textwrap

import pytest

from blender_runner import RECORDER, blender_version, needs_blender, run_installed

SETUP = """
prefs = bpy.context.preferences.addons["bl_ext.user_default.lighthouse"].preferences
scene = bpy.context.scene
layer = bpy.context.view_layer
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)

def new_light_in_kelvin():
    bpy.ops.lighthouse.add_light(type='POINT')
    return layer.objects.active.data.use_temperature
"""


def run(snippet, user_dir, setup=""):
    return run_installed(SETUP + setup + textwrap.dedent(snippet), user_dir)[0]


@needs_blender(5, 0, "Light.use_temperature")
def test_an_untouched_file_follows_a_kelvin_default(tmp_path):
    result = run("""
        prefs.new_light_mode = 'KELVIN'
        report([scene.lighthouse_new_lights, new_light_in_kelvin()])
    """, tmp_path)

    assert result == ["FOLLOW", True]


@needs_blender(5, 0, "Light.use_temperature")
def test_with_a_kelvin_default_one_toggle_pins_color_and_a_second_follows_again(tmp_path):
    result = run("""
        prefs.new_light_mode = 'KELVIN'
        steps = []
        for _ in range(2):
            bpy.ops.lighthouse.toggle_new_light_mode()
            steps.append([scene.lighthouse_new_lights, new_light_in_kelvin()])
        report(steps)
    """, tmp_path)

    assert result == [["COLOR", False], ["FOLLOW", True]]


@needs_blender(5, 0, "Light.use_temperature")
def test_a_pinned_file_keeps_its_mode_when_the_default_changes_and_a_following_file_switches(tmp_path):
    result = run("""
        def after_default_changes_to_kelvin(scene_value):
            prefs.new_light_mode = 'COLOR'
            scene.lighthouse_new_lights = scene_value
            before = new_light_in_kelvin()
            prefs.new_light_mode = 'KELVIN'
            return [before, new_light_in_kelvin()]
        report({"pinned": after_default_changes_to_kelvin('COLOR'),
                "following": after_default_changes_to_kelvin('FOLLOW')})
    """, tmp_path)

    assert result == {"pinned": [False, False], "following": [False, True]}


# Blender 4.2 crashes on wm.read_userpref() in background mode, and hides this setting anyway.
@pytest.mark.skipif(blender_version() < (5, 0), reason="wm.read_userpref() crashes Blender 4.2 headless")
def test_the_default_is_kept_across_restarts(tmp_path):
    run("""
        prefs.new_light_mode = 'KELVIN'
        bpy.ops.wm.save_userpref()
        report(True)
    """, tmp_path)
    # The test runs use --factory-startup, which skips userpref.blend, so load it as a normal start would.
    result = run("""
        bpy.ops.wm.read_userpref()
        prefs = bpy.context.preferences.addons["bl_ext.user_default.lighthouse"].preferences
        report(prefs.new_light_mode)
    """, tmp_path)

    assert result == "KELVIN"


def test_preferences_draw_the_default_only_where_lights_have_a_temperature(tmp_path):
    log = run("""
        report(drawn(type(prefs).draw))
    """, tmp_path, setup=RECORDER)

    assert ["operator", "lighthouse.restore_default_presets", "Restore Default Presets"] in log
    assert (["prop", "new_light_mode"] in log) == (blender_version() >= (5, 0))
