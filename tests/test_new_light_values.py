import textwrap

from blender_runner import needs_blender, run_in_blender

SETUP = """
import lighthouse
lighthouse.register()
empty_scene()
layer = bpy.context.view_layer

def added(light_type):
    bpy.ops.lighthouse.add_light(type=light_type)
    return layer.objects.active.data
"""


def run(snippet):
    return run_in_blender(SETUP + textwrap.dedent(snippet))


def test_a_new_sun_and_area_get_shift_a_values():
    result = run("""
        sun, area = added('SUN'), added('AREA')
        report([sun.energy, area.size, area.size_y])
    """)

    assert result == [1.0, 1.0, 1.0]


def test_a_new_point_and_spot_keep_the_values_lights_new_gives():
    result = run("""
        def values(light):
            return [light.energy, light.shadow_soft_size] + ([light.spot_size] if light.type == 'SPOT' else [])
        report([values(added(t)) == values(bpy.data.lights.new("Plain", t)) for t in ('POINT', 'SPOT')])
    """)

    assert result == [True, True]


@needs_blender(5, 0, "Light.use_temperature")
def test_in_kelvin_mode_a_new_sun_and_area_get_both_shift_a_values_and_kelvin():
    result = run("""
        bpy.context.scene.lighthouse_new_lights = 'KELVIN'
        default = bpy.types.Light.bl_rna.properties["temperature"].default
        sun, area = added('SUN'), added('AREA')
        report([[sun.energy, sun.use_temperature, sun.temperature == default, list(sun.color)],
                [area.size, area.size_y, area.use_temperature, area.temperature == default, list(area.color)]])
    """)

    assert result == [[1.0, True, True, [1.0, 1.0, 1.0]], [1.0, 1.0, True, True, [1.0, 1.0, 1.0]]]
