import math

from blender_runner import run_in_blender

FACTORS = ["specular_factor", "diffuse_factor", "volume_factor", "use_shadow"]
# Exposure (4.4+) and temperature (5.0+) come first, on Blender versions that have them.
NEWER = ["exposure", "use_temperature", "temperature"]


def test_eevee_details_show_only_properties_each_light_type_uses():
    details = run_in_blender("""
        from lighthouse.lights import detail_properties
        empty_scene()
        report({
            t: detail_properties(add_light(t, t).data, "BLENDER_EEVEE")
            for t in ("POINT", "SUN", "SPOT", "AREA")
        })
    """)

    assert details == {
        "POINT": NEWER + ["shadow_soft_size"] + FACTORS,
        "SUN": NEWER + ["angle"] + FACTORS,
        "SPOT": NEWER + ["shadow_soft_size"] + FACTORS,
        "AREA": NEWER + FACTORS,
    }


def test_switching_to_cycles_adds_cycles_options_and_switching_back_removes_them():
    details = run_in_blender("""
        from lighthouse.lights import detail_properties
        scene = empty_scene()
        lights = {t: add_light(t, t).data for t in ("POINT", "SUN", "SPOT", "AREA")}
        def current():
            return {t: detail_properties(light, scene.render.engine) for t, light in lights.items()}
        scene.render.engine = "CYCLES"
        cycles = current()
        scene.render.engine = "BLENDER_EEVEE"
        report({"cycles": cycles, "eevee": current()})
    """)

    cycles = ["cycles.max_bounces", "cycles.use_multiple_importance_sampling", "cycles.is_caustics_light"]
    assert details["cycles"] == {
        "POINT": NEWER + ["shadow_soft_size"] + FACTORS + cycles,
        "SUN": NEWER + ["angle"] + FACTORS + cycles,
        "SPOT": NEWER + ["shadow_soft_size"] + FACTORS + cycles,
        "AREA": NEWER + FACTORS + cycles + ["cycles.is_portal"],
    }
    assert details["eevee"] == {
        "POINT": NEWER + ["shadow_soft_size"] + FACTORS,
        "SUN": NEWER + ["angle"] + FACTORS,
        "SPOT": NEWER + ["shadow_soft_size"] + FACTORS,
        "AREA": NEWER + FACTORS,
    }


def test_editing_a_detail_changes_the_light_the_properties_editor_shows():
    values = run_in_blender("""
        from lighthouse.lights import detail_target
        empty_scene()
        sun = add_light("Sun", "SUN").data
        area = add_light("Area", "AREA").data
        for light, path, value in ((sun, "angle", 0.25), (sun, "use_shadow", False),
                                   (area, "cycles.max_bounces", 7), (area, "cycles.is_portal", True)):
            owner, prop = detail_target(light, path)
            setattr(owner, prop, value)
        report({
            "angle": bpy.data.lights["Sun"].angle,
            "use_shadow": bpy.data.lights["Sun"].use_shadow,
            "max_bounces": bpy.data.lights["Area"].cycles.max_bounces,
            "is_portal": bpy.data.lights["Area"].cycles.is_portal,
        })
    """)

    assert math.isclose(values.pop("angle"), 0.25, rel_tol=1e-6)
    assert values == {"use_shadow": False, "max_bounces": 7, "is_portal": True}


ACCORDION = """
        import lighthouse
        from lighthouse.lights import details_open
        lighthouse.register()
        empty_scene()
        lights = {name: add_light(name) for name in ("A", "B", "C")}

        def open_details():
            settings = bpy.context.window_manager.lighthouse
            return sorted(name for name, obj in lights.items() if details_open(settings, obj))
"""


def test_opening_details_closes_the_others_unless_keep_others_is_set():
    steps = run_in_blender(ACCORDION + """
        steps = []
        bpy.ops.lighthouse.toggle_details(name="A")
        bpy.ops.lighthouse.toggle_details(name="B")
        steps.append(open_details())
        bpy.ops.lighthouse.toggle_details(name="C", keep_others=True)
        steps.append(open_details())
        bpy.ops.lighthouse.toggle_details(name="B")
        steps.append(open_details())
        report(steps)
    """)

    assert steps == [["B"], ["B", "C"], ["C"]]


def test_renaming_a_light_keeps_its_details_open():
    still_open = run_in_blender(ACCORDION + """
        bpy.ops.lighthouse.toggle_details(name="A")
        lights["A"].name = "Key Light"
        report(open_details())
    """)

    assert still_open == ["A"]


def test_toggling_details_forgets_deleted_lights():
    entries = run_in_blender(ACCORDION + """
        bpy.ops.lighthouse.toggle_details(name="A")
        bpy.ops.lighthouse.toggle_details(name="B", keep_others=True)
        bpy.data.objects.remove(lights.pop("A"))
        bpy.ops.lighthouse.toggle_details(name="C", keep_others=True)
        report(len(bpy.context.window_manager.lighthouse.expanded))
    """)

    assert entries == 2


def test_open_details_are_panel_state_outside_undo_and_the_object():
    surface = run_in_blender("""
        import lighthouse
        lighthouse.register()
        report({
            "undo": "UNDO" in lighthouse.LIGHTHOUSE_OT_toggle_details.bl_options,
            "on_window_manager": "expanded" in bpy.context.window_manager.lighthouse.bl_rna.properties,
            "on_object": hasattr(bpy.types.Object, "lighthouse_expanded"),
        })
    """)

    assert surface == {"undo": False, "on_window_manager": True, "on_object": False}


def test_details_leave_out_properties_an_older_blender_lacks():
    details = run_in_blender("""
        from lighthouse.lights import detail_properties
        empty_scene()

        class OlderLight:
            \"\"\"A real light whose RNA lacks the properties added after Blender 4.2.\"\"\"
            def __init__(self, light):
                self._light = light
                self.bl_rna = type("RNA", (), {"properties": {
                    key: prop for key, prop in light.bl_rna.properties.items()
                    if key not in ("exposure", "use_temperature", "temperature")
                }})()
            def __getattr__(self, name):
                return getattr(self._light, name)

        report(detail_properties(OlderLight(add_light("Key", "POINT").data), "CYCLES"))
    """)

    assert details == ["shadow_soft_size"] + FACTORS + [
        "cycles.max_bounces", "cycles.use_multiple_importance_sampling", "cycles.is_caustics_light",
    ]
