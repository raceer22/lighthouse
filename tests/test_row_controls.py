from blender_runner import run_in_blender


def test_clicking_a_name_selects_only_that_light_and_makes_it_active():
    state = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        key = add_light("Key")
        fill = add_light("Fill")
        cube = add_mesh("Cube")
        key.select_set(True)
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube

        bpy.ops.lighthouse.select_light(name="Fill")

        layer = bpy.context.view_layer
        report({
            "selected": sorted(o.name for o in layer.objects if o.select_get()),
            "active": layer.objects.active.name,
        })
    """)

    assert state == {"selected": ["Fill"], "active": "Fill"}


def test_sun_power_is_in_watts_per_square_metre_and_others_in_watts():
    units = run_in_blender("""
        from lighthouse.lights import power_unit
        empty_scene()
        report({
            t: power_unit(add_light(t, t).data)
            for t in ("POINT", "SUN", "SPOT", "AREA")
        })
    """)

    assert units == {"POINT": "W", "SUN": "W/m²", "SPOT": "W", "AREA": "W"}
