from pytest import approx

from blender_runner import blender_version, needs_blender, reports, run_installed

# The default presets set Kelvin on 5.0+ with a white color; older lights get the RGB fallback.
KELVIN = blender_version() >= (5, 0)


def test_warm_interior_bulb_changes_a_selected_point_light_but_not_a_selected_sun(tmp_path):
    lights = run_installed("""
        empty_scene()
        point = add_light("Point", "POINT")
        sun = add_light("Sun", "SUN")
        for obj in (point, sun):
            obj.data.energy = 7
            obj.data.color = (0.2, 0.3, 0.4)
            obj.data.shadow_soft_size = 0.5
            obj.select_set(True)
        sun.data.angle = 0.1
        bpy.ops.lighthouse.apply_preset(preset='USER:Warm Interior Bulb')
        report({
            obj.name: [obj.data.energy, list(obj.data.color), obj.data.shadow_soft_size]
            for obj in (point, sun)
        } | {"sun angle": sun.data.angle})
    """, tmp_path)[0]

    assert lights == {
        "Point": [40, [1, 1, 1] if KELVIN else approx([1.0, 0.73, 0.45]), approx(0.035)],
        "Sun": [7, approx([0.2, 0.3, 0.4]), 0.5],
        "sun angle": approx(0.1),
    }


def test_unselected_lights_are_untouched_and_skipped_lights_are_reported(tmp_path):
    energies, output = run_installed("""
        empty_scene()
        lights = [add_light("Desk"), add_light("Hall"), add_light("Sun", "SUN"), add_light("Moon", "SUN")]
        for obj in lights:
            obj.data.energy = 7
        for obj in (lights[0], lights[2], lights[3]):
            obj.select_set(True)
        bpy.ops.lighthouse.apply_preset(preset='USER:Warm Interior Bulb')
        report({obj.name: obj.data.energy for obj in lights})
    """, tmp_path)

    assert energies == {"Desk": 40, "Hall": 7, "Sun": 7, "Moon": 7}
    assert reports(output) == ["Applied Warm Interior Bulb to 1 light (2 skipped: incompatible type)"]


def test_studio_softbox_sets_an_area_light_size_to_the_preset_diameter(tmp_path):
    size = run_installed("""
        empty_scene()
        area = add_light("Area", "AREA")
        area.data.size = 0.3
        area.select_set(True)
        bpy.ops.lighthouse.apply_preset(preset='USER:Studio Softbox')
        report(area.data.size)
    """, tmp_path)[0]

    assert size == approx(1.0)


def test_midday_sun_sets_a_selected_sun_and_its_angle(tmp_path):
    sun = run_installed("""
        empty_scene()
        sun = add_light("Sun", "SUN")
        sun.data.angle = 0.1
        sun.select_set(True)
        bpy.ops.lighthouse.apply_preset(preset='USER:Midday Sun')
        report([sun.data.energy, list(sun.data.color), sun.data.angle])
    """, tmp_path)[0]

    assert sun == [4.5, [1, 1, 1] if KELVIN else approx([1.0, 0.97, 0.92]), approx(0.0093)]


@needs_blender(5, 0, "Light.use_temperature")
def test_default_presets_set_their_kelvin_with_a_white_color_that_does_not_tint_it(tmp_path):
    lights = run_installed("""
        empty_scene()
        lights = {}
        for preset, light_type in (('Studio Softbox', 'AREA'), ('Warm Interior Bulb', 'POINT'), ('Midday Sun', 'SUN'),
                                    ('Golden Hour Sun', 'SUN'), ('Moonlight', 'SUN')):
            for obj in bpy.context.view_layer.objects:
                obj.select_set(False)
            obj = add_light(preset, light_type)
            obj.data.color = (0.2, 0.3, 0.4)
            obj.select_set(True)
            bpy.ops.lighthouse.apply_preset(preset='USER:' + preset)
            lights[preset] = [obj.data.use_temperature, obj.data.temperature, list(obj.data.color)]
        report(lights)
    """, tmp_path)[0]

    assert lights == {
        "Studio Softbox": [True, 5600, [1, 1, 1]],
        "Warm Interior Bulb": [True, 2700, [1, 1, 1]],
        "Midday Sun": [True, 5500, [1, 1, 1]],
        "Golden Hour Sun": [True, 2800, [1, 1, 1]],
        "Moonlight": [True, 4100, [1, 1, 1]],
    }


def test_a_library_light_is_skipped_as_read_only_and_reported(tmp_path):
    energies, output = run_installed(f"""
        empty_scene()
        library_light = add_light("Library")
        path = {str(tmp_path / "library.blend")!r}
        bpy.data.libraries.write(path, {{library_light}})
        bpy.data.objects.remove(library_light)
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.objects = ["Library"]
        bpy.context.scene.collection.objects.link(dst.objects[0])
        local = add_light("Local")
        local.select_set(True)
        bpy.data.objects["Library"].select_set(True)
        from importlib import import_module
        presets = import_module("bl_ext.user_default.lighthouse.presets")
        counts = presets.apply_preset([local, bpy.data.objects["Library"]], presets.DEFAULT_PRESETS[1])
        local.data.energy = 7
        bpy.ops.lighthouse.apply_preset(preset='USER:Warm Interior Bulb')
        report([list(counts), {{o.name: o.data.energy for o in bpy.context.view_layer.objects}}])
    """, tmp_path / "config")

    counts, energies = energies
    assert counts == [1, 0, 1]
    assert energies == {"Local": 40, "Library": 10}
    assert reports(output) == ["Applied Warm Interior Bulb to 1 light (1 skipped: read-only)"]
