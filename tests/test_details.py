import math

from blender_runner import run_in_blender

FACTORS = ["specular_factor", "diffuse_factor", "volume_factor", "use_shadow"]


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
        "POINT": ["shadow_soft_size"] + FACTORS,
        "SUN": ["angle"] + FACTORS,
        "SPOT": ["shadow_soft_size"] + FACTORS,
        "AREA": FACTORS,
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
        "POINT": ["shadow_soft_size"] + FACTORS + cycles,
        "SUN": ["angle"] + FACTORS + cycles,
        "SPOT": ["shadow_soft_size"] + FACTORS + cycles,
        "AREA": FACTORS + cycles + ["cycles.is_portal"],
    }
    assert details["eevee"] == {
        "POINT": ["shadow_soft_size"] + FACTORS,
        "SUN": ["angle"] + FACTORS,
        "SPOT": ["shadow_soft_size"] + FACTORS,
        "AREA": FACTORS,
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
