import textwrap

import pytest

from blender_runner import RECORDER, blender_version, needs_blender, run_in_blender

SETUP = """
import lighthouse
lighthouse.register()
empty_scene()
scene = bpy.context.scene
layer = bpy.context.view_layer

def new_light(**kwargs):
    bpy.ops.lighthouse.add_light(type='POINT', **kwargs)
    light = layer.objects.active.data
    return {"use_temperature": light.use_temperature, "temperature": light.temperature,
            "color": [round(c, 4) for c in light.color]}

# Lights have no temperature before Blender 5.0.
DEFAULT_TEMPERATURE = getattr(bpy.types.Light.bl_rna.properties.get("temperature"), "default", None)
DEFAULT_COLOR = [round(c, 4) for c in bpy.types.Light.bl_rna.properties["color"].default_array]
"""

only_before_5 = pytest.mark.skipif(blender_version() >= (5, 0), reason="checks Blender before 5.0")


def run(snippet, setup=""):
    return run_in_blender(SETUP + setup + textwrap.dedent(snippet))


def test_toggling_pins_the_opposite_of_the_default_and_toggling_back_follows_it_again():
    result = run("""
        from lighthouse.lights import new_light_mode, toggled_mode
        table = {}
        for default in ('COLOR', 'KELVIN'):
            steps = ['FOLLOW']
            for _ in range(2):
                steps.append(toggled_mode(steps[-1], default))
            table[default] = [[value, new_light_mode(value, default)] for value in steps]
        report(table)
    """)

    assert result == {
        "COLOR": [["FOLLOW", "COLOR"], ["KELVIN", "KELVIN"], ["FOLLOW", "COLOR"]],
        "KELVIN": [["FOLLOW", "KELVIN"], ["COLOR", "COLOR"], ["FOLLOW", "KELVIN"]],
    }


@needs_blender(5, 0, "Light.use_temperature")
def test_a_fresh_file_follows_color_and_new_lights_keep_blenders_color():
    result = run("""
        light = new_light()
        report([scene.lighthouse_new_lights, light["use_temperature"], light["color"] == DEFAULT_COLOR])
    """)

    assert result == ["FOLLOW", False, True]


@needs_blender(5, 0, "Light.use_temperature")
def test_after_one_toggle_new_lights_start_in_kelvin_at_the_default_temperature_and_white():
    result = run("""
        bpy.ops.lighthouse.toggle_new_light_mode()
        collection = bpy.data.collections.new("Set")
        scene.collection.children.link(collection)
        expected = {"use_temperature": True, "temperature": DEFAULT_TEMPERATURE, "color": [1.0, 1.0, 1.0]}
        report([scene.lighthouse_new_lights,
                new_light() == expected,
                new_light(name="Set", use_active=False) == expected])
    """)

    assert result == ["KELVIN", True, True]


@needs_blender(5, 0, "Light.use_temperature")
def test_a_second_toggle_follows_the_default_again():
    result = run("""
        bpy.ops.lighthouse.toggle_new_light_mode()
        bpy.ops.lighthouse.toggle_new_light_mode()
        report([scene.lighthouse_new_lights, new_light()["use_temperature"]])
    """)

    assert result == ["FOLLOW", False]


@needs_blender(5, 0, "Light.use_temperature")
def test_kelvin_mode_leaves_blenders_own_add_and_duplicate_alone():
    result = run("""
        scene.lighthouse_new_lights = 'KELVIN'
        bpy.ops.object.light_add(type='POINT')
        added = layer.objects.active
        bpy.ops.object.select_all(action='DESELECT')
        added.select_set(True)
        bpy.ops.object.duplicate()
        duplicate = layer.objects.active
        report([added.data.use_temperature, duplicate is not added, duplicate.data.use_temperature])
    """)

    assert result == [False, True, False]


def test_the_files_mode_is_saved_with_it():
    result = run("""
        import os, tempfile
        path = os.path.join(tempfile.mkdtemp(), "mode.blend")
        bpy.context.scene.lighthouse_new_lights = 'KELVIN'
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.open_mainfile(filepath=path)
        report(bpy.context.scene.lighthouse_new_lights)
    """)

    assert result == "KELVIN"


def test_header_draws_the_toggle_only_where_lights_have_a_temperature():
    result = run("""
        from lighthouse.lights import supports_temperature
        def panel_draw(holder, context):
            panel = bpy.types.LIGHTHOUSE_PT_lights
            methods = {name: value for name, value in vars(panel).items() if name.startswith("draw")}
            panel.draw(type("Panel", (), {**methods, "layout": holder.layout})(), context)
        entries = drawn(panel_draw)
        header = entries[:entries.index(["prop", "type_filter"])]
        report([supports_temperature(), [e for e in header if "lighthouse.toggle_new_light_mode" in e]])
    """, RECORDER)

    if blender_version() >= (5, 0):
        assert result == [True, [["operator", "lighthouse.toggle_new_light_mode", ""]]]
    else:
        assert result == [False, []]


@only_before_5
def test_kelvin_mode_before_5_adds_a_plain_light():
    result = run("""
        scene.lighthouse_new_lights = 'KELVIN'
        report([bpy.ops.lighthouse.add_light(type='POINT') == {'FINISHED'},
                hasattr(layer.objects.active.data, "use_temperature")])
    """)

    assert result == [True, False]
