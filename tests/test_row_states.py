from blender_runner import run_in_blender


def test_hidden_lights_stay_listed():
    names = run_in_blender("""
        from lighthouse.lights import listed_lights
        empty_scene()
        add_light("Viewport").hide_viewport = True
        add_light("Render").hide_render = True
        add_light("Eye").hide_set(True)
        add_light("Shown")
        report([o.name for o in listed_lights(bpy.context.view_layer)])
    """)

    assert names == ["Eye", "Render", "Shown", "Viewport"]


def test_hidden_lights_are_dimmed_and_shown_ones_are_not():
    dimmed = run_in_blender("""
        from lighthouse.lights import row_state
        empty_scene()
        add_light("Viewport").hide_viewport = True
        add_light("Render").hide_render = True
        add_light("Eye").hide_set(True)
        add_light("Shown")
        layer = bpy.context.view_layer
        report({o.name: row_state(o, layer).dimmed for o in layer.objects})
    """)

    assert dimmed == {"Viewport": True, "Render": True, "Eye": True, "Shown": False}


def test_light_linked_from_a_library_is_read_only_and_local_one_is_not(tmp_path):
    read_only = run_in_blender(f"""
        from lighthouse.lights import row_state
        empty_scene()
        library_light = add_light("Library")
        path = {str(tmp_path / "library.blend")!r}
        bpy.data.libraries.write(path, {{library_light}})
        bpy.data.objects.remove(library_light)
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.objects = ["Library"]
        bpy.context.scene.collection.objects.link(dst.objects[0])
        add_light("Local")
        layer = bpy.context.view_layer
        layer.update()
        report({{o.name: row_state(o, layer).read_only for o in layer.objects}})
    """)

    assert read_only == {"Library": True, "Local": False}


def test_light_with_system_override_is_read_only_and_editable_override_is_not(tmp_path):
    read_only = run_in_blender(f"""
        from lighthouse.lights import row_state
        empty_scene()
        lights = [bpy.data.lights.new(n, "POINT") for n in ("System", "Editable")]
        path = {str(tmp_path / "library.blend")!r}
        bpy.data.libraries.write(path, set(lights))
        for light in lights:
            bpy.data.lights.remove(light)
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.lights = ["System", "Editable"]
        for linked in dst.lights:
            override = linked.override_create()
            override.override_library.is_system_override = linked.name == "System"
            obj = bpy.data.objects.new(linked.name, override)
            bpy.context.scene.collection.objects.link(obj)
        layer = bpy.context.view_layer
        layer.update()
        report({{o.name: row_state(o, layer).read_only for o in layer.objects}})
    """)

    assert read_only == {"System": True, "Editable": False}


def test_editing_power_on_one_shared_row_changes_the_other():
    powers = run_in_blender("""
        from lighthouse.lights import listed_lights
        empty_scene()
        key = add_light("Key")
        twin = bpy.data.objects.new("Twin", key.data)
        bpy.context.scene.collection.objects.link(twin)
        layer = bpy.context.view_layer
        layer.update()
        rows = {o.name: o for o in listed_lights(layer)}
        rows["Key"].data.energy = 250.0
        report({name: obj.data.energy for name, obj in rows.items()})
    """)

    assert powers == {"Key": 250.0, "Twin": 250.0}
