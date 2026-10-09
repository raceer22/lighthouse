from blender_runner import run_in_blender

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


def test_built_ins_set_only_the_rgb_color_on_a_light_without_temperature():
    lights = run_in_blender(OLDER_LIGHT + """
        from lighthouse.presets import BUILTIN_PRESETS, apply_preset
        empty_scene()
        lights = {}
        for key, light_type in (('CANDLE', 'POINT'), ('BULB_60W', 'SPOT'), ('DAYLIGHT', 'SUN')):
            data = add_light(key, light_type).data
            stub = type("Object", (), {"data": OlderLight(data)})()
            apply_preset([stub], BUILTIN_PRESETS[key])
            lights[key] = [data.energy, [round(c, 3) for c in data.color], data.use_temperature]
        report(lights)
    """)

    assert lights == {
        "CANDLE": [1, [1.0, 0.58, 0.16], False],
        "BULB_60W": [60, [1.0, 0.71, 0.42], False],
        "DAYLIGHT": [4, [1.0, 0.96, 0.9], False],
    }
