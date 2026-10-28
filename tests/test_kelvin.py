from blender_runner import needs_blender, run_in_blender

# A real light whose RNA lacks the properties added after Blender 4.2, as on 4.2.
OLDER_LIGHT = """
        NEWER = ("exposure", "use_temperature", "temperature")

        class OlderLight:
            \"\"\"A real light whose RNA lacks the properties added after Blender 4.2.\"\"\"
            def __init__(self, light):
                object.__setattr__(self, "_light", light)
                object.__setattr__(self, "bl_rna", type("RNA", (), {"properties": {
                    key: prop for key, prop in light.bl_rna.properties.items() if key not in NEWER
                }})())
            def __getattr__(self, name):
                if name in NEWER:
                    raise AttributeError(name)
                return getattr(self._light, name)
            def __setattr__(self, name, value):
                if name in NEWER:
                    raise AttributeError(name)
                setattr(self._light, name, value)
"""


@needs_blender(5, 0, "Light.use_temperature")
def test_row_shows_kelvin_only_for_a_light_using_temperature():
    controls = run_in_blender(OLDER_LIGHT + """
        from lighthouse.lights import color_control
        empty_scene()
        kelvin = add_light("Kelvin").data
        kelvin.use_temperature = True
        rgb = add_light("RGB").data
        older = add_light("Older").data
        older.use_temperature = True
        report([color_control(kelvin), color_control(rgb), color_control(OlderLight(older))])
    """)

    assert controls == ["temperature", "color", "color"]


def test_default_presets_set_only_the_rgb_color_on_a_light_without_temperature():
    lights = run_in_blender(OLDER_LIGHT + """
        from lighthouse.presets import DEFAULT_PRESETS, apply_preset
        empty_scene()
        lights = {}
        for preset, light_type in zip(DEFAULT_PRESETS, ('AREA', 'POINT', 'SUN', 'SUN', 'SUN')):
            data = add_light(preset.label, light_type).data
            stub = type("Object", (), {"data": OlderLight(data)})()
            apply_preset([stub], preset)
            lights[preset.label] = [round(data.energy, 3), [round(c, 3) for c in data.color], getattr(data, "use_temperature", False)]
        report(lights)
    """)

    assert lights == {
        "Studio Softbox": [250, [1.0, 0.98, 0.95], False],
        "Warm Interior Bulb": [40, [1.0, 0.73, 0.45], False],
        "Midday Sun": [4.5, [1.0, 0.97, 0.92], False],
        "Golden Hour Sun": [2, [1.0, 0.65, 0.35], False],
        "Moonlight": [0.05, [0.82, 0.9, 1.0], False],
    }
