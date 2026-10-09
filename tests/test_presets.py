from pytest import approx

from blender_runner import run_in_blender, run_in_blender_with_reports


def test_60w_bulb_changes_a_selected_point_light_but_not_a_selected_sun():
    lights = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        point = add_light("Point", "POINT")
        sun = add_light("Sun", "SUN")
        for obj in (point, sun):
            obj.data.energy = 7
            obj.data.color = (0.2, 0.3, 0.4)
            obj.data.shadow_soft_size = 0.5
            obj.select_set(True)
        sun.data.angle = 0.1
        bpy.ops.lighthouse.apply_preset(preset='BULB_60W')
        report({
            obj.name: [obj.data.energy, list(obj.data.color), obj.data.shadow_soft_size]
            for obj in (point, sun)
        } | {"sun angle": sun.data.angle})
    """)

    assert lights == {
        "Point": [60, approx([1.0, 0.71, 0.42]), approx(0.03)],
        "Sun": [7, approx([0.2, 0.3, 0.4]), 0.5],
        "sun angle": approx(0.1),
    }


def test_unselected_lights_are_untouched_and_skipped_lights_are_reported():
    energies, reports = run_in_blender_with_reports("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        lights = [add_light("Desk"), add_light("Hall"), add_light("Sun", "SUN"), add_light("Moon", "SUN")]
        for obj in lights:
            obj.data.energy = 7
        for obj in (lights[0], lights[2], lights[3]):
            obj.select_set(True)
        bpy.ops.lighthouse.apply_preset(preset='BULB_60W')
        report({obj.name: obj.data.energy for obj in lights})
    """)

    assert energies == {"Desk": 60, "Hall": 7, "Sun": 7, "Moon": 7}
    assert reports == ["Applied 60W Bulb to 1 light (2 skipped: incompatible type)"]


def test_candle_sets_an_area_light_size_to_the_preset_diameter():
    size = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        area = add_light("Area", "AREA")
        area.data.size = 1.0
        area.select_set(True)
        bpy.ops.lighthouse.apply_preset(preset='CANDLE')
        report(area.data.size)
    """)

    assert size == approx(0.02)


def test_daylight_sets_a_selected_sun_and_its_angle():
    sun = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        sun = add_light("Sun", "SUN")
        sun.data.angle = 0.1
        sun.select_set(True)
        bpy.ops.lighthouse.apply_preset(preset='DAYLIGHT')
        report([sun.data.energy, list(sun.data.color), sun.data.angle])
    """)

    assert sun == [4, approx([1.0, 0.96, 0.9]), approx(0.0093)]
