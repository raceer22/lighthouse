from blender_runner import run_in_blender

ENERGIES = """
        def energies():
            return {o.name: o.data.energy for o in bpy.context.view_layer.objects if o.type == 'LIGHT'}
"""

SCENE = """
        import lighthouse
        lighthouse.register()
        empty_scene()
        add_light("A").data.energy = 100
        add_light("B").data.energy = 200
        add_light("C").data.energy = 400
"""


def test_scaling_all_lights_by_half_halves_every_power():
    energies = run_in_blender(ENERGIES + SCENE + """
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        report(energies())
    """)

    assert energies == {"A": 50, "B": 100, "C": 200}


def test_scaling_selected_lights_changes_only_the_selected_ones():
    energies = run_in_blender(ENERGIES + SCENE + """
        bpy.context.view_layer.objects["A"].select_set(True)
        bpy.context.view_layer.objects["C"].select_set(True)
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='SELECTED')
        report(energies())
    """)

    assert energies == {"A": 50, "B": 200, "C": 200}


def test_light_data_shared_by_two_objects_is_scaled_once():
    energy = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        a = add_light("A")
        a.data.energy = 100
        twin = bpy.data.objects.new("Twin", a.data)
        bpy.context.scene.collection.objects.link(twin)
        bpy.context.view_layer.update()
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        report(a.data.energy)
    """)

    assert energy == 50


def test_library_and_system_override_lights_are_left_unchanged(tmp_path):
    energies = run_in_blender(ENERGIES + f"""
        import lighthouse
        lighthouse.register()
        empty_scene()
        library_light = add_light("Library")
        system = bpy.data.lights.new("System", "POINT")
        for light in (library_light.data, system):
            light.energy = 100
        path = {str(tmp_path / "library.blend")!r}
        bpy.data.libraries.write(path, {{library_light, system}})
        bpy.data.objects.remove(library_light)
        bpy.data.lights.remove(system)
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.objects = ["Library"]
            dst.lights = ["System"]
        bpy.context.scene.collection.objects.link(dst.objects[0])
        override = dst.lights[0].override_create()
        override.override_library.is_system_override = True
        bpy.context.scene.collection.objects.link(bpy.data.objects.new("System", override))
        add_light("Local").data.energy = 100
        bpy.context.view_layer.update()
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        report(energies())
    """)

    assert energies == {"Library": 100, "System": 100, "Local": 50}


def test_list_filters_do_not_narrow_the_scope():
    energies = run_in_blender(ENERGIES + SCENE + """
        filters = bpy.context.window_manager.lighthouse
        filters.name_filter = "A"
        filters.type_filter = 'SUN'
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        report(energies())
    """)

    assert energies == {"A": 50, "B": 100, "C": 200}
